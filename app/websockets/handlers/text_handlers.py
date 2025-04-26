# app/websocket_handlers/text_handler.py
import asyncio
import base64
import os
from agents import Agent, RunResultStreaming, Runner
from fastapi import WebSocket
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.supabase.conversation_history import Message, append_message_to_history, replace_conversation_history_with_summary
from app.supabase.profiles import ProfileRepository
from app.utils.token_count import calculate_credits_to_deduct, calculate_provider_cost
from app.websockets.context.store import get_context_key, update_context
from app.websockets.orchestrate_contextual import orchestration_websocket
from app.websockets.schemas.messages import LocalLingoMessage, MultistepMessage, OrchestrateMessage, RawMessage, UIActionMessage, TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage, FeedbackMessage


from app.function.memory_extraction import MemoryExtractionService
from app.personal_agents.slang_extraction import SlangExtractionService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def handle_text(websocket: WebSocket, message: TextMessage, user_id: str):
    await websocket.send_json({"type": "text_action", "status": "ok"})
    update_context(user_id, "last_message", message.text)
    update_context(user_id, "settings", message)    


async def handle_audio(websocket: WebSocket, message: AudioMessage, user_id: str):
    await websocket.send_json({"type": "audio_action", "status": "ok"})
    update_context(user_id, "settings", message)
    # Transcribe audio using Whisper
    audio_bytes = base64.b64decode(message.audio)
    user_transcript = await stt(audio_bytes)

    await websocket.send_json({"type": "user_transcript", "text": user_transcript})
    update_context(user_id, "last_message", user_transcript)
    

async def handle_image(websocket: WebSocket, message: ImageMessage, user_id: str):
    await websocket.send_json({"type": "image_action", "status": "image ok"})
    await websocket.send_json({"type": "info", "text": "Analyzing image..."})
    image_analysis = await analyze_image(image_data=message.data, image_message=message.input, image_format=message.format)    
    update_context(user_id, "last_image_analysis", image_analysis)
    await websocket.send_json({"type": "image_analysis", "text": image_analysis})


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
    await websocket.send_json({"type": "time_action", "status": "ok"})
    update_context(user_id, "time", {"timestamp": message.timestamp, "timezone": message.timezone})


ui_action_agent = Agent(
    name="UI Action Agent",
    instructions="""
    Given the user's input, decide if you need to send a ui action to the user.
    If you do, return the action, target, and status.
    If you don't, return a ui message with the action as "none".
    Only return an action if you are sure about the action.
    Return with the action of "none" if you are unsure.
    
    You can choose one of the following actions:
    - toggle_conversation_history
    - toggle_knowledge_base
    - toggle_credits
    - toggle_settings
    - toggle_inoformation
    - toggle_capture
    - toggle_notifications
    
    Example:
    User: "Show me the conversation history"
    UI Action: "toggle_conversation_history"
    
    User: "What is the weather in Tokyo?"
    UI Action: "none"
    """,
    model="gpt-4o-mini",
    output_type=UIActionMessage
)

async def handle_ui_action(websocket: WebSocket, message: str):
    # decide what to do based on the user input
    ui_result = await Runner.run(ui_action_agent, message)
    
    ui_action: UIActionMessage = UIActionMessage.model_validate(ui_result.final_output)
    
    if ui_action.action != "none":
        response_dict = ui_action.model_dump()
        await websocket.send_json(response_dict)
    
async def handle_raw_mode(websocket: WebSocket, message: RawMessage, user_id: str):
    await websocket.send_json({"type": "raw_action", "status": "Raw Mode ok"})
    update_context(user_id, "raw_mode", message.is_raw)

async def handle_feedback(websocket: WebSocket, message: FeedbackMessage, user_id: str):
    await websocket.send_json({"type": "feedback_action", "status": "Feedback ok"})
    update_context(user_id, "feedback", message.feedback_type)

async def handle_local_lingo(websocket: WebSocket, message: LocalLingoMessage, user_id: str):
    await websocket.send_json({"type": "local_lingo_action", "status": "Local Lingo ok"})
    update_context(user_id, "local_lingo", message.local_lingo)

async def handle_orchestration(websocket: WebSocket, message: OrchestrateMessage, user_id: str):
    await websocket.send_json({"type": "orchestration", "status": "processing"})
    
    user_input = get_context_key(user_id, "last_message")
    settings = get_context_key(user_id, "settings")
        
    result : RunResultStreaming = await orchestration_websocket(user_id=user_id, user_input=user_input, websocket=websocket, extract=message.extract, summarize=message.summarize)

    asyncio.create_task(handle_ui_action(websocket, message.user_input))

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
                #print("AI Response: ", event.item.raw_item.content[0].text)
                await websocket.send_json({
                    "type": "ai_response",
                    "text":  event.item.raw_item.content[0].text
                })
                
    final = result.final_output
    await websocket.send_json({"type": "ai_transcript", "text": final})
    await websocket.send_json({"type": "orchestration", "status": "done"})
    
    # TODO: change this to the actual agent name dynamically
    history = append_message_to_history(user_id, "Noelle", final)

    # Process the history and costs in the background
    asyncio.create_task(process_history(user_id, history, summarize=message.summarize, extract=message.extract))
    
    settings = get_context_key(user_id, "settings")
    if settings.type == "audio":
        # send audio response
        encoded_audio = await tts(final, settings.voice)
        await websocket.send_json({"type": "audio_response", "audio": encoded_audio})


# Helpers
async def analyze_image(image_data: list[str], image_message: str = "what's in this image?", image_format: str = "jpeg") -> str: # image_data is base64 encoded
    try:    
        # Build content array with the text message first
        content = [{ "type": "input_text", "text": image_message }]
        
        # Add all images from the list
        for img in image_data:
            content.append({
                "type": "input_image",
                "image_url": f"data:image/{image_format};base64,{img}",
            })
        
        response = await openai_client.responses.create(
            model="gpt-4o-mini",
            input=[{"role": "user", "content": content}]
        )
        
        analysis = response.output_text
                
        return analysis

    except Exception as e:
        return "Failed to analyze image"

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
    
    # replace history with summary if the history is longer than the summarize value
    if len(history) > summarize:
        asyncio.create_task(replace_conversation_history_with_summary(user_id))
        
        if extract:        
            # get all message from history that match the user_id
            history_string = [msg for msg in history if msg.user_id == user_id]
        
            # Convert the history to a string
            history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in history_string])
            
            # Extract knowledge from the history.
            extraction = MemoryExtractionService(user_id)
            extract_task = asyncio.create_task(extraction.extract_memory(history_string))
            await extract_task

            # Run MBTI analysis
            mbti_service = MBTIAnalysisService(user_id)
            mbti_task = asyncio.create_task(mbti_service.analyze_message(history_string))
            await mbti_task

            # Run OCEAN analysis
            ocean_service = OceanAnalysisService(user_id)
            ocean_task = asyncio.create_task(ocean_service.analyze_message(history_string))
            await ocean_task
                    
            # Run SLANG analysis
            slang_service = SlangExtractionService(user_id)
            slang_task = asyncio.create_task(slang_service.extract_slang(history_string))
            await slang_task
    
    
    # costs = f"""
    # Provider Cost: {provider_cost}
    # Credits Cost: {credits_cost}
    # """
    #logging.info(f"Costs: {costs}")