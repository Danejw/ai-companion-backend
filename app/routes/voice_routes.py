from io import BytesIO
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from app.openai.voice import Voices, voice_assistant_client, english_agent
from fastapi import APIRouter

router = APIRouter()

@router.post("/voice-assistant")
async def voice_assistant(voice: Voices = Voices.ALLOY, audio: UploadFile = File(...)):
    response_audio = await voice_assistant_client(english_agent, voice, audio)

    return StreamingResponse(
        content=response_audio,
        media_type="audio/mp3"  # You could change this based on your playback needs
    )