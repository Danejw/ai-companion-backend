import os
from agents import Agent, ItemHelpers, Runner, function_tool
from agents.voice import TTSModelSettings
from pydantic import ValidationError
from app.auth import verify_token_websocket
from openai import AsyncOpenAI
import base64
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.websockets.context.store import update_context
from app.function.orchestrate import chat_orchestration
from app.websockets.handlers.text_handlers import handle_audio, handle_gps, handle_orchestration, handle_text, handle_time
from app.websockets.schemas.messages import AudioMessage, GPSMessage, ImageMessage, Message, TextMessage, TimeMessage, UIActionMessage, OrchestrateMessage
from pydantic import TypeAdapter

router = APIRouter()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
message_adapter = TypeAdapter(Message)


@function_tool
def get_weather(city: str):
    response = "It always sunny in " + city
    return response


instructions = f"""

You are a tutor for the Hawaiian language.

Response as if you were a native resident of Hawaii with a slight pidgin accent.

Teach the user about to speak in Hawaiian.

Pronounce the words clearly and correctly in the native Hawaiian dialect and toungue.

"""

health_assistant= "Voice Affect: Calm, composed, and reassuring; project quiet authority and confidence."
"Tone: Sincere, empathetic, and gently authoritative—express genuine apology while conveying competence."
"Pacing: Steady and moderate; unhurried enough to communicate care, yet efficient enough to demonstrate professionalism."


custom_tts_settings = TTSModelSettings(
    voice="ash",
    instructions=health_assistant,
)


agent = Agent(
        name="Hawaii Tutor Agent",
        handoff_description="An agent teaches the user about Hawaiian culture, history, and language.",
        instructions=instructions,
        model="gpt-4o-mini",         
    )


@router.websocket("/main")
async def websocket_main(websocket: WebSocket, user_id: str = Depends(verify_token_websocket)):
    await websocket.accept()
    print(f"WebSocket connected for user {user_id}")

    try:
        while True:
            raw = await websocket.receive_json()

            try:
                message = message_adapter.validate_python(raw)
            except ValidationError as ve:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format",
                    "details": ve.errors()
                })
                continue
            match message:          
                case TextMessage():
                    await handle_text(agent, websocket, message, user_id)
                
                case AudioMessage():
                    await handle_audio(agent, websocket, message, user_id)

                case ImageMessage():
                    update_context(user_id, "image", {"format": message.format})
                    await websocket.send_json({"type": "image_action", "status": "ok"})

                case GPSMessage():
                    await handle_gps(websocket, message, user_id)
                    
                case TimeMessage():
                    await handle_time(websocket, message, user_id)

                case UIActionMessage():
                    print(f"Received UI action: {message.action} on {message.target}")
                    await websocket.send_json({"type": "ui_action", "status": "ok"})
                
                case OrchestrateMessage():
                    await handle_orchestration(agent, websocket, message, user_id)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")


@router.websocket("/voice-orchestration")
async def websocket_voice(websocket: WebSocket, user_id: str = Depends(verify_token_websocket)):
    await websocket.accept()

    print("WebSocket connected")
    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "audio":
                audio_base64 = data["audio"]
                audio_bytes = base64.b64decode(audio_base64)

                # Transcribe audio using Whisper
                transcript_response = await openai_client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe", #"whisper-1", gpt-4o-transcribe
                    file=("audio.webm", audio_bytes, "audio/webm"),
                )

                user_transcript = transcript_response.text
                
                print("user_transcript: ", user_transcript)

                # Emit user's transcript back to frontend
                await websocket.send_json({"type": "user_transcript", "text": user_transcript})

                # # Run chat orchestration logic (your existing implementation)
                #ai_response = await chat_orchestration(user_id, user_transcript)
                
                # final_output = ""
                # async for chunk_str in ai_response():
                #     # chunk_str is already a JSON string (e.g. from `json.dumps(...) + "\n"`)
                #     # so we can send it as text directly:
                #     if "delta" in chunk_str:
                #         final_output += chunk_str["delta"]
                #     elif "tool_call" in chunk_str:
                #         await websocket.send_json({"type": "tool_call_item", "text": chunk_str["tool_call"]})
                #     elif "tool_call_output" in chunk_str:
                #         await websocket.send_json({"type": "tool_call_output_item", "text": chunk_str["tool_call_output"]})
                #     elif "agent_updated" in chunk_str:
                #         await websocket.send_json({"type": "agent_updated", "text": chunk_str["agent_updated"]})
                    
                #     final_output += chunk_str
                # await websocket.send_text(chunk_str)
                
                ai_response = Runner.run_streamed(agent, user_transcript)
                
                async for event in ai_response.stream_events():
                    # There are different event types: raw_response_event, agent_updated_stream_event, etc.
                    
                    if event.type == "raw_response_event":
                        # Usually just partial model deltas—skip or log if you want
                        continue

                    elif event.type == "agent_updated_stream_event":
                        # The agent itself changed
                        updated_name = event.new_agent.name
                        # Send an update to the frontend
                        await websocket.send_json({
                            "event_type": event.type,
                            "message": f"Agent updated: {updated_name}"
                        })

                    elif event.type == "run_item_stream_event":
                        # Could be "tool_call_item", "tool_call_output_item", or "message_output_item"

                        if event.item.type == "tool_call_item":
                            # The agent called a tool
                            await websocket.send_json({"type": "tool_call_item", "text": event.item.raw_item.name})

                        elif event.item.type == "tool_call_output_item":
                            # The tool responded
                            await websocket.send_json({"type": "tool_call_output_item", "text": event.item.output})

                        elif event.item.type == "message_output_item":
                            # The agent produced a message
                            message_text = ItemHelpers.text_message_output(event.item)
                            await websocket.send_json({"type": "message_output_item", "text": event.item.raw_item.to_json()})
                        else:
                            # For other item types, do nothing or handle them as needed
                            pass
                
                print("ai_response: ", ai_response)
                
                ai_final_output = ai_response.final_output
                
                print("ai_response: ", ai_final_output) 

                # Emit AI transcript event
                await websocket.send_json({"type": "ai_transcript", "text": ai_final_output})

                # # Generate AI audio (TTS)
                ai_audio_stream = await openai_client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="ash",
                    input=ai_final_output,
                )

                audio_data = await ai_audio_stream.aread()

                # # Stream audio data back to frontend as base64 chunks
                encoded_audio = base64.b64encode(audio_data).decode()
                await websocket.send_json({"type": "audio_response", "audio": encoded_audio})

    except WebSocketDisconnect:
        print("WebSocket disconnected")


