# app/websocket_handlers/text_handler.py
import base64
import os
from fastapi import WebSocket
from openai import AsyncOpenAI
from app.websockets.context.store import update_context
from app.websockets.schemas.messages import OrchestrateMessage, UIActionMessage, TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))





async def handle_text(websocket: WebSocket, message: TextMessage, user_id: str):
    update_context(user_id, "last_text", message.text)
    
    #print("message: ", message)
    
    print("Received text")
    
    # Do things with the text
    await websocket.send_json({"type": "text_ack", "status": "ok"})


# app/websocket_handlers/audio_handler.py
from fastapi import WebSocket
from app.websockets.context.store import update_context

async def handle_audio(websocket: WebSocket, message: AudioMessage, user_id: str):
    update_context(user_id, "audio_received", True)
    
    #print("message: ", message)

    # Transcribe audio using Whisper
    audio_bytes = base64.b64decode(message.audio)
    transcript_response = await openai_client.audio.transcriptions.create(
        model="whisper-1", #"whisper-1", gpt-4o-transcribe, gpt-4o-mini-transcribe
        file=("audio.webm", audio_bytes, "audio/webm"),
    )
    user_transcript = transcript_response.text

    print("user_transcript: ", user_transcript)

    await websocket.send_json({"type": "user_transcript", "text": user_transcript})

    # Do other things with the transcript
    

# app/websocket_handlers/image_handler.py
from fastapi import WebSocket
from app.websockets.context.store import update_context

async def handle_image(websocket: WebSocket, message: ImageMessage, user_id: str):
    update_context(user_id, "image", {"format": message.format})
    await websocket.send_json({"type": "image_ack", "status": "ok"})


# app/websocket_handlers/gps_handler.py
from fastapi import WebSocket
from app.websockets.context.store import update_context

async def handle_location(websocket: WebSocket, message: GPSMessage, user_id: str):
    update_context(user_id, "location", {
        "latitude": message.latitude,
        "longitude": message.longitude,
        "accuracy": message.accuracy
    })
    await websocket.send_json({"type": "location_ack", "status": "ok"})


# app/websocket_handlers/time_handler.py
from fastapi import WebSocket
from app.websockets.context.store import update_context

async def handle_time(websocket: WebSocket, message: TimeMessage, user_id: str):
    update_context(user_id, "time", {
        "timestamp": message.timestamp,
        "timezone": message.timezone
    })
    await websocket.send_json({"type": "time_ack", "status": "ok"})


# app/websocket_handlers/ui_action_handler.py
from fastapi import WebSocket

async def handle_ui_action(websocket: WebSocket, message: UIActionMessage):
    # Just send it back for now
    await websocket.send_json({
        "type": "ui_ack",
        "action": message.action,
        "target": message.target,
        "status": "ok"
    })


# app/websocket_handlers/orchestrate_handler.py
from fastapi import WebSocket
from app.websockets.orchestrate_contextual import run_contextual_orchestration

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
