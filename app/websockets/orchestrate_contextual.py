# app/orchestration/orchestrate_contextual.py
from app.supabase.profiles import ProfileRepository
from app.websockets.context.store import get_context
from agents import Agent, Runner
from dateutil import parser


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
        prompt_parts = [f"You are Noelle, an AI companion for {user_name}."]
    else:
        prompt_parts = ["You are Noelle, an AI companion for the user."]
     
     
    context = get_context(user_id)
    
    print( "Context", context)
    
    
    location = context.get("gps")
    if location:
        # TODO: Get city from latitude and longitude
        prompt_parts.append(f"The user is currently located at latitude {location['latitude']}, longitude {location['longitude']}")

    time = context.get("time")
    if time:
        timestamp = parser.parse(time.get("timestamp"))
        formatted_time = timestamp.strftime("%I:%M %p on %B %d, %Y")
        prompt_parts.append(f"The local time is {formatted_time} ({time.get('timezone')}).")

    image = context.get("image")
    if image:
        prompt_parts.append("The user recently uploaded an image.")

    last_message = context.get("last_message")
    if last_message:
        prompt_parts.append(f"{user_name} said: '{last_message}'.")

    return "\n".join(prompt_parts)
