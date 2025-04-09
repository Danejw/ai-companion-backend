import asyncio
from io import BytesIO
import tempfile
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from openai import OpenAI
import os
from openai import AsyncOpenAI
from app.openai.voice import Voices


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # or hardcode the key for testing
openai = AsyncOpenAI()


async def speech_to_text(file : UploadFile, model: str = "whisper-1") -> str:
    audio_bytes = await file.read()
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file.flush()

        with open(tmp_file.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model=model, file=audio_file)   
   
    return transcript.text


def speech_to_text_from_bytes(file: BytesIO, model: str = "whisper-1") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(file.getbuffer())
        tmp_file.flush()

    with open(tmp_file.name, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(model=model, file=audio_file)
    return transcript.text


async def text_to_speech(text : str, instructions: str = "", voice: Voices = Voices.ALLOY):
    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        instructions=instructions,
        response_format="pcm",
    ) as response:         
        # Stream the audio content
        async def audio_stream():
            for chunk in response.iter_bytes(chunk_size=1024):
                yield chunk
                await asyncio.sleep(0)  # Yield control to event loop

        return StreamingResponse(audio_stream(), media_type="audio/mp3")