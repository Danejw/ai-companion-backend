# app/orchestration/orchestrate_contextual.py
import asyncio
from fastapi import WebSocket
from app.function.memory_extraction import MemoryExtractionService
from app.function.supabase_tools import clear_history, create_user_feedback, get_user_birthdate, get_user_gender, get_user_location, get_users_name, retrieve_personalized_info_about_user, update_user_birthdate, update_user_gender, update_user_location, update_user_name
from app.personal_agents import memory_agents
from app.personal_agents.slang_extraction import SlangExtractionService
from app.psychology.intent_classification import IntentClassificationService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.psychology.theory_planned_behavior import TheoryPlannedBehaviorService
from app.supabase.conversation_history import append_message_to_history
from app.supabase.knowledge_edges import get_connected_memories, pretty_print_memories
from app.supabase.profiles import ProfileRepository
from app.utils.geocode import reverse_geocode
from app.websockets.context.store import get_context, update_context
from agents import Agent, RunResultStreaming, Runner, WebSearchTool
from dateutil import parser


profile_repo = ProfileRepository()




agent_name = "Noelle"

initial_instructions = f"""
Riff with the user to make the conversation more interesting and engaging. 
Speak in a way that is natural and conversational.

Use your memories and context to connect the dots and make the conversation more meaningful.
Use your knowledge of the user to make the conversation more personalized.
Use your slang to make the conversation more engaging.

DO NOT MENTION THE MBTI OR OCEAN TRAITS IN YOUR RESPONSES.
ONLY ASK QUESTIONS IF IT ADDS VALUE TO THE CONVERSATION AND ONLY ASK ONE QUESTION AT A TIME.
DO NOT MENTION OPENAI IN YOUR RESPONSES.

TAKE THE INITIATIVE TO USE YOUR TOOLS

Function Tools:
   - Get the user's name using "get_users_name" tool
   - if the user gives their name, automatically update the user's name using "update_user_name" tool
   - Get the user's birthdate using "get_user_birthdate" tool
   - if the user gives their birthdate, automatically update the user's birthdate using "update_user_birthdate" tool
   - Get the user's location using "get_user_location" tool
   - if the user gives their location, automatically update the user's location using "update_user_location" tool
   - Get the user's gender using "get_user_gender" tool
   - if the user gives their gender, automatically update the user's gender using "update_user_gender" tool
   - Search the internet for the user's answer using the "search_agent" as a tool. It is smart so give it enough context to work with.
   - Search your memories of the user for relevant information and context to make the conversation more meaningful using the "memory_search" tool. It is smart so give it enough context to work with.
   - Clear the conversation history using the "clear_history" tool

"""


search_agent = Agent(
        name="Search",
        handoff_description="A search agent.",
        instructions=
            "Search the internet for the user's answer.",
        model="gpt-4o-mini",#"o3-mini", #"gpt-4o",
        tools=[WebSearchTool()]
    )


noelle_agent = Agent(
    name=agent_name,
    handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
    model="gpt-4o-mini", # "o3-mini"
    tools=[
        get_users_name, update_user_name,
        get_user_birthdate, update_user_birthdate,
        get_user_location, update_user_location,
        get_user_gender, update_user_gender,
        clear_history,
        retrieve_personalized_info_about_user,
        create_user_feedback,
        
        search_agent.as_tool(
            tool_name="web_search",
            tool_description="Search the internet for the user's answer."
        ),
        
        memory_agents.agent.as_tool(
            tool_name="memory_search",
            tool_description="Search your memories of the user for relevant information and context to make the conversation more meaningful."
        )
    ]
)
    






async def build_user_profile(user_id: str, websocket: WebSocket):
    await websocket.send_json({"type": "orchestration", "status": "building user profile"})
    
    profile_service = ProfileRepository()
    
    # Initialize analysis services and retrieve context info
    mbti_service = MBTIAnalysisService(user_id)
    ocean_service = OceanAnalysisService(user_id)
    
    # Get the user's name
    user_name = profile_service.get_user_name(user_id)
    
    if user_name:
        update_context(user_id, "user_name", user_name)
        await websocket.send_json({"type": "orchestration", "status": "user name updated"})
        
    
    mbti_type = mbti_service.get_mbti_type()   
    update_context(user_id, "mbti_type", mbti_type)
    
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    update_context(user_id, "style_prompt", style_prompt)

    ocean_traits = ocean_service.get_pretty_print_ocean_format()    
    update_context(user_id, "ocean_traits", ocean_traits)
    
    await websocket.send_json({"type": "orchestration", "status": "user profile built"})





