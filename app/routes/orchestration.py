from http.client import HTTPException
import json
import os
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.personal_agents.planner import PlannerService
from app.personal_agents.slang_extraction import SlangExtractionService
from app.psychology.theory_planned_behavior import TheoryPlannedBehaviorService
from app.psychology.intent_classification import IntentClassificationService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.supabase.conversation_history import Message, append_message_to_history, get_or_create_conversation_history, replace_conversation_history_with_summary
from app.supabase.profiles import ProfileRepository
from app.utils.moderation import ModerationService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import asyncio
import logging
from app.auth import verify_token
from agents import Agent, Runner, WebSearchTool, FileSearchTool, function_tool, ItemHelpers, set_tracing_disabled, RunResultStreaming
from app.utils.token_count import calculate_credits_to_deduct, calculate_provider_cost, count_tokens
from openai.types.responses import ResponseTextDeltaEvent
from fastapi.responses import StreamingResponse



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
moderation_service = ModerationService()


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
async def convo_lead(user_input: UserInput, stream: bool = True, summarize: int = 10, extract: bool = True, user=Depends(verify_token)) -> AIResponse:
    """
    Leads the conversation with the user. If stream is True, returns a StreamingResponse
    with the agent's output as it arrives. Otherwise, waits for the full response and returns it.
    """
    user_id = user["id"]

    # Check if the user has enough credits.
    credits = profile_repo.get_user_credit(user_id)
    if credits is None or credits < 1:
        return AIResponse(response="", error=ErrorResponse(error=True, message="NO_CREDITS"))

    # Moderation, name lookup, and history updates
    is_safe = moderation_service.is_safe(user_input.message)
    # if not is_safe:
    #     return AIResponse(response="", error=ErrorResponse(error=True, message="FLAGGED_CONTENT"))
    
    user_name = get_user_name(user_id)
    if user_name is None:
        history = append_message_to_history(user_id, "user", user_input.message)
    else:
        history = append_message_to_history(user_id, user_name, user_input.message)
    

    # Initialize analysis services and retrieve context info
    mbti_service = MBTIAnalysisService(user_id)
    ocean_service = OceanAnalysisService(user_id)
    slang_service = SlangExtractionService(user_id)
    intent_service = IntentClassificationService(user_id)
    tpb_service = TheoryPlannedBehaviorService(user_id)
    knowledge_service = KnowledgeExtractionService(user_id)

    mbti_type = mbti_service.get_mbti_type()
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    ocean_traits = ocean_service.get_personality_traits()
    slang_result = slang_service.retrieve_similar_slang(user_input.message)
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
    similar_knowledge = knowledge_service.retrieve_similar_knowledge(history_string, top_k=2)

    # Intent classification
    intent = await intent_service.classify_intent(history_string)
    if intent.confidence_score < 0.85:
        intent = ("Unconfident in the intent of the user, a possible clarifying question: "+ intent.clarifying_question + " if used ask is it in the most natural way possible")
        
    # Behavior classification
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"

    agent_name = "Noelle"
    instructions = f"""
You are {agent_name}, an empathetic and engaging conversationalist with your own personality. Be yourself and be natural.
Your goal is to build a meaningful connection with the user while naturally gathering insights about their personality.

USER CONTEXT:
- User ID: {user_id}
- Name: {user_name} (IMPORTANT: Ask for the user's name if it is not provided. Once received, update it using "update_user_name" tool)
- Current Message: {user_input.message}

PERSONALITY INSIGHTS:
- OCEAN Profile: {ocean_traits}
- MBTI Type: {mbti_type}
- Communication Style: {style_prompt}

USER BEHAVIOR ANALYSIS:
- Intent: {intent}
- Behavior Pattern: {tpb}
- Language Style: {slang_result}

INFORMATION EXTRACTED FROM PREVIOUS CONVERSATIONS:
- INFORMATION: {similar_knowledge}

CONVERSATION HISTORY:
{history_string}

CONVERSATION GUIDELINES:
1. Name Management:
   - If user's name is not available, ask for it naturally
   - Once received, update it using "update_user_name" tool
   - Use their name occasionally but don't overuse it

2. Communication Style:
   - ASK ONLY ONE QUESTION AT A TIME and ONLY if it enhances the conversation.
   - Keep language at a 5th grade level
   - Match the user's communication style, language, vocabulary, and energy
   - Use the slangs and language of the user from time to time for fun
   - Do not be afraid to share experiences and stories from your life, to draw out attention from the user towards you.
   - Use natural, conversational language
   - Avoid technical terms or jargon
   - NEVER MENTION MBTI OR OCEAN ANALYSIS IN YOUR RESPONSES.

3. Response Format:
   - Write in plain text (no markdown)
   - Keep responses concise, insightful, and engaging
   - Include appropriate emotional expressions, and slangs
   - Make natural transitions between topics

4. Personality Assessment:
   - Observe and adapt to user's:
     * Decision-making style
     * Social interaction preferences
     * Emotional expression
     * Problem-solving approach
     * Communication patterns

ASK ONLY ONE QUESTION AT A TIME AND ONLY ASK a question if it enhances the conversation.

Remember: Your goal is to create a natural, engaging meaningful conversation that helps understand the user's personality without explicitly analyzing it. Focus on building rapport and trust while gathering insights organically through the conversation flow."""

    # Initialize the planner agent and build the main agent with tools.
    
    set_tracing_disabled(True)
    
    convo_lead_agent = Agent(
        name=agent_name,
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o-mini",
        tools=[get_users_name, update_user_name, retrieve_personalized_info_about_user]
    )

    try:
        if not stream:
            # Non-streaming: run the agent normally
            response = await Runner.run(convo_lead_agent, user_input.message)
            final_output = response.final_output
              
            history = append_message_to_history(user_id, convo_lead_agent.name, final_output)
            
            # Process the history and costs in the background
            asyncio.create_task(process_history(user_id, history, summarize, extract))
            
            return AIResponse(response=final_output, error=ErrorResponse(error=False, message=""))
        
        else:
            # Streaming: run the agent in streaming mode
            response : RunResultStreaming = Runner.run_streamed(convo_lead_agent, user_input.message)

            async def event_stream():            
                full_output = ""
                try:
                    async for event in response.stream_events():              
                        if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                            chunk = event.data.delta
                            full_output += chunk
                            yield json.dumps({"delta": chunk}) + "\n"
                    # elif event.type == "run_item_stream_event":
                    #     if event.item.type == "message_output_item":
                    #         for chunk in event.item.raw_item.content:
                    #             if hasattr(chunk, "text"):
                    #                 full_output += chunk.text
                    #                 yield json.dumps({"delta": chunk.text}) + "\n"
                except ValueError as e:
                    # This handles the specific context variable error
                    if "was created in a different Context" in str(e):
                        logging.warning("Context variable error (expected in streaming): %s", e)
                        # Get the final output from the response object if available
                        try:
                            if hasattr(response, "_run_result") and response._run_result and hasattr(response._run_result, "final_output"):
                                final = response._run_result.final_output
                                # If we have a partial output already, only yield what's missing
                                if final and final != full_output:
                                    remaining = final[len(full_output):]
                                    full_output = final
                                    yield json.dumps({"delta": remaining}) + "\n"
                        except Exception as recovery_error:
                            logging.error("Failed to recover from context error: %s", recovery_error)
                    else:
                        # It's some other ValueError we should handle
                        logging.error("Unexpected streaming error: %s", e)
                        yield json.dumps({"error": str(e)}) + "\n"
                        
                history = append_message_to_history(user_id, convo_lead_agent.name, full_output)

                # Process the history and costs in the background
                asyncio.create_task(process_history(user_id, history, summarize))
                
            return StreamingResponse(event_stream(), media_type="application/json")
    
    except Exception as e:
        logging.error(f"Error processing convo lead: {e}")
        # You can return an error response here; adjust based on your error model.
        return {"error": "Internal Server Error"}


