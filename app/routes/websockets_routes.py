import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.auth import verify_token_websocket
from openai import AsyncOpenAI
import asyncio
import base64

from app.function.orchestrate import chat_orchestration


router = APIRouter()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))



@router.websocket("/voice-orchestration")
async def websocket_voice_endpoint(websocket: WebSocket, user_id: str = Depends(verify_token_websocket)):
    print( "user_id: ", user_id)

    
    await websocket.accept()
    
    
    print( "user_id: ", user_id)
    print(os.getenv("SUPABASE_JWT_SECRET"))

    print("WebSocket connected")
    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "audio":
                audio_base64 = data["audio"]
                audio_bytes = base64.b64decode(audio_base64)

                # Transcribe audio using Whisper
                transcript_response = await openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.webm", audio_bytes, "audio/webm"),
                )

                user_transcript = transcript_response.text

                # Emit user's transcript back to frontend
                await websocket.send_json({"type": "user_transcript", "text": user_transcript})

                # Run chat orchestration logic (your existing implementation)
                ai_response = await chat_orchestration(user_transcript, user_id)

                # Emit AI transcript event
                await websocket.send_json({"type": "ai_transcript", "text": ai_response})

                # Generate AI audio (TTS)
                ai_audio_stream = await openai_client.audio.speech.create(
                    model="tts-1",
                    voice="onyx",
                    input=ai_response,
                )

                audio_data = await ai_audio_stream.aread()

                # Stream audio data back to frontend as base64 chunks
                encoded_audio = base64.b64encode(audio_data).decode()
                await websocket.send_json({"type": "audio_response", "audio": encoded_audio})

    except WebSocketDisconnect:
        print("WebSocket disconnected")
