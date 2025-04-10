import asyncio
import logging
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
    tmp_file_name = None
    
    try: 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()

            with open(tmp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(model=model, file=audio_file)  
    finally:
        if tmp_file_name and os.path.exists(tmp_file_name):
            os.unlink(tmp_file_name)
   
    return transcript.text


async def text_to_speech(text : str, instructions: str = "", voice: Voices = Voices.ALLOY):
    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        instructions=instructions,
        response_format="mp3",
    ) as response:
        try:
            async for chunk in response.iter_bytes(chunk_size=1024):
                yield chunk
                await asyncio.sleep(0)  # Yield control to the event loop
        except Exception as e:
            logging.error(f"Error in audio stream: {str(e)}", exc_info=True)
            raise