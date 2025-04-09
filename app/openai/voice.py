import asyncio
from enum import Enum
from io import BytesIO
import io
import random
import tempfile
from pydub import AudioSegment
from fastapi import File, UploadFile
import numpy as np
import sounddevice as sd
from agents.voice import AudioInput, SingleAgentVoiceWorkflow, VoicePipeline, TTSModelSettings, VoicePipelineConfig
from agents import Agent, FileSearchTool, Runner, WebSearchTool, function_tool, trace
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from app.openai.transcribe import transcribe_audio_whisper


sd.default.samplerate = 24000  # Set to your desired sampling rate
samplerate = 24000 #44100

model = "gpt-4o-mini-tts"

class Voices(str, Enum):
    ALLOY = "alloy"     # Female
    ASH = "ash"         # Male Deep Voice
    CORAL = "coral"     # Female High Pitch
    ECHO = "echo"       # Female
    FABLE = "fable"     # Female English Accent
    ONYX = "onyx"       # Male
    NOVA = "nova"       # Female
    SAGE = "sage"       # Female
    SHIMMER = "shimmer" # Female

voice = Voices.ALLOY


# Common system prompt for voice output best practices:
system_prompt = """


"""

# Voice prompts
empathic_assistant="""
        Speak in a consistent tone and style. Speak clearly and empathetically.
        Tempo: Speak an a consistent normal pace, include brief pauses and after before questions
        Emotion: Warm and supportive, conveying empathy and care, ensuring the listener feels guided and safe throughout the journey.
    """

health_assistant= "Voice Affect: Calm, composed, and reassuring; project quiet authority and confidence."
"Tone: Sincere, empathetic, and gently authoritative—express genuine apology while conveying competence."
"Pacing: Steady and moderate; unhurried enough to communicate care, yet efficient enough to demonstrate professionalism."

coach_assistant="Voice: High-energy, upbeat, and encouraging, projecting enthusiasm and motivation."
"Punctuation: Short, punchy sentences with strategic pauses to maintain excitement and clarity."
"Delivery: Fast-paced and dynamic, with rising intonation to build momentum and keep engagement high."

themed_character_assistant="Affect: Deep, commanding, and slightly dramatic, with an archaic and reverent quality that reflects the grandeur of Olde English storytelling."
"Tone: Noble, heroic, and formal, capturing the essence of medieval knights and epic quests, while reflecting the antiquated charm of Olde English."    
"Emotion: Excitement, anticipation, and a sense of mystery, combined with the seriousness of fate and duty."
"Pronunciation: Clear, deliberate, and with a slightly formal cadence."
"Pause: Pauses after important Olde English phrases such as \"Lo!\" or \"Hark!\" and between clauses like \"Choose thy path\" to add weight to the decision-making process and allow the listener to reflect on the seriousness of the quest."


# You are a friendly, local Hawaiian assistant who speaks in authentic Pidgin English (Hawai‘i Creole English). Your tone should be casual, warm, and full of local flavor — like you're chatting with an old friend at the beach.

# Speak with simplicity, emotional expression, and heart. You use Pidgin grammar and vocabulary naturally, blending English with Hawaiian and other local influences. You’re not formal or robotic — you “talk story.”

# Guidelines:
# - Use simplified grammar (e.g., “I went go” instead of “I went to”)
# - Include local terms like “pau,” “bumbai,” “da kine,” “brah,” “choke,” and “ono”
# - Keep it relaxed, rhythmic, and emotionally resonant
# - Drop into island-style sentence flow (don’t force standard English)
# - Be warm, supportive, and personable
# - You may use Hawaiian words when it feels natural, but you don’t overdo it

# Examples:
# - Standard: “Are you done eating?”
# - Pidgin: “You pau eat already?”

# - Standard: “We’ll do it later.”
# - Pidgin: “We go bumbai.”

# Keep it real, keep it local. Speak like home.

custom_tts_settings = TTSModelSettings(
    instructions=health_assistant,
    voice=voice
)



@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    print(f"[debug] get_weather called with city: {city}")
    choices = ["sunny", "cloudy", "rainy", "snowy"]
    return f"The weather in {city} is {random.choice(choices)}."


