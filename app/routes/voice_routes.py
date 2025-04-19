from io import BytesIO
from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.auth import verify_token
from app.openai.transcribe import speech_to_text, speech_to_text_from_bytes, text_to_speech
from app.openai.voice import Voices, voice_assistant_client, english_agent
from fastapi import APIRouter

from app.websockets.handlers import text_handlers


router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: Voices = Voices.ALLOY


@router.post("/voice-assistant")
async def voice_assistant(voice: Voices = Voices.ALLOY, audio: UploadFile = File(...), user_id: str = Depends(verify_token)):
    try:
        response_audio : BytesIO = await voice_assistant_client(english_agent, voice, audio)

        transcript = speech_to_text_from_bytes(response_audio)
        response_audio.seek(0)
        
        headers = {"X-Transcript": transcript}

        return StreamingResponse(
            content=response_audio,
            media_type="audio/mp3",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
  
@router.post("/speech-to-text")
async def stt(audio: UploadFile = File(...), user_id: str = Depends(verify_token)):
    try:
        transcript = await speech_to_text(audio)
        return transcript
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
    
@router.post("/text-to-speech")
async def tts(request: TTSRequest, user_id: str = Depends(verify_token)):
    try:
        audio_stream = text_to_speech(text=request.text, voice=request.voice)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")
    except Exception as e:
        print("TTS error: ", e)
        raise HTTPException(status_code=500, detail=str(e))

