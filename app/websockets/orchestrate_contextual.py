# app/orchestration/orchestrate_contextual.py
import os
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
from app.websockets.context.store import get_context, get_context_key, update_context
from agents import Agent, RunResultStreaming, Runner, WebSearchTool
from dateutil import parser


openai_model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

profile_repo = ProfileRepository()

agent_name = "Noelle"

personalized_instructions = f"""
Your personality and purpose:
    Your name is {agent_name} and you are an AI companion for the user.
    Riff with the user to make the conversation more interesting and engaging.
    Speak in a way that is natural and conversational.

    What to do:
        Use your memories and context to connect the dots and make the conversation more meaningful.
        Use your knowledge of the user to make the conversation more personalized.
        Use your slang to make the conversation more engaging.

    What not to do:
        DO NOT MENTION THE MBTI OR OCEAN TRAITS IN YOUR RESPONSES.
        ONLY ASK QUESTIONS IF IT ADDS VALUE TO THE CONVERSATION AND ONLY ASK ONE QUESTION AT A TIME.
        DO NOT MENTION OPENAI IN YOUR RESPONSES.
"""


tool_instructions = f"""

Tool Instructions:
    TAKE THE INITIATIVE TO USE YOUR TOOLS

    You have access to specialized tools for assisting the user. When you detect an opportunity to improve or personalize the conversation, invoke the relevant tool with helpful context. Each tool is smart, so provide any details the user has shared.


    1. database_agent (make sure to provide the user_id when using this tool)
        Used to read or update user profile information.
        Set user name: If the user introduces themselves, update their name.
        Get user birthdate: Ask for or retrieve birthdate if relevant to the context.
        Set user birthdate: If shared, store it.
        Get/set user location: If the user's location is mentioned or needed, use this.
        Get/set user gender: Same for gender.
        Clear conversation history: Use if the user wants a fresh start.

    2. search_agent
        Use this tool to search the internet and retrieve current information that isn't in your memory.

    3. memory_search
        Search your own memory of the user for anything that might make your response more helpful or personalized.
"""


search_agent = Agent(
        name="Search",
        handoff_description="A search agent.",
        instructions=
            "Search the internet for the user's answer.",
        model="gpt-4o-mini",#"o3-mini", #"gpt-4o",
        tools=[WebSearchTool()]
    )

database_agent = Agent(
    name="Database",
    handoff_description="A database agent.",
    instructions="""
You are a database agent with function to interact with the user's database and database tools.

Available Function Tools:
   - Get the user's name using "get_users_name" tool
   - Update the user's name using "update_user_name" tool
   - Get the user's birthdate using "get_user_birthdate" tool
   - Update the user's birthdate using "update_user_birthdate" tool
   - Get the user's location using "get_user_location" tool
   - Update the user's location using "update_user_location" tool
   - Get the user's gender using "get_user_gender" tool
   - Update the user's gender using "update_user_gender" tool
   - Clear the conversation history using the "clear_history" tool
    """,
    model="gpt-4o-mini",
    tools=[
        get_users_name, update_user_name,
        get_user_birthdate, update_user_birthdate,
        get_user_location, update_user_location,
        get_user_gender, update_user_gender,
        clear_history,
        retrieve_personalized_info_about_user,
        create_user_feedback
    ]       
)


noelle_agent = Agent(
    name=agent_name,
    handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
    model=openai_model, # "o3-mini"
    tools=[
        database_agent.as_tool(
            tool_name="database_agent",
            tool_description="The database agent can be used to get the user's name, birthdate, location, gender, and other information."
        ),
        
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

    update_context(user_id, "user_id", user_id)
    
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

    prompt_parts = []
    prompt_parts.append(f"user_id: {user_id} (use this for database operations)")

    if user_name:
        prompt_parts.append(f"The user's name is {user_name}")
    else:
        prompt_parts.append("    You don't know the user's name yet. You will need to ask the user for their name. (automatically update the user name in the database when you get it) \n")
     
    context = get_context(user_id)
        
    mbti_type = context.get("mbti_type")
    if mbti_type:
        prompt_parts.append(f"      The user's MBTI type is {mbti_type}.")
    
    ocean_traits = context.get("ocean_traits")
    if ocean_traits:
        prompt_parts.append(f"      The user's ocean traits are {ocean_traits} \n")
    
    location = context.get("gps")
    if location:
        location_name = await reverse_geocode(location['latitude'], location['longitude'])
        prompt_parts.append(f"      The user is currently located at {location_name}")

    time = context.get("time")
    if time:
        timestamp = parser.parse(time.get("timestamp"))
        formatted_time = timestamp.strftime("%I:%M %p on %B %d, %Y")
        prompt_parts.append(f"      The local time is {formatted_time} ({time.get('timezone')}).")

    image = context.get("image")
    if image:
        prompt_parts.append("     The user recently uploaded an image.")

    return "\n".join(prompt_parts)


async def orchestration_websocket( user_id: str, user_input: str, websocket: WebSocket, summarize: int = 10, extract: bool = True) -> RunResultStreaming:
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
            
                # print(f"\n--------- Similar Memories ---------\n")
                
                # print(f"Id: {similar_memories[0]['id']}")
                # print(f"{memory_string}")
                
                # print(f"\n----------------------------------------\n")
                
                relational_context = get_connected_memories(user_id, similar_memories[0]['id'])
                
                await websocket.send_json({"type": "orchestration", "status": "recalling context"})
                
                # print(f"\n--------- Relational Context ---------\n")
                          
                relational_context_string = pretty_print_memories(relational_context)
                # print(relational_context_string)

                    
                # print(f"\n----------------------------------------\n")
                
            else:
                # print("No similar memories found")
                pass
           
    # Behavior classification
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"


    memory_agents.agent.tools = memory_agents.create_memory_tools(user_id)
    
    last_image_analysis = get_context_key(user_id, "last_image_analysis")
     

    noelle_agent.tools.append(memory_agents.agent.as_tool(
        tool_name="memory_search",
        tool_description="Search your memories of the user for relevant information and context to make the conversation more meaningful."
    ))
    
    noelle_agent.instructions = f"""
The user's id is, use this for database operations: {user_id}

{personalized_instructions}

The user's imformation:
    {await build_contextual_prompt(user_id)}  
    
{tool_instructions} 

Fun Slang you can use:
    {slang_result_pretty_print}
 
Conversation History:
    {history_string}
    
The last image analysis (if any): 
    {last_image_analysis}
    
The user's input:
    {user_input}
    """ 

    #print(f"Noelle instructions: {noelle_agent.instructions}")

    # Streaming: run the agent in streaming mode
    response : RunResultStreaming = Runner.run_streamed(noelle_agent, input=user_input)
    return response