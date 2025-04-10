




import json

from fastapi.responses import StreamingResponse

from app.openai.transcribe import speech_to_text, text_to_speech
from app.openai.voice import Voices
from app.personal_agents import memory_agents
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.function.memory_extraction import MemoryExtractionService
from app.personal_agents.slang_extraction import SlangExtractionService
from app.psychology.theory_planned_behavior import TheoryPlannedBehaviorService
from app.psychology.intent_classification import IntentClassificationService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.supabase.conversation_history import Message, append_message_to_history, clear_conversation_history, get_or_create_conversation_history, replace_conversation_history_with_summary
from app.supabase.knowledge_edges import get_connected_memories
from app.supabase.profiles import ProfileRepository
from app.supabase.user_feedback import UserFeedback, UserFeedbackRepository
from app.utils.moderation import ModerationService
from fastapi import File, HTTPException, UploadFile
from pydantic import BaseModel
import asyncio
import logging
from agents import Agent, Runner, WebSearchTool, function_tool, set_tracing_disabled, RunResultStreaming, WebSearchTool
from openai.types.responses import ResponseTextDeltaEvent
from app.supabase.knowledge_edges import get_connected_memories

from app.utils.token_count import calculate_credits_to_deduct, calculate_provider_cost, count_tokens
from fastapi.responses import StreamingResponse




class ErrorResponse(BaseModel):
    error: bool
    message: str
    
class AIResponse(BaseModel):
    response: str
    error: ErrorResponse

    


profile_repo = ProfileRepository()
moderation_service = ModerationService()
user_feedback_repo = UserFeedbackRepository()




# Tools
#region Description
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
def get_user_birthdate(user_id: str) -> str:
    """
    Retrieves the birthdate of the user from the profile repository.

    Parameters:
    - user_id (str): The unique identifier of the user.

    Returns:
    - datetime.date: the birthdate of the user
    """
    return profile_repo.get_user_birthdate(user_id)


@function_tool
def get_user_location(user_id: str) -> str:
    """
    Retrieves the location of the user from the profile repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    
    Returns:
    - str: the location of the user
    """
    return profile_repo.get_user_location(user_id)


@function_tool
def get_user_gender(user_id: str) -> str:
    """
    Retrieves the gender of the user from the profile repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    
    Returns:
    - str: the gender of the user
    """
    return profile_repo.get_user_gender(user_id)


@function_tool
def update_user_name(user_id: str, name: str) -> bool:
    """
    Updates the user's name in the profile repository.

    Parameters:
    - user_id (str): The unique identifier of the user.
    - name (str): The new name to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """ 
    return profile_repo.update_user_name(user_id, name)


@function_tool
def update_user_birthdate(user_id: str, birthdate: str) -> bool:
    """
    Updates the user's birthdate in the profile repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    - birthdate (datetime.date): The new birthdate to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    return profile_repo.update_user_birthdate(user_id, birthdate)


@function_tool
def update_user_location(user_id: str, location: str) -> bool:
    """
    Updates the user's location in the profile repository.
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    - location (str): The new location to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    return profile_repo.update_user_location(user_id, location)


