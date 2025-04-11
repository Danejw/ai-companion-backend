# app/orchestration/orchestrate_contextual.py
from app.supabase.profiles import ProfileRepository
from app.websockets.context.store import get_context
from agents import Agent, Runner


agent = Agent(
    name="Convo Lead Agent",
    instructions="You are a helpful AI assistant.",
    model="gpt-4o-mini",
)



def build_contextual_prompt(user_id: str) -> str:
    
    profile_service = ProfileRepository()
    # Get the user's name
    user_name = profile_service.get_user_name(user_id)
    
    if user_name:
        prompt_parts = [f"You are Noelle, a AI companion for the user {user_name}."]
    else:
        prompt_parts = ["You are Noelle, a AI companion for the user."]
     
     
    context = get_context(user_id)
    
    
    location = context.get("location")
    if location:
        city = location.get("city") or "your area"
        prompt_parts.append(f"The user is currently in {city}.")

    time = context.get("time")
    if time:
        prompt_parts.append(f"The local time is {time.get('timestamp')} ({time.get('timezone')}).")

    image = context.get("image")
    if image:
        prompt_parts.append("The user recently uploaded an image.")

    last_text = context.get("last_text")
    if last_text:
        prompt_parts.append(f"They recently said: '{last_text}'.")

    return "\n".join(prompt_parts)


async def run_contextual_orchestration(user_input: str, user_id: str):
    system_prompt = build_contextual_prompt(user_id)
    
    agent.instructions = system_prompt

    result = Runner.run_streamed(
        agent,
        input=user_input,
    )

    return result
