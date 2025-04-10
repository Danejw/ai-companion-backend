import base64
import logging
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import verify_token
from app.function.orchestrate import chat_orchestration, voice_orchestration
from app.openai.voice import Voices


router = APIRouter()


class UserInput(BaseModel):
    message: str
    

@router.post("/voice-orchestration")
async def voice_orchestrate(voice: Voices = Voices.ALLOY, audio: UploadFile = File(...), summarize: int = 10, extract: bool = True, user=Depends(verify_token)):
    user_id = user["id"]
    try:       
        stream, final_output = await voice_orchestration(user_id, voice, audio, summarize, extract)
        
        sanitized_output = base64.b64encode(final_output.encode('utf-8')).decode('ascii')        
        headers = {
            "X-Transcript": sanitized_output,
        }
        
        # Define streaming function
        async def stream_content():
            try:
                async for chunk in stream:
                    yield chunk
            except Exception as e:
                logging.error(f"Error in streaming: {str(e)}", exc_info=True)
                raise

        return StreamingResponse(
            stream_content(),
            media_type="audio/mp3",  
            headers=headers
        )
    except Exception as e:
        logging.error(f"Endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/chat-orchestration")
async def chat_orchestrate(user_input: UserInput, summarize: int = 10, extract: bool = True, user=Depends(verify_token)):
    user_id = user["id"] 
    try:
        stream = await chat_orchestration(user_id, user_input.message, summarize, extract)
        return StreamingResponse(stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))