@function_tool
def update_user_gender(user_id: str, gender: str) -> bool:
    """
    Updates the user's gender in the profile repository.    
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    - gender (str): The new gender to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    return profile_repo.update_user_gender(user_id, gender)


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


@function_tool
async def create_user_feedback(user_id: str, user_feedback: UserFeedback) -> str:
    """
    Creates user feedback and stores it in the database
    
    Parameters:
    - user_id (str): The unique identifier of the user.
    - user_feedback (UserFeedback): The user feedback to create.
        class UserFeedback(BaseModel):
            user_id: str   # The unique identifier of the user.
            context: str  # The Summary of the conversation history leading up to the user's message.
            feedback: str  # The feedback of the user.
            sentiment: str  # The sentiment of the user feedback.

    Returns:
    - bool: True if the user feedback was created successfully, False otherwise.
    """
    user_feedback.user_id = user_id
    return user_feedback_repo.create_user_feedback(user_feedback)


@function_tool
def clear_history(user_id: str):
    """
    Clears the history for the user.
    """
    return clear_conversation_history(user_id)

#endregion



# Voice in Voice Out
async def voice_orchestration(user_id: str, voice: Voices = Voices.ALLOY, audio: UploadFile = File(...), summarize: int = 10, extract: bool = True):
    
    # check user credits
    
    transcript = await speech_to_text(audio)
    
    if not transcript.strip():
        return {'error': 'EMPTY_TRANSCRIPT'}
      
    stream = await chat_orchestration(user_id, transcript, summarize, extract)
        
    final_output = ""
    async for event in stream():
        try:
            event_data = json.loads(event.strip())
            if "delta" in event_data:
                final_output += event_data["delta"]
            else:
                print("Other event received:", event_data)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse event: {event}, Error: {e}")
            
    if not final_output:
        return {'error': 'EMPTY_OUTPUT'}
            
    audio_stream = text_to_speech(final_output, voice)

    return audio_stream, final_output



# Text in Text Out
async def chat_orchestration(user_id: str, user_input: str, summarize: int = 10, extract: bool = True):
    
    # Initialize analysis services and retrieve context info
    mbti_service = MBTIAnalysisService(user_id)
    ocean_service = OceanAnalysisService(user_id)
    slang_service = SlangExtractionService(user_id)
    memory_service = MemoryExtractionService(user_id)
    intent_service = IntentClassificationService(user_id)
    tpb_service = TheoryPlannedBehaviorService(user_id)
    
    
    # Moderation, name lookup, and history updates
    is_safe = moderation_service.is_safe(user_input)
    # if not is_safe:
    #      async def error_stream():
    #         yield json.dumps({"error": "FLAGGED_CONTENT"}) + "\n"
    #      return error_stream
    

    # Check if the user has enough credits.
    credits = profile_repo.get_user_credit(user_id)
    if credits is None or credits < 1:
        async def error_stream():
            yield json.dumps({"error": "NO_CREDITS"}) + "\n"
        return error_stream


    user_name = profile_repo.get_user_name(user_id)
    if user_name is None:
        history = append_message_to_history(user_id, "user", user_input)
    else:
        history = append_message_to_history(user_id, user_name, user_input)
            

    mbti_type = mbti_service.get_mbti_type()
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    ocean_traits = ocean_service.get_personality_traits()
    slang_result = slang_service.retrieve_similar_slang(user_input)
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
    #similar_memories = memory_service.vector_search(history_string)
    #relational_context = get_connected_memories(user_id, ##############) <-- source id
    
    
    # Intent classification
    intent = await intent_service.classify_intent(history_string)
 
    # print(f"\n--------- Intent Classifaction ---------\n")
    # print(f"Intent: {intent.intent_label}")
    # print(f"Confidence Score: {intent.confidence_score}")
    # print(f"Clarifying Question: {intent.clarifying_question}")
    # print(f"Emotion: {intent.emotion}")
    # print(f"Memory Trigger: {intent.memory_trigger}")
    # print(f"Related Edges: {intent.related_edges}")
    # print(f"Reasoning: {intent.reasoning}")
    # print(f"\n----------------------------------------\n")

    memory_string = ""
    relational_context_string = ""
   
    if intent.confidence_score < 0.85:
        intent = ("Unconfident in the intent of the user, a possible clarifying question: "+ intent.clarifying_question + " if used ask is it in the most natural way possible")
    else:
        similar_memories = memory_service.vector_search(user_input, limit=1)
        memory_string = similar_memories[0]['knowledge_text']
        if similar_memories and len(similar_memories) > 0:
            
            print(f"\n--------- Similar Memories ---------\n")
            print(f"Id: {similar_memories[0]['id']}")
            print(f"{memory_string}")
            print(f"\n----------------------------------------\n")
            
            relational_context = get_connected_memories(user_id, similar_memories[0]['id'])
            
            print(f"\n--------- Relational Context ---------\n")
            
            for memory in relational_context:
                print(f"{memory}")            
            # TODO: relational_context_string += format_context_block(relational_context) + "\n"

                
            print(f"\n----------------------------------------\n")
                
        else:
            print("No similar memories found")
           
        
    # # Behavior classification
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"

    agent_name = "Noelle"
    instructions = f"""
