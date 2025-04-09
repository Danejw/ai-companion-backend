# app/routes/transcribe.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.openai.transcribe import transcribe_audio_whisper
import tempfile

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        audio_data = await audio.read()

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name

        # Re-open the file for reading
        with open(tmp_file_path, "rb") as f:
            transcript_text = transcribe_audio_whisper(f)

        return {"transcript": transcript_text}

    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to transcribe audio.")
