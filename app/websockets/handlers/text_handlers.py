# app/websocket_handlers/text_handler.py
import asyncio
import base64
from io import BytesIO
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


async def handle_text(websocket: WebSocket, message: TextMessage, user_id: str):
    await websocket.send_json({"type": "text_action", "status": "ok"})
    update_context(user_id, "last_message", message.text)
    update_context(user_id, "settings", message)
    # response = await Runner.run(agent, message.text)
    # await websocket.send_json({"type": "ai_response", "text": response.final_output})
    
    print("Added Text: ", get_context(user_id))

async def handle_audio(websocket: WebSocket, message: AudioMessage, user_id: str):
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

    
    image_analysis = await analyze_image(message.data, message.format)
    
    update_context(user_id, "image", {"analysis": image_analysis})
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
    update_context(user_id, "time", {
        "timestamp": message.timestamp,
        "timezone": message.timezone
    })
    await websocket.send_json({"type": "time_action", "status": "ok"})

<<<<<<< Updated upstream
async def handle_ui_action(websocket: WebSocket, message: UIActionMessage):
    # Just send it back for now
    await websocket.send_json({
        "type": "ui_action",
        "action": message.action,
        "target": message.target,
        "status": "ok"
    })
=======

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
    

    
    
    
    
>>>>>>> Stashed changes

async def handle_orchestration(websocket: WebSocket, message: OrchestrateMessage, user_id: str):
    await websocket.send_json({"type": "orchestration", "status": "processing"})
    
    user_input = get_context_key(user_id, "last_message")
    settings = get_context_key(user_id, "settings")
        
    print("Settings: ", settings)

<<<<<<< Updated upstream
    result : RunResultStreaming = await orchestration_websocket(user_id=user_id, agent=agent, user_input=user_input, websocket=websocket, extract=settings.extract, summarize=settings.summarize)
=======
    result : RunResultStreaming = await orchestration_websocket(user_id=user_id, user_input=user_input, websocket=websocket, extract=message.extract, summarize=message.summarize)

    asyncio.create_task(handle_ui_action(websocket, message.user_input))
>>>>>>> Stashed changes

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
    
    # TODO: change this to the actual agent name dynamically
    history = append_message_to_history(user_id, "Noelle", final)

    # Process the history and costs in the background
    asyncio.create_task(process_history(user_id, history, summarize=10, extract=True))
    
    
    settings = get_context_key(user_id, "settings")
    if settings.type == "audio":
        # send audio response
        encoded_audio = await tts(final, settings.voice)
        await websocket.send_json({"type": "audio_response", "audio": encoded_audio})


# Helpers

async def analyze_image(image_data: bytes, image_format: str) -> str:
    try:
        # Decode base64 image data
        image_data = base64.b64decode(image_data)
        image_format = image_format.lower()

       # Create a readable image file-like object
        image_file = BytesIO(image_data)

        # Optionally: Run analysis using OpenAI Vision
        result = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What do you see in this image?"},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/{image_format};base64,{image_data}"
                        }}
                    ],
                },
            ],
            max_tokens=1000
        )

        analysis = result.choices[0].message.content

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
    
    # costs = f"""
    # Provider Cost: {provider_cost}
    # Credits Cost: {credits_cost}
    # """
    #logging.info(f"Costs: {costs}")

    # replace history with summary
    if len(history) >= summarize:
        asyncio.create_task(replace_conversation_history_with_summary(user_id, extract))
