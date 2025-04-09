from io import BytesIO
from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from app.auth import verify_token
from app.openai.transcribe import speech_to_text, text_to_speech
from app.openai.voice import Voices, voice_assistant_client, english_agent
from fastapi import APIRouter
import tempfile


router = APIRouter()

@router.post("/voice-assistant")
async def voice_assistant(voice: Voices = Voices.ALLOY, audio: UploadFile = File(...), user_id: str = Depends(verify_token)):
    try:
        response_audio : BytesIO = await voice_assistant_client(english_agent, voice, audio)

        # 1. Create a temp mp3 file for transcription
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(response_audio.getbuffer())
            tmp_file.flush()

            # 2. Transcribe using Whisper with the file path
            with open(tmp_file.name, "rb") as audio_file:
                transcript = speech_to_text(audio_file)
                
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
  
@router.post("/speech-to-text")
async def stt(audio: UploadFile = File(...)):#, user_id: str = Depends(verify_token)):
    try:
        transcript = await speech_to_text(audio)
        return transcript
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
    
@router.post("/text-to-speech")
async def tts(text: str, voice: Voices = Voices.ALLOY):#, user_id: str = Depends(verify_token)):
    try:
        return await text_to_speech(text, voice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

