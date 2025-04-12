# app/websocket_handlers/text_handler.py
import asyncio
import base64
import os
from agents import Agent, RunResultStreaming
from fastapi import WebSocket
from openai import AsyncOpenAI
from app.supabase.conversation_history import Message, append_message_to_history, replace_conversation_history_with_summary
from app.supabase.profiles import ProfileRepository
from app.utils.token_count import calculate_credits_to_deduct, calculate_provider_cost
from app.websockets.context.store import get_context, get_context_key, update_context
from app.websockets.orchestrate_contextual import build_contextual_prompt, orchestration_websocket
from app.websockets.schemas.messages import OrchestrateMessage, UIActionMessage, TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def handle_text(agent: Agent, websocket: WebSocket, message: TextMessage, user_id: str):
    await websocket.send_json({"type": "text_action", "status": "ok"})
    update_context(user_id, "last_message", message.text)
    update_context(user_id, "settings", message)
    # response = await Runner.run(agent, message.text)
    # await websocket.send_json({"type": "ai_response", "text": response.final_output})
    
    print("Added Text: ", get_context(user_id))

async def handle_audio(agent: Agent, websocket: WebSocket, message: AudioMessage, user_id: str):
    await websocket.send_json({"type": "audio_action", "status": "ok"})
    update_context(user_id, "settings", message)
    # Transcribe audio using Whisper
    audio_bytes = base64.b64decode(message.audio)
    user_transcript = await stt(audio_bytes)

    await websocket.send_json({"type": "user_transcript", "text": user_transcript})
    update_context(user_id, "last_message", user_transcript)
    

# TODO: handle everything below this
async def handle_image(websocket: WebSocket, message: ImageMessage, user_id: str):
    await websocket.send_json({"type": "image_action", "status": "ok"})

    update_context(user_id, "image", {"format": message.format})

async def handle_gps(websocket: WebSocket, message: GPSMessage, user_id: str):
    await websocket.send_json({"type": "gps_action", "status": "ok"})
    update_context(user_id, "gps", {
        "latitude": message.coords.latitude,
        "longitude": message.coords.longitude,
        "altitude": message.coords.altitude,
        "speed": message.coords.speed,
    })

    # print("Context: ", get_context(user_id))    


async def handle_time(websocket: WebSocket, message: TimeMessage, user_id: str):
    update_context(user_id, "time", {
        "timestamp": message.timestamp,
        "timezone": message.timezone
    })
    await websocket.send_json({"type": "time_action", "status": "ok"})

async def handle_ui_action(websocket: WebSocket, message: UIActionMessage):
    # Just send it back for now
    await websocket.send_json({
        "type": "ui_action",
        "action": message.action,
        "target": message.target,
        "status": "ok"
    })

async def handle_orchestration(agent: Agent, websocket: WebSocket, message: OrchestrateMessage, user_id: str):
    await websocket.send_json({"type": "orchestration", "status": "processing"})
    
    print("Orchestrating: ", message.user_input)
    
    system_prompt = await build_contextual_prompt(user_id)
    
    print( "System prompt", system_prompt)
    
    agent.instructions = system_prompt
    
    user_input = get_context_key(user_id, "last_message")
    settings = get_context_key(user_id, "settings")
        
    print("Settings: ", settings)

    result : RunResultStreaming = await orchestration_websocket(user_id=user_id, agent=agent, user_input=user_input, websocket=websocket, extract=settings.extract, summarize=settings.summarize)

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            continue

        elif event.type == "agent_updated_stream_event":
            await websocket.send_json({
                "type": "agent_updated",
                "text": event.new_agent.name
            })

        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                await websocket.send_json({
                    "type": "tool_call_item",
                    "text": event.item.raw_item.name
                })

            elif event.item.type == "tool_call_output_item":
                await websocket.send_json({
                    "type": "tool_call_output_item",
                    "text": event.item.output
                })

            elif event.item.type == "message_output_item":
                print("AI Response: ", event.item.raw_item.content[0].text)
                await websocket.send_json({
                    "type": "ai_response",
                    "text":  event.item.raw_item.content[0].text
                })
                
    final = result.final_output
    await websocket.send_json({"type": "ai_transcript", "text": final})
    await websocket.send_json({"type": "orchestration", "status": "done"})
    
    history = append_message_to_history(user_id, agent.name, final)

    # Process the history and costs in the background
    asyncio.create_task(process_history(user_id, history, summarize=10, extract=True))
    
    
    settings = get_context_key(user_id, "settings")
    if settings.type == "audio":
        # send audio response
        encoded_audio = await tts(final, settings.voice)
        await websocket.send_json({"type": "audio_response", "audio": encoded_audio})


# Helpers
async def stt(audio_bytes: bytes) -> str:
    transcript_response = await openai_client.audio.transcriptions.create(
        model="whisper-1", #"whisper-1", gpt-4o-transcribe, gpt-4o-mini-transcribe
        file=("audio.webm", audio_bytes, "audio/webm"),
    )
    user_transcript = transcript_response.text
    return user_transcript

async def tts(text :str, voice :str) -> str:
    # # Generate AI audio (TTS)
    ai_audio_stream = await openai_client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
    )

    audio_data = await ai_audio_stream.aread()

    # # Stream audio data back to frontend as base64 chunks
    encoded_audio = base64.b64encode(audio_data).decode()
    return encoded_audio
    
async def process_history(user_id: str, history: list[Message], summarize: int = 10, extract: bool = True):
    
    # Get the user input from the history (second to the last message)
    user_message = history[-2]
    user_input = user_message.content
        
    # Get the agents final output from the history (last message)
    ai_message = history[-1]
    ai_output = ai_message.content
        
    # calculate costs
    provider_cost = calculate_provider_cost(user_input, ai_output)
    credits_cost = calculate_credits_to_deduct(provider_cost)
    
    # deduct credits
    profile_repo = ProfileRepository()
    profile_repo.deduct_credits(user_id, credits_cost)
    
    # costs = f"""
    # Provider Cost: {provider_cost}
    # Credits Cost: {credits_cost}
    # """
    #logging.info(f"Costs: {costs}")

    # replace history with summary
    if len(history) >= summarize:
        asyncio.create_task(replace_conversation_history_with_summary(user_id, extract))
