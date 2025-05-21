import os
from agents import Agent, ItemHelpers, Runner, function_tool
from app.auth import verify_token_websocket
from openai import AsyncOpenAI
import base64
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.supabase.profiles import ProfileRepository
from app.utils.moderation import ModerationService
from app.websockets.handlers.text_handlers import handle_audio, handle_feedback, handle_gps, handle_image, handle_improv, handle_local_lingo, handle_orchestration, handle_personality, handle_text, handle_time
from app.websockets.orchestrate_contextual import build_user_profile
from app.websockets.schemas.messages import ImprovMessage, Message, AudioMessage, FeedbackMessage, GPSMessage, ImageMessage, LocalLingoMessage, PersonalityMessage, TextMessage, TimeMessage, OrchestrateMessage
from pydantic import TypeAdapter, ValidationError

router = APIRouter()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
message_adapter = TypeAdapter(Message)


@router.websocket("/main")
async def websocket_main(websocket: WebSocket, user_id: str = Depends(verify_token_websocket)):
    print("WebSocket main connecting")
    
    await websocket.accept()

    print("WebSocket connected")

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

                case PersonalityMessage():
                    await handle_personality(websocket, message, user_id)
                
                case LocalLingoMessage():
                    await handle_local_lingo(websocket, message, user_id)
                    
                case FeedbackMessage():
                    await handle_feedback(websocket, message, user_id)
                
                case OrchestrateMessage():
                    await handle_orchestration(websocket, message, user_id)

                case ImprovMessage():
                    await handle_improv(websocket, user_id, message)
                    
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")