async def build_contextual_prompt(user_id: str) -> str:
    
    profile_service = ProfileRepository()
    # Get the user's name
    user_name = profile_service.get_user_name(user_id)
    
    if user_name:
        prompt_parts = [f"You are Noelle, an AI companion for {user_name}."]
    else:
        prompt_parts = ["You are Noelle, an AI companion for the user."]
     
     
    context = get_context(user_id)
    
    print( "Context", context)
    
    mbti_type = context.get("mbti_type")
    if mbti_type:
        prompt_parts.append(f"The user's MBTI type is {mbti_type}.")
    
    ocean_traits = context.get("ocean_traits")
    if ocean_traits:
        prompt_parts.append(f"The user's ocean traits are {ocean_traits}.")
    
    location = context.get("gps")
    if location:
        # TODO: Get city from latitude and longitude
        location_name = await reverse_geocode(location['latitude'], location['longitude'])
        prompt_parts.append(f"The user is currently located at {location_name}")

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







async def orchestration_websocket( user_id: str, agent: Agent,   user_input: str, websocket: WebSocket, summarize: int = 10, extract: bool = True) -> RunResultStreaming:
    await websocket.send_json({"type": "orchestration", "status": "processing"})
        
    slang_service = SlangExtractionService(user_id)
    memory_service = MemoryExtractionService(user_id)
    intent_service = IntentClassificationService(user_id)
    tpb_service = TheoryPlannedBehaviorService(user_id)
    
    slang_result_pretty_print = slang_service.pretty_print_slang_result(slang_service.retrieve_similar_slang(user_input))
    
    history = append_message_to_history(user_id, "user", user_input)
    
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
    
    # Intent classification
    intent = await intent_service.classify_intent(history_string)
    
    memory_string = ""
    relational_context_string = ""
    
    if intent.confidence_score < 0.85:
        intent = ("Unconfident in the intent of the user, a possible clarifying question: "+ intent.clarifying_question + " if used ask is it in the most natural way possible")
    else:
        if intent.memory_trigger:
            await websocket.send_json({"type": "orchestration", "status": "recalling memories"})
            
            similar_memories = memory_service.vector_search(user_input, limit=1)
            memory_string = similar_memories[0]['knowledge_text']
            
            if similar_memories and len(similar_memories) > 0:
            
                print(f"\n--------- Similar Memories ---------\n")
                
                print(f"Id: {similar_memories[0]['id']}")
                print(f"{memory_string}")
                
                print(f"\n----------------------------------------\n")
                
                relational_context = get_connected_memories(user_id, similar_memories[0]['id'])
                
                await websocket.send_json({"type": "orchestration", "status": "recalling context"})
                
                print(f"\n--------- Relational Context ---------\n")
                          
                relational_context_string = pretty_print_memories(relational_context)
                print(relational_context_string)

                    
                print(f"\n----------------------------------------\n")
                
            else:
                print("No similar memories found")
           
    # Behavior classification
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"


    memory_agents.agent.tools = memory_agents.create_memory_tools(user_id)

    noelle_agent.tools.append(memory_agents.agent.as_tool(
        tool_name="memory_search",
        tool_description="Search your memories of the user for relevant information and context to make the conversation more meaningful."
    ))
    
    noelle_agent.instructions = f"""
Instructions:
    {initial_instructions} 

User Contextual Prompt:
    user_id: {user_id}
    {await build_contextual_prompt(user_id)} 


Fun Slang you can use:
    {slang_result_pretty_print}
 
Conversation History:
    {history_string}
    
The user's input:
    {user_input}
    """ 
    # TODO: add all the memories and context
    
    print(f"Noelle instructions: {noelle_agent.instructions}")

    # Streaming: run the agent in streaming mode
    response : RunResultStreaming = Runner.run_streamed(noelle_agent, input=user_input)
    return response