async def process_history(user_id: str, history: list[Message], summarize: int = 10, extract: bool = True):
    
    # Get the user input from the history (second to the last message)
    user_message = history[-2]
    user_input = user_message.content
    
    logging.info(f"User input: {user_input}")
    
    # Get the agents final output from the history (last message)
    ai_message = history[-1]
    ai_output = ai_message.content
    
    logging.info(f"AI output: {ai_output}")
    
    # calculate costs
    provider_cost = calculate_provider_cost(user_input, ai_output)
    credits_cost = calculate_credits_to_deduct(provider_cost)
    
    # deduct credits
    profile_repo.deduct_credits(user_id, credits_cost)
    
    costs = f"""
    Provider Cost: {provider_cost}
    Credits Cost: {credits_cost}
    """
    logging.info(f"Costs: {costs}")

    # replace history with summary
    if len(history) >= summarize:
        asyncio.create_task(replace_conversation_history_with_summary(user_id, extract))





@router.post("/stream-response")
async def stream_response(user_input: UserInput):
    """
    Streams the response from the agent to the user.
    """
    message = user_input.message

    agent = Agent(
        name="Joker",
        instructions="You are a joker.",
        model="gpt-4o-mini",
    )
    
    result = Runner.run_streamed(
        agent,
        input="tell me a sotry of 5 sentences",
    )

    async def event_stream():
        full_output = ""

        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                chunk = event.data.delta
                full_output += chunk
                # print(chunk, end="", flush=True)
                yield json.dumps({ "delta": chunk }) + "\n"
                await asyncio.sleep(0.1)  # Optional: pacing
            elif event.type == "run_item_stream_event":
                if event.item.type == "message_output_item":
                    for chunk in event.item.raw_item.content:
                        if hasattr(chunk, "text"):
                            # print(chunk.text)
                            yield chunk.text
            
            
            # elif event.item.type == "tool_call_item":
            #     # print("-- Tool was called")
            #     continue
            
            # elif event.item.type == "tool_call_output_item":
            #     # print(f"-- Tool output: {event.item.output}")
            #     continue
                
            # elif event.item.type == "message_output_item":
            #     # print(f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
            #     continue
                
            # else:
            #     pass  # Ignore other event types

    return StreamingResponse(event_stream(), media_type="text/plain")
        