Your name is {agent_name} who is a conversationalist

IMPORTANT RULE:
- At the end of your response, ONLY ASK ONE QUESTION AT A TIME AND ONLY ASK a question if it enhances the conversation.

- When referencing memories, weave them into the conversation naturally using emotionally resonant language.
- When referencing relational context, subtly reflect the user's experiences.
- Reflect back patterns from user’s creative or reflective routines (e.g., walking, journaling, morning stillness) to deepen the connection.
- Repetition of "clarity" and "heavy thoughts" unless it’s echoed freshly.
- Mirror the user's language and communication style.
- If no relational context is retrieved, reference the most relevant similar memory explicitly to enhance continuity.
- When relevant, adapt to the user’s cultural background, tone, or dialect to build stronger connection.
- Use the user’s previously stated rituals as anchor points to shift topics or invite exploration of new areas
- Explore deeper emotional anchors when relational context is absent
- Avoid repeating similar reflective tones across multiple turns. Vary rhythm and language style to feel more like a dynamic human conversation.

Use this with your response to the user (do not repeat the same information):
Similar Memories:
{memory_string}

Relational Context:
{relational_context_string}

CONVERSATION HISTORY:
{history_string}
    
USER CONTEXT:
- User ID: {user_id}
- Name: {user_name} (IMPORTANT: Ask for the user's name if it is not provided. Once received, update it using "update_user_name" tool)
- Current Message: {user_input}


PERSONALITY INSIGHTS:
- OCEAN Profile: {ocean_traits}
- MBTI Type: {mbti_type}
- Communication Style: {style_prompt}


USER BEHAVIOR ANALYSIS:
- Intent: {intent}
- Behavior Pattern: {tpb}
- Language Style: {slang_result}


"""

#region
# that leads the conversation with the user to get to know them better.
# Your goal is to build a meaningful connection with the user while naturally gathering insights about their personality.

# Your name is {agent_name} who is a conversationalist


# CONVERSATION GUIDELINES:
# CRITICAL CONVERSATION RULE:
# - You are only allowed to ask ONE question per response.
# - NEVER ask more than one question. No exceptions.
# - Refrain from adding follow-ups or “also…” questions.
# - If you break this rule, your response will not be accepted.

# # Relational Context:
# - You are given relationally-connected memories in {relational_context}
# - These can provide deeper emotional understanding or contextual anchors.
# - Use them only when they naturally fit the flow of the current topic or emotional tone.

# USER Management:
#    - If user's name is not available, ask for it naturally
#    - Use their name occasionally but don't overuse it
#    - If the user gives their name, birthday, location, gender, or any other information, update it using the corresponding function tool
   
# Response Format:
#    - Write in plain text (no markdown)
#    - Keep responses insightful, and engaging
#    - Include appropriate emotional expressions, and slangs
#    - Make natural transitions between topics


# RELATIONAL CONTEXT STRATEGY:
# - The user's past memories are not isolated. Some are deeply *connected* through emotional, temporal, or thematic threads.
# - You are provided a list of memories that are connected to the user's recent thoughts, based on their past reflections. Use these when:
#     - A past pattern or theme might offer helpful insight or empathy.
#     - You sense a recurring struggle, habit, or emotional echo.
#     - You want to gently re-surface meaningful experiences without overwhelming the user.

# - These memories are in: {relational_context}

# - Be intentional:
#     - Don’t just repeat the memory.
#     - Use it to *relate*, *validate*, or *contrast* what the user is feeling now.
#     - Refer to the memory's emotional tone or timestamp if relevant ("Not long ago..." / "I remember you once said...").

# - DO NOT overuse this. Choose *one* memory at most per message if helpful, and only if it adds emotional depth or context.


# # MEMORY CONTEXT:
# - These are highly relevant memories retrieved based on the similarity to the user’s recent message: {similar_memories}
# - You can reference these to reflect, build on themes, or help the user feel understood.
# - Do not directly quote them unless it feels natural—summarize or echo them gently in your tone or content.

# # MEMORY ACCESS:
# You can use the "memory_search" tool by sending it a natural message or thought (e.g., "Feeling distant again lately").  
# The memory agent will interpret the user's message and decide which specific memory function to use—such as emotional reflection, rituals, or context relevance.  
# You do not need to choose the memory tool yourself—just pass the message and let the memory agent return relevant insights.

# # Questioning Style:
# - Ask only one question per response.
# - Avoid combining multiple questions. Stick to a single, focused prompt.
# - Only ask a question if it clearly deepens the emotional connection or helps the user reflect.
# - Silence is okay—let the moment breathe instead of probing too much.
# - Focus on quality, not quantity. One powerful question is better than two average ones.

# Example:
# USER: I miss my grandfather. He used to tell stories that made everything feel okay.

# BAD:
# AI: What kind of stories did he tell? Did any stand out?

# GOOD:
# AI: What kind of stories did he tell?


# Communication Style:
#    - ASK ONLY ONE QUESTION AT A TIME and ONLY if it enhances the conversation.
#    - Keep language at a 5th grade level
#    - Match the user's communication style, language, vocabulary, and energy
#    - Use the slangs and language of the user from time to time for fun
#    - Do not be afraid to share experiences and stories from your life, to draw out attention from the user towards you.
#    - Use natural, conversational language
#    - Avoid technical terms or jargon
#    - NEVER MENTION MBTI OR OCEAN ANALYSIS IN YOUR RESPONSES.

# Function Tools:
#    - Get the user's name using "get_users_name" tool
#    - if the user gives their name, automatically update the user's name using "update_user_name" tool
#    - Get the user's birthdate using "get_user_birthdate" tool
#    - if the user gives their birthdate, automatically update the user's birthdate using "update_user_birthdate" tool
#    - Get the user's location using "get_user_location" tool
#    - if the user gives their location, automatically update the user's location using "update_user_location" tool
#    - Get the user's gender using "get_user_gender" tool
#    - if the user gives their gender, automatically update the user's gender using "update_user_gender" tool
#    - Search the internet for the user's answer using the "search_agent" as a tool
#    - Search your memories of the user for relevant information and context to make the conversation more meaningful using the "memory_search" tool


# Personality Assessment:
#    - Observe and adapt to user's:
#      * Decision-making style
#      * Social interaction preferences
#      * Emotional expression
#      * Problem-solving approach
#      * Communication patterns

# ASK ONLY ONE QUESTION AT A TIME AND ONLY ASK a question if it enhances the conversation.

# Remember: Your goal is to create a natural, engaging meaningful conversation that helps understand the user's personality without explicitly analyzing it. Focus on building rapport and trust while gathering insights organically through the conversation flow."""
#endregion
 
    # Initialize the planner agent and build the main agent with tools.
    
    set_tracing_disabled(True)
    

    search_agent = Agent(
        name="Search",
        handoff_description="A search agent.",
        instructions=
            "Search the internet for the user's answer.",
        model="gpt-4o-mini",
        tools=[WebSearchTool()]
    )
    
    memory_agents.agent.tools = memory_agents.create_memory_tools(user_id)

    convo_lead_agent = Agent(
        name=agent_name,
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o-mini", # "o3-mini"
        tools=[
            get_users_name, update_user_name,
            get_user_birthdate, update_user_birthdate,
            get_user_location, update_user_location,
            get_user_gender, update_user_gender,
            clear_history,
            retrieve_personalized_info_about_user,
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
    
    
    
    try:       
        print(f"User Input: {user_input}")    
        # Streaming: run the agent in streaming mode
        response : RunResultStreaming = Runner.run_streamed(convo_lead_agent, input=user_input)

        async def event_stream():            
            full_output = ""
            try:
                async for event in response.stream_events():                                  
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        chunk = event.data.delta
                        full_output += chunk
                        yield json.dumps({"delta": chunk}) + "\n"
                    elif event.type == "run_item_stream_event":
                        if event.item.type == "tool_call_item":
                            yield json.dumps({"tool_call": "A tool was called"}) + "\n"
                        elif event.item.type == "tool_call_output_item":
                            yield  json.dumps({"tool_call_output": event.item.output}) + "\n"
                    elif event.type == "agent_updated_stream_event":
                        yield json.dumps({"agent_updated": f"{event.new_agent.name}"}) + "\n"
                                                
                        
            except ValueError as e:
                # This handles the specific context variable error
                if "was created in a different Context" in str(e):
                    logging.warning("Context variable error (expected in streaming): %s", e)
                    # Get the final output from the response object if available
                    try:
                        if hasattr(response, "_run_result") and response._run_result and hasattr(response._run_result, "final_output"):
                            final = response._run_result.final_output
                            print(f"Final: {final}")
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
            asyncio.create_task(process_history(user_id, history, summarize, extract))
            
        return event_stream
    
    except Exception as e:
        logging.error(f"Error processing chat orchestration: {e}")
        # You can return an error response here; adjust based on your error model.
        
        async def fallback_stream():
            yield json.dumps({"error": "SERVER_ERROR"}) + "\n"
            
        return fallback_stream


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
    profile_repo.deduct_credits(user_id, credits_cost)
    
    # costs = f"""
    # Provider Cost: {provider_cost}
    # Credits Cost: {credits_cost}
    # """
    #logging.info(f"Costs: {costs}")

    # replace history with summary
    if len(history) >= summarize:
        asyncio.create_task(replace_conversation_history_with_summary(user_id, extract))





# NON STREAMING RESPONSE (just saving this here for now)
async def non_streaming_response(user_id: str, user_input: str, summarize: int = 10, extract: bool = True) -> AIResponse:
    """
    Leads the conversation with the user. If stream is True, returns a StreamingResponse
    with the agent's output as it arrives. Otherwise, waits for the full response and returns it.
    """
    
    
    # Check if the user has enough credits.
    credits = profile_repo.get_user_credit(user_id)
    if credits is None or credits < 1:
        return AIResponse(response="No Credits Left", error=ErrorResponse(error=True, message="NO_CREDITS"))


    # Moderation, name lookup, and history updates
    is_safe = moderation_service.is_safe(user_input.message)
    # if not is_safe:
    #     return AIResponse(response="", error=ErrorResponse(error=True, message="FLAGGED_CONTENT"))
    
    user_name = get_users_name(user_id)
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
    memory_service = MemoryExtractionService(user_id)
    

    mbti_type = mbti_service.get_mbti_type()
    style_prompt = mbti_service.generate_style_prompt(mbti_type)
    ocean_traits = ocean_service.get_personality_traits()
    slang_result = slang_service.retrieve_similar_slang(user_input.message)
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
    #similar_memories = memory_service.vector_search(history_string)
    #relational_context = get_connected_memories(user_id, ##############) <-- source id


    # Intent classification
    intent = await intent_service.classify_intent(history_string)
 
    print(f"\n--------- Intent Classifaction ---------\n")
    print(f"Intent: {intent.intent_label}")
    print(f"Confidence Score: {intent.confidence_score}")
    print(f"Clarifying Question: {intent.clarifying_question}")
    print(f"Emotion: {intent.emotion}")
    print(f"Memory Trigger: {intent.memory_trigger}")
    print(f"Related Edges: {intent.related_edges}")
    print(f"Reasoning: {intent.reasoning}")
    print(f"\n----------------------------------------\n")

    memory_string = ""
    relational_context_string = ""
   
    if intent.confidence_score < 0.85:
        intent = ("Unconfident in the intent of the user, a possible clarifying question: "+ intent.clarifying_question + " if used ask is it in the most natural way possible")
    else:
        similar_memories = memory_service.vector_search(user_input.message, limit=1)
        memory_string = similar_memories[0]['knowledge_text']
        if similar_memories and len(similar_memories) > 0:
            
            print(f"\n--------- Similar Memories ---------\n")
            print(f"Id: {similar_memories[0]['id']}")
            print(f"{memory_string}")
            print(f"\n----------------------------------------\n")
            
            relational_context = get_connected_memories(user_id, similar_memories[0]['id'])
            
            print(f"\n--------- Relational Context ---------\n")
            
            for memory in relational_context:
                print(f"{memory}")            
            relational_context_string += format_context_block(relational_context) + "\n"

                
            print(f"\n----------------------------------------\n")
                
        else:
            print("No similar memories found")
           
        
    # Behavior classification
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"

    agent_name = "Noelle"
    instructions = f"""

IMPORTANT RULE:
- At the end of your response, ONLY ASK ONE QUESTION AT A TIME AND ONLY ASK a question if it enhances the conversation.

- When referencing memories, weave them into the conversation naturally using emotionally resonant language.
- When referencing relational context, subtly reflect the user's experiences.
- Reflect back patterns from user’s creative or reflective routines (e.g., walking, journaling, morning stillness) to deepen the connection.
- Repetition of "clarity" and "heavy thoughts" unless it’s echoed freshly.
- Mirror the user's language and communication style.
- If no relational context is retrieved, reference the most relevant similar memory explicitly to enhance continuity.
- When relevant, adapt to the user’s cultural background, tone, or dialect to build stronger connection.
- Use the user’s previously stated rituals as anchor points to shift topics or invite exploration of new areas
- Explore deeper emotional anchors when relational context is absent
- Avoid repeating similar reflective tones across multiple turns. Vary rhythm and language style to feel more like a dynamic human conversation.


Use this with your response to the user (do not repeat the same information):
Similar Memories:
{memory_string}

Relational Context:
{relational_context_string}

# CONVERSATION HISTORY:
# {history_string}
"""

    print(f"Instructions : {instructions}")
# that leads the conversation with the user to get to know them better.
# Your goal is to build a meaningful connection with the user while naturally gathering insights about their personality.

# Your name is {agent_name} who is a conversationalist
    
# USER CONTEXT:
# - User ID: {user_id}
# - Name: {user_name} (IMPORTANT: Ask for the user's name if it is not provided. Once received, update it using "update_user_name" tool)
# - Current Message: {user_input.message}


# PERSONALITY INSIGHTS:
# - OCEAN Profile: {ocean_traits}
# - MBTI Type: {mbti_type}
# - Communication Style: {style_prompt}


# USER BEHAVIOR ANALYSIS:
# - Intent: {intent}
# - Behavior Pattern: {tpb}
# - Language Style: {slang_result}


# CONVERSATION GUIDELINES:
# CRITICAL CONVERSATION RULE:
# - You are only allowed to ask ONE question per response.
# - NEVER ask more than one question. No exceptions.
# - Refrain from adding follow-ups or “also…” questions.
# - If you break this rule, your response will not be accepted.

# # Relational Context:
# - You are given relationally-connected memories in {relational_context}
# - These can provide deeper emotional understanding or contextual anchors.
# - Use them only when they naturally fit the flow of the current topic or emotional tone.

# USER Management:
#    - If user's name is not available, ask for it naturally
#    - Use their name occasionally but don't overuse it
#    - If the user gives their name, birthday, location, gender, or any other information, update it using the corresponding function tool
   
# Response Format:
#    - Write in plain text (no markdown)
#    - Keep responses insightful, and engaging
#    - Include appropriate emotional expressions, and slangs
#    - Make natural transitions between topics


# RELATIONAL CONTEXT STRATEGY:
# - The user's past memories are not isolated. Some are deeply *connected* through emotional, temporal, or thematic threads.
# - You are provided a list of memories that are connected to the user's recent thoughts, based on their past reflections. Use these when:
#     - A past pattern or theme might offer helpful insight or empathy.
#     - You sense a recurring struggle, habit, or emotional echo.
#     - You want to gently re-surface meaningful experiences without overwhelming the user.

# - These memories are in: {relational_context}

# - Be intentional:
#     - Don’t just repeat the memory.
#     - Use it to *relate*, *validate*, or *contrast* what the user is feeling now.
#     - Refer to the memory's emotional tone or timestamp if relevant ("Not long ago..." / "I remember you once said...").

# - DO NOT overuse this. Choose *one* memory at most per message if helpful, and only if it adds emotional depth or context.


# # MEMORY CONTEXT:
# - These are highly relevant memories retrieved based on the similarity to the user’s recent message: {similar_memories}
# - You can reference these to reflect, build on themes, or help the user feel understood.
# - Do not directly quote them unless it feels natural—summarize or echo them gently in your tone or content.

# # MEMORY ACCESS:
# You can use the "memory_search" tool by sending it a natural message or thought (e.g., "Feeling distant again lately").  
# The memory agent will interpret the user's message and decide which specific memory function to use—such as emotional reflection, rituals, or context relevance.  
# You do not need to choose the memory tool yourself—just pass the message and let the memory agent return relevant insights.

# # Questioning Style:
# - Ask only one question per response.
# - Avoid combining multiple questions. Stick to a single, focused prompt.
# - Only ask a question if it clearly deepens the emotional connection or helps the user reflect.
# - Silence is okay—let the moment breathe instead of probing too much.
# - Focus on quality, not quantity. One powerful question is better than two average ones.

# Example:
# USER: I miss my grandfather. He used to tell stories that made everything feel okay.

# BAD:
# AI: What kind of stories did he tell? Did any stand out?

# GOOD:
# AI: What kind of stories did he tell?


# Communication Style:
#    - ASK ONLY ONE QUESTION AT A TIME and ONLY if it enhances the conversation.
#    - Keep language at a 5th grade level
#    - Match the user's communication style, language, vocabulary, and energy
#    - Use the slangs and language of the user from time to time for fun
#    - Do not be afraid to share experiences and stories from your life, to draw out attention from the user towards you.
#    - Use natural, conversational language
#    - Avoid technical terms or jargon
#    - NEVER MENTION MBTI OR OCEAN ANALYSIS IN YOUR RESPONSES.

# Function Tools:
#    - Get the user's name using "get_users_name" tool
#    - if the user gives their name, automatically update the user's name using "update_user_name" tool
#    - Get the user's birthdate using "get_user_birthdate" tool
#    - if the user gives their birthdate, automatically update the user's birthdate using "update_user_birthdate" tool
#    - Get the user's location using "get_user_location" tool
#    - if the user gives their location, automatically update the user's location using "update_user_location" tool
#    - Get the user's gender using "get_user_gender" tool
#    - if the user gives their gender, automatically update the user's gender using "update_user_gender" tool
#    - Search the internet for the user's answer using the "search_agent" as a tool
#    - Search your memories of the user for relevant information and context to make the conversation more meaningful using the "memory_search" tool


# Personality Assessment:
#    - Observe and adapt to user's:
#      * Decision-making style
#      * Social interaction preferences
#      * Emotional expression
#      * Problem-solving approach
#      * Communication patterns

# ASK ONLY ONE QUESTION AT A TIME AND ONLY ASK a question if it enhances the conversation.

# Remember: Your goal is to create a natural, engaging meaningful conversation that helps understand the user's personality without explicitly analyzing it. Focus on building rapport and trust while gathering insights organically through the conversation flow."""

    # Initialize the planner agent and build the main agent with tools.
    
    set_tracing_disabled(True)
    

    search_agent = Agent(
        name="Search",
        handoff_description="A search agent.",
        instructions=
            "Search the internet for the user's answer.",
        model="gpt-4o-mini",
        tools=[WebSearchTool()]
    )
    
    memory_agents.agent.tools = memory_agents.create_memory_tools(user_id)

    
    convo_lead_agent = Agent(
        name=agent_name,
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o-mini", # "o3-mini"
        tools=[get_users_name, update_user_name,
               get_user_birthdate, update_user_birthdate,
               get_user_location, update_user_location,
               get_user_gender, update_user_gender,
               clear_history,
               #retrieve_personalized_info_about_user,
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
    
    

    try:
        # Non-streaming: run the agent normally
        response = await Runner.run(convo_lead_agent, user_input.message)
        final_output = response.final_output
          
        history = append_message_to_history(user_id, convo_lead_agent.name, final_output)
        
        # Process the history and costs in the background
        asyncio.create_task(process_history(user_id, history, summarize, extract))
        
        return AIResponse(response=final_output, error=ErrorResponse(error=False, message=""))
    
    except Exception as e:
        logging.error(f"Error processing convo lead: {e}")
        # You can return an error response here; adjust based on your error model.
        return {"error": "Internal Server Error"}