def get_default_input_device_info():
    default_input_device_info = sd.query_devices(kind='input')
    print(default_input_device_info)
    return default_input_device_info
    
    

spanish_agent = Agent(
    name="Spanish",
    handoff_description="A spanish speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in Spanish.",
    ),
    model=model,
)

pidgin_agent = Agent(
    name="Pidgin",
    handoff_description="A pidgin speaking agent.",
    instructions=system_prompt,
    model=model,
)

english_agent = Agent(
    name="English",
    handoff_description="A English speaking agent.",
    instructions=
        "You're speaking to a human, so be polite and concise. Speak in English.",
    model=model,
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. If the user speaks in Spanish, handoff to the spanish agent.",
    ),
    model=model, 
    handoffs=[spanish_agent],
    tools=[get_weather],
)





hawaiian_agent = Agent(
    name="Hawaiian",
    handoff_description="A Hawaiian speaking agent.",
    instructions=system_prompt + prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in Hawaiian.",
    ),
    model=model,
)


# --- Agent: Search Agent ---
search_voice_agent = Agent(
    name="SearchVoiceAgent",
    instructions=system_prompt + (
        "You immediately provide an input to the WebSearchTool to find up-to-date information on the user's query."
    ),
    model=model,
    tools=[WebSearchTool()],
)

# --- Agent: Knowledge Agent ---
knowledge_voice_agent = Agent(
    name="KnowledgeVoiceAgent",
    instructions=system_prompt + (
        "You answer user questions on our product portfolio with concise, helpful responses using the FileSearchTool."
    ),
    model=model,
    tools=[FileSearchTool(
            max_num_results=3,
            vector_store_ids=["VECTOR_STORE_ID"],
        ),],
)

# --- Agent: Account Agent ---
account_voice_agent = Agent(
    name="AccountVoiceAgent",
    instructions=system_prompt + (
        "You provide account information based on a user ID using the get_account_info tool."
    ),
    model=model,
)

# --- Agent: Triage Agent ---
triage_voice_agent = Agent(
    name="VoiceAssistant",
    instructions=prompt_with_handoff_instructions("""
You are the virtual assistant for Acme Shop. Welcome the user and ask how you can help.
Based on the user's intent, route to:
- AccountAgent for account-related queries
- KnowledgeAgent for product FAQs
- SearchAgent for anything requiring real-time web search
"""),
    handoffs=[account_voice_agent, knowledge_voice_agent, search_voice_agent],
    model=model,
)


async def voice_assistant():
    # samplerate = sd.query_devices(kind='input')['default_samplerate']

    while True:
        pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(triage_voice_agent))

        # Check for input to either provide voice or exit
        cmd = input("Press Enter to speak your query (or type 'esc' to exit): ")
        if cmd.lower() == "esc":
            print("Exiting...")
            break      
        print("Listening...")
        recorded_chunks = []

         # Start streaming from microphone until Enter is pressed
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', callback=lambda indata, frames, time, status: recorded_chunks.append(indata.copy())):
            input()

        # Concatenate chunks into single buffer
        recording = np.concatenate(recorded_chunks, axis=0)

        # Input the buffer and await the result
        audio_input = AudioInput(buffer=recording)

        with trace("ACME App Voice Assistant"):
            result = await pipeline.run(audio_input)

         # Transfer the streamed result into chunks of audio
        response_chunks = []
        async for event in result.stream():
            if event.type == "voice_stream_event_audio":
                print(f"Received audio event: {event.data}")
                response_chunks.append(event.data)
            elif event.type == "voice_stream_event_lifecycle":
                # lifecycle
                pass    
            elif event.type == "voice_stream_event_error":
                # error
                pass

        response_audio = np.concatenate(response_chunks, axis=0)

        # Play response
        print("Assistant is responding...")
        sd.play(response_audio, samplerate=samplerate)
        sd.wait()
        print("---")

