import os
from agents import Agent, ItemHelpers, Runner, function_tool
from agents.voice import TTSModelSettings
from pydantic import ValidationError
from app.auth import verify_token_websocket
from openai import AsyncOpenAI
import base64
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.supabase.profiles import ProfileRepository
from app.utils.moderation import ModerationService
from app.websockets.handlers.text_handlers import handle_audio, handle_feedback, handle_gps, handle_image, handle_orchestration, handle_raw_mode, handle_text, handle_time
from app.websockets.orchestrate_contextual import build_user_profile
from app.websockets.schemas.messages import AudioMessage, FeedbackMessage, GPSMessage, ImageMessage, Message, RawMessage, TextMessage, TimeMessage, OrchestrateMessage
from pydantic import TypeAdapter

router = APIRouter()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
message_adapter = TypeAdapter(Message)


@router.websocket("/main")
async def websocket_main(websocket: WebSocket, user_id: str = Depends(verify_token_websocket)):
    await websocket.accept()

    # Check credits send error back if 0
    profile_service = ProfileRepository()
    moderation_service = ModerationService()

    credits = profile_service.get_user_credit(user_id)
    if credits is None or credits < 1:
        await websocket.send_json({"type": "error", "text": "NO_CREDITS"})
        return
    
    # TODO: Moderation check per message input
    
    # build user profile
    await build_user_profile(user_id, websocket)


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
                    await handle_text(websocket, message, user_id)
                
                case AudioMessage():
                    await handle_audio(websocket, message, user_id)

                case ImageMessage():
                    await handle_image(websocket, message, user_id)

                case GPSMessage():
                    await handle_gps(websocket, message, user_id)
                    
                case TimeMessage():
                    await handle_time(websocket, message, user_id)

                case RawMessage():
                    await handle_raw_mode(websocket, message, user_id)
                    
                case FeedbackMessage():
                    await handle_feedback(websocket, message, user_id)
                
                case OrchestrateMessage():
                    await handle_orchestration(websocket, message, user_id)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")



# Depricated
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
                
                agent = Agent(
                    name="Basic Agent",
                    instructions=instructions,
                    model="gpt-4o-mini",
                    tools=[get_weather]
                )
                
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


