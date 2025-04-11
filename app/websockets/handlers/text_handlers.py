# app/websocket_handlers/text_handler.py
import base64
import os
from agents import Agent, Runner
from fastapi import WebSocket
from openai import AsyncOpenAI
from app.websockets.context.store import update_context
from app.websockets.orchestrate_contextual import run_contextual_orchestration
from app.websockets.schemas.messages import OrchestrateMessage, UIActionMessage, TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def handle_text(agent: Agent, websocket: WebSocket, message: TextMessage, user_id: str):
    update_context(user_id, "last_text", message.text)
    response = await Runner.run(agent, message.text)
    await websocket.send_json({"type": "ai_response", "text": response.final_output})
    await websocket.send_json({"type": "text_ack", "status": "ok"})

async def handle_audio(agent: Agent, websocket: WebSocket, message: AudioMessage, user_id: str):
    update_context(user_id, "audio_received", True)

    # Transcribe audio using Whisper
    audio_bytes = base64.b64decode(message.audio)
    user_transcript = await stt(audio_bytes, websocket)

    await websocket.send_json({"type": "user_transcript", "text": user_transcript})
    
    response = await Runner.run(agent, user_transcript)
    
    await websocket.send_json({"type": "ai_transcript", "text": response.final_output})

    voice = message.voice if message.voice else "alloy"
    await tts(response.final_output, voice, websocket)

# TODO: handle everything below this
async def handle_image(websocket: WebSocket, message: ImageMessage, user_id: str):
    update_context(user_id, "image", {"format": message.format})
    await websocket.send_json({"type": "image_ack", "status": "ok"})

async def handle_location(websocket: WebSocket, message: GPSMessage, user_id: str):
    update_context(user_id, "location", {
        "latitude": message.latitude,
        "longitude": message.longitude,
        "accuracy": message.accuracy
    })
    await websocket.send_json({"type": "location_ack", "status": "ok"})

async def handle_time(websocket: WebSocket, message: TimeMessage, user_id: str):
    update_context(user_id, "time", {
        "timestamp": message.timestamp,
        "timezone": message.timezone
    })
    await websocket.send_json({"type": "time_ack", "status": "ok"})

async def handle_ui_action(websocket: WebSocket, message: UIActionMessage):
    # Just send it back for now
    await websocket.send_json({
        "type": "ui_ack",
        "action": message.action,
        "target": message.target,
        "status": "ok"
    })

async def handle_orchestration(websocket: WebSocket, message: OrchestrateMessage, user_id: str):
    await websocket.send_json({"type": "orchestrating"})

    result = await run_contextual_orchestration(user_input=message.user_input, user_id=user_id)

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            continue

        elif event.type == "agent_updated_stream_event":
            await websocket.send_json({
                "type": "agent_updated",
                "text": event.new_agent.name
            })

        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                await websocket.send_json({
                    "type": "tool_call_item",
                    "text": event.item.raw_item.name
                })

            elif event.item.type == "tool_call_output_item":
                await websocket.send_json({
                    "type": "tool_call_output_item",
                    "text": event.item.output
                })

            elif event.item.type == "message_output_item":
                await websocket.send_json({
                    "type": "ai_response",
                    "text": event.item.raw_item.content
                })
                
    final = result.final_output
    await websocket.send_json({"type": "ai_transcript", "text": final})



async def stt(audio_bytes: bytes, websocket: WebSocket) -> str:
    transcript_response = await openai_client.audio.transcriptions.create(
        model="whisper-1", #"whisper-1", gpt-4o-transcribe, gpt-4o-mini-transcribe
        file=("audio.webm", audio_bytes, "audio/webm"),
    )
    user_transcript = transcript_response.text
    return user_transcript

async def tts(text :str, voice :str, websocket: WebSocket) -> str:
    # # Generate AI audio (TTS)
    ai_audio_stream = await openai_client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
    )

    audio_data = await ai_audio_stream.aread()

    # # Stream audio data back to frontend as base64 chunks
    encoded_audio = base64.b64encode(audio_data).decode()
    await websocket.send_json({"type": "audio_response", "audio": encoded_audio})
    return encoded_audio