async def voice_assistant_optimized():
    # samplerate = sd.query_devices(kind='input')['default_samplerate']
    voice_pipeline_config = VoicePipelineConfig(tts_settings=custom_tts_settings)

    while True:
        pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(pidgin_agent), config=voice_pipeline_config)

        # Check for input to either provide voice or exit
        cmd = input("Press Enter to speak your query (or type 'esc' to exit): ")
        if cmd.lower() == "esc":
            print("Exiting...")
            break       
        print("Listening...")
        recorded_chunks = []

         # Start streaming from microphone until Enter is pressed
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', callback=lambda indata, frames, time, status: recorded_chunks.append(indata.copy())):
            input()

        if recorded_chunks: 
            # Concatenate chunks into single buffer
            recording = np.concatenate(recorded_chunks, axis=0)

        # Input the buffer and await the result
        audio_input = AudioInput(buffer=recording)
        
    

        with trace("ACME App Optimized Voice Assistant"):
            result = await pipeline.run(audio_input)

         # Transfer the streamed result into chunks of audio
        response_chunks = []
        async for event in result.stream():
            if event.type == "voice_stream_event_audio":
                response_chunks.append(event.data)
                
        if response_chunks:
            response_audio = np.concatenate(response_chunks, axis=0)

        # Play response
        print("Assistant is responding...")
        if response_audio:  
            sd.play(response_audio, samplerate=samplerate)
            sd.wait()
        print("---")



async def voice_assistant_client(agent: Agent, voice: Voices = Voices.ALLOY, audio: UploadFile = File(...)) -> BytesIO:
    # 1. Set TTS voice and initialize pipeline config
    custom_tts_settings.voice = voice.value
    voice_pipeline_config = VoicePipelineConfig(tts_settings=custom_tts_settings)

    # 2. Read the uploaded audio file
    audio_bytes = await audio.read()
    
    # Determine the format based on MIME type
    if audio.content_type == "audio/webm":
        input_format = "webm"
    elif audio.content_type == "audio/mpeg" or audio.content_type == "audio/mp3":
        input_format = "mp3"
    elif audio.content_type == "audio/wav":
        input_format = "wav"
    else:
        raise ValueError(f"Unsupported audio format: {audio.content_type}")
    

    # 3. Convert the uploaded WebM/MP3 to raw PCM (int16) for OpenAI SDK
    segment = AudioSegment.from_file(BytesIO(audio_bytes), format=input_format)
    segment = segment.set_channels(1).set_frame_rate(24000).set_sample_width(2)
    buffer = np.array(segment.get_array_of_samples(), dtype=np.int16)

    # 4. Prepare pipeline input
    audio_input = AudioInput(buffer=buffer)
    pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent), config=voice_pipeline_config)
    
    
    
    
    # 5. Run the agent on the audio input
    with trace("Knolia Voice Assistant"):
        result = await pipeline.run(audio_input)

    # 6. Collect response audio from the agent (raw PCM chunks)
    response_chunks = []
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            response_chunks.append(event.data)

    if not response_chunks:
        raise ValueError("No audio returned from voice pipeline.")

    # 7. Combine raw audio and convert to MP3 using pydub
    response_audio = np.concatenate(response_chunks, axis=0)
    pcm_bytes = response_audio.tobytes()
    pcm_segment = AudioSegment(
        data=pcm_bytes,
        sample_width=2,
        frame_rate=24000,
        channels=1
    )

    mp3_io = BytesIO()
    pcm_segment.export(mp3_io, format="mp3")
    mp3_io.seek(0)

    return mp3_io




async def main():
    
    # result = await Runner.Run(agent, "What is the weather in San Francisco?")
    # print(result)
    
    # pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(english_agent))
    # buffer = np.zeros(samplerate * 3, dtype=np.int16)
    # audio_input = AudioInput(buffer=buffer)

    # result = await pipeline.run(audio_input)

    # # Create an audio player using `sounddevice`
    # player = sd.OutputStream(samplerate=samplerate, channels=1, dtype=np.int16)
    # player.start()

    # # Play the audio stream as it comes in
    # async for event in result.stream():
    #     if event.type == "voice_stream_event_audio":
    #         player.write(event.data)
    #     elif event.type == "voice_stream_event_lifecycle":
    #         # lifecycle
    #         pass    
    #     elif event.type == "voice_stream_event_error":
    #         # error
    #         pass

    await voice_assistant_optimized()
    


if __name__ == "__main__":
    asyncio.run(main())