from http.client import HTTPException
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.personal_agents.planner import PlannerService
from app.personal_agents.slang_extraction import SlangExtractionService
from app.psychology.theory_planned_behavior import TheoryPlannedBehaviorService
from app.psychology.intent_classification import IntentClassificationService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.supabase.conversation_history import append_message_to_history, get_or_create_conversation_history, replace_conversation_history_with_summary
from app.supabase.profiles import ProfileRepository
from app.utils.moderation import ModerationService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import asyncio
import logging
from app.auth import verify_token
from agents import Agent, Runner, WebSearchTool, FileSearchTool, function_tool
from app.utils.token_count import calculate_credits_to_deduct, calculate_provider_cost, count_tokens


router = APIRouter()


class UserInput(BaseModel):
    message: str
    

    
class ErrorResponse(BaseModel):
    error: bool
    message: str
    
class AIResponse(BaseModel):
    response: str
    error: ErrorResponse
    

profile_repo = ProfileRepository()


def get_user_name(user_id: str) -> str:
    return profile_repo.get_user_name(user_id)

@function_tool
def get_users_name(user_id: str) -> str:
    """
    Retrieves the name of the user from the profile repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    
    Returns:
    - str: the name of the user
    """ 
    return profile_repo.get_user_name(user_id)



@function_tool
def update_user_name(user_id: str, name: str) -> str:
    """
    Updates the user's name in the profile repository.

    Parameters:
    - user_id (str): The unique identifier of the user.
    - name (str): The new name to update for the user.

    Returns:
    - str: the names of the user
    """ 
    return profile_repo.update_user_name(user_id, name)

@function_tool
async def retrieve_personalized_info_about_user(user_id: str, query: str) -> str:
    """
    Retireve personalized information about the user for more personalized, deeper, and meaningful conversation.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    
    - query (str): The query to find addtional information about the user to personalize the conversation.

    Returns:
    - str: the addtional information about the user
    """

    knowledge_service = KnowledgeExtractionService(user_id)
    try:
        return await knowledge_service.retrieve_similar_knowledge(query)
    except Exception as e:
        logging.error(f"Error retrieving knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/orchestration")
