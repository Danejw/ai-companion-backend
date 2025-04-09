from io import BytesIO
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from app.openai.transcribe import transcribe_audio_whisper
from app.openai.voice import Voices, voice_assistant_client, english_agent
from fastapi import APIRouter
import tempfile


router = APIRouter()

@router.post("/voice-assistant")
async def voice_assistant(voice: Voices = Voices.ALLOY, audio: UploadFile = File(...)):
    response_audio : BytesIO = await voice_assistant_client(english_agent, voice, audio)

    # 1. Create a temp mp3 file for transcription
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(response_audio.getbuffer())
        tmp_file.flush()

        # 2. Transcribe using Whisper with the file path
        with open(tmp_file.name, "rb") as audio_file:
            transcript = transcribe_audio_whisper(audio_file)
            
        print("Transcript: ", transcript)

    # 3. Rewind BytesIO for streaming
    response_audio.seek(0)
    
        # Stream the audio and send the transcript in a header
    headers = {
        "X-Transcript": transcript  # Optional: you can pass it back this way
    }

    # Return the audio as a streaming response
    return StreamingResponse(
        content=response_audio,
        media_type="audio/mp3",
        headers=headers
    )