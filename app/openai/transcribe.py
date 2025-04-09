from openai import OpenAI
import os


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # or hardcode the key for testing

def transcribe_audio_whisper(file, model: str = "whisper-1") -> str:
    transcript = client.audio.transcriptions.create(
        model=model,
        file=("response.mp3", file)
    )
    return transcript.text