async def orchestrate(user_input: UserInput, user=Depends(verify_token)):
    """
    Orchestrates sentiment analysis, personality assessments (MBTI, OCEAN),
    knowledge extraction, similarity search, and dynamic AI response generation.
    """
    try:
        user_id = user["id"]
        message = user_input.message
        
        logging.info(f"User ID: {user_id}")

        # Run analyses concurrently
        mbti_service = MBTIAnalysisService(user_id)
        mbti_task = asyncio.create_task(mbti_service.analyze_message(message))
        
        ocean_service = OceanAnalysisService(user_id)
        ocean_task = asyncio.create_task(ocean_service.analyze_message(message))

        knowledge_service = KnowledgeExtractionService(user_id)

        # Wait for all tasks to complete
        await mbti_task  # MBTI updates asynchronously
        await ocean_task  # OCEAN updates asynchronously
        
        # Retrieve stored MBTI & OCEAN
        mbti_type = mbti_service.get_mbti_type()
        style_prompt = mbti_service.generate_style_prompt(mbti_type)
        ocean_traits = ocean_service.get_personality_traits()
        
        logging.info(f"MBTI Type: {mbti_type, style_prompt}")
        logging.info(f"OCEAN Traits: {ocean_traits}")

        # Run similarity search on extracted knowledge
        similar_knowledge = await knowledge_service.retrieve_similar_knowledge(message, top_k=3)

        # Construct dynamic system prompt
        system_prompt = (
            f"MBTI Type: {mbti_type, style_prompt}.\n"
            f"OCEAN Traits: {ocean_traits}.\n"
            f"Similar Previous Knowledge: {similar_knowledge}."
        )
        
        logging.info(f"System prompt: {system_prompt}")

        # Generate AI response using system prompt
        conversational_agent = Agent(
            name="Wit",
            handoff_description="A conversational response agent given the context.",
            instructions= system_prompt + "\n\n You are a conversational agent. Respond to the user using the information provided.",
            model="gpt-4o-mini",
            tools=[
                WebSearchTool(),
                FileSearchTool()
            ]
        )

        response = await Runner.run(conversational_agent, message)
              
        logging.info(f"Response Object: {response}")  

        return response.final_output

    except Exception as e:
        logging.error(f"Error processing orchestration: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
@router.post("/convo-lead")
async def convo_lead(user_input: UserInput, user=Depends(verify_token)) -> AIResponse:
    """
    Leads the conversation with the user. Asking questions to get to know the user better.  
    """
    user_id = user["id"]
    
    credits = profile_repo.get_user_credit(user_id)
    if credits is None or credits < 1:
        return AIResponse(response="", error=ErrorResponse(error=True, message="NO_CREDITS"))    
    
    
    # Check if the user's message is safe
    moderation_service = ModerationService()
    is_safe = moderation_service.is_safe(user_input.message)
    if not is_safe:
        return AIResponse(response="", error=ErrorResponse(error=True, message="FLAGGED_CONTENT"))
    # Get the users name
    user_name = get_user_name(user_id)
    
    # Append the new user message to the conversation history
    if user_name is None:
        append_message_to_history(user_id, "user", user_input.message)
    else:
        append_message_to_history(user_id, user_name, user_input.message)
    
    # Initialize the services
    mbti_service = MBTIAnalysisService(user_id)    
    ocean_service = OceanAnalysisService(user_id)
    slang_service = SlangExtractionService(user_id)
    intent_service = IntentClassificationService(user_id)
    tpb_service = TheoryPlannedBehaviorService(user_id)

    # Retrieve stored MBTI & OCEAN
    mbti_type = mbti_service.get_mbti_type()
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    ocean_traits = ocean_service.get_personality_traits()
    slang_result = slang_service.retrieve_similar_slang(user_input.message)
    
    
    # Retrieve or create the conversation context for the user
    history = get_or_create_conversation_history(user_id)
    
    # Convert history list to string
    history_string = "\n".join(history)
    
    # Classify the intent of the user
    intent = await intent_service.classify_intent(history_string)
    if intent.confidence_score < 0.85:
        intent = "Unconfident in the intent of the user, a possible clarifying question: " + intent.clarifying_question + (f"if used ask is it in the most natural way possible")
    
    # Classify the behavior of the user
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"
    
    instructions = f"""
        You are a conversational agent. 
        
        The user_id is {user_id}.
        You are having a conversation with (this is the user's name) {user_name}. 
        If their name is not available, ask for it first. 
        When the user's name is given, update it using the update_user_name tool.
                
        You will lead the conversation with the user. You will ask questions to get to know the user better.
        Ask your questions in a natural way as the conversation progresses. Ask questions that are relevant to gain accurate MBTI type and OCEAN analysis traits of the user.
        Ask questions that are relevant to the user's message.
        
        Keep your language simple, natural, and conversational. Keep it at a 5th grade level.
        
        DO NOT MENTION MBTI OR OCEAN analysis in your response.
        DO NOT RESPOND IN MARKDOWN FORMAT. Your response should feel human-like and conversational.
        DO NOT ask more than 1 question at a time.
        
        Personality OCEAN Traits of the {user_id} are: {ocean_traits}
        Personality MBTI Type of the {user_id} is: {mbti_type}
        
        Your conversational style should be: {style_prompt}
        
        The intent of the user is: {intent}
        The behavior of the user is: {tpb}
        
        Adapt to the {user_name} language and slang.
        Use similar language as the user, here are some examples: {slang_result}

        Conversation History: {history_string}
    """
    
    logging.info(f"Convo Lead Instructions: {instructions}")
    
    # Initialize the planner agent
    planner_agent = PlannerService().agent
    
    # Generate AI response using system prompt
    convo_lead_agent = Agent(
        name="Astra AI",
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o-mini",
        tools=[
            get_users_name, update_user_name, 
            retrieve_personalized_info_about_user,
            planner_agent.as_tool(
                tool_name="create_plan",
                tool_description="A tool that creates a plan for the user to follow."
            )
        ]
    )
    
    try:
        # Count the tokens in the user's message
        input_tokens = count_tokens(user_input.message)
                
        response = await Runner.run(convo_lead_agent, user_input.message)
    
        logging.info(f"Convo Lead Response: {response}")
            
        # Append the agent's response back to the conversation history
        append_message_to_history(user_id, convo_lead_agent.name, response.final_output)
        
        if len(history) >= 10:
            await replace_conversation_history_with_summary(user_id)
            
        # Count the tokens in the agent's response
        output_tokens = count_tokens(response.final_output)

        # Calculate the cost of the tokens
        provider_cost = calculate_provider_cost(user_input.message, convo_lead_agent.model)
        credits_cost = calculate_credits_to_deduct(provider_cost)
        
        costs = f"""
        Input Tokens: {input_tokens}
        Output Tokens: {output_tokens}
        Total Tokens: {input_tokens + output_tokens}\n
        Provider Cost: {provider_cost}
        Credits Cost: {credits_cost}
        """
        logging.info(f"Costs: {costs}")
        
        # Deduct the credits from the user's balance
        profile_repo.deduct_credits(user_id, credits_cost)
                    
        return AIResponse(response=response.final_output, error=ErrorResponse(error=False, message=""))
            
    except Exception as e:
        logging.error(f"Error processing convo lead: {e}")
        return {"error": "Internal Server Error"}
    


    


        
        

        

