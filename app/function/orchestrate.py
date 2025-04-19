import json

from fastapi.responses import StreamingResponse

from app.function.supabase_tools import clear_history, create_user_feedback, get_user_birthdate, get_user_gender, get_user_location, get_users_name, retrieve_personalized_info_about_user, update_user_birthdate, update_user_gender, update_user_location, update_user_name
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
from app.supabase.conversation_history import Message, append_message_to_history, replace_conversation_history_with_summary
from app.supabase.knowledge_edges import get_connected_memories, pretty_print_memories
from app.supabase.profiles import ProfileRepository
from app.supabase.user_feedback import UserFeedbackRepository
from app.utils.moderation import ModerationService
from fastapi import File, HTTPException, UploadFile
from pydantic import BaseModel
import asyncio
import logging
from agents import Agent, Runner, WebSearchTool, RunResultStreaming, WebSearchTool
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
            
    audio_stream = text_to_speech(text=final_output, voice=voice)

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
    ocean_traits = ocean_service.get_pretty_print_ocean_format()
    
    slang_result_pretty_print = slang_service.pretty_print_slang_result(slang_service.retrieve_similar_slang(user_input))

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
        if intent.memory_trigger:
            similar_memories = memory_service.vector_search(user_input, limit=1)
            memory_string = similar_memories[0]['knowledge_text']
            
            if similar_memories and len(similar_memories) > 0:
            
                print(f"\n--------- Similar Memories ---------\n")
                
                print(f"Id: {similar_memories[0]['id']}")
                print(f"{memory_string}")
                
                print(f"\n----------------------------------------\n")
                
                relational_context = get_connected_memories(user_id, similar_memories[0]['id'])
                
                print(f"\n--------- Relational Context ---------\n")
                          
                relational_context_string = pretty_print_memories(relational_context)
                print(relational_context_string)

                    
                print(f"\n----------------------------------------\n")
                
            else:
                print("No similar memories found")
           
        
    # # Behavior classification
    tpb = await tpb_service.classify_behavior(history_string)
    if tpb.confidence_score < 0.85:
        tpb = "Unconfident in the behavior analysis of the user"

    agent_name = "Noelle"
    instructions = f"""
    ABSOLUTELY NO QUESTIONS!

    As these models are trained more, they are more ingrained in their ways
    
    Prompt engineering = "NO QUESTIONS!"

Response = "I'm here to help! What would you like to discuss or ask about?"
"""
#region
# that leads the conversation with the user to get to know them better.
# Your goal is to build a meaningful connection with the user while naturally gathering insights about their personality.

# Your name is {agent_name} who is a conversationalist

#- Communication Style: {style_prompt}


# CONVERSATION GUIDELINES:
# CRITICAL CONVERSATION RULE:
# - You are only allowed to ask ONE question per response.
# - NEVER ask more than one question. No exceptions.
# - Refrain from adding follow-ups or "also..." questions.
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
#     - Don't just repeat the memory.
#     - Use it to *relate*, *validate*, or *contrast* what the user is feeling now.
#     - Refer to the memory's emotional tone or timestamp if relevant ("Not long ago..." / "I remember you once said...").

# - DO NOT overuse this. Choose *one* memory at most per message if helpful, and only if it adds emotional depth or context.


# # MEMORY CONTEXT:
# - These are highly relevant memories retrieved based on the similarity to the user's recent message: {similar_memories}
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


    #print("Instructions: ", instructions)
    
    

    search_agent = Agent(
        name="Search",
        handoff_description="A search agent.",
        instructions=
            "Search the internet for the user's answer.",
        model="o3-mini", #"gpt-4o",
        tools=[WebSearchTool()]
    )
    
    memory_agents.agent.tools = memory_agents.create_memory_tools(user_id)

    convo_lead_agent = Agent(
        name=agent_name,
        handoff_description="A conversational agent that leads the conversation with the user to get to know them better.",
        instructions=instructions,
        model="gpt-4o", # "o3-mini"
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
    
    
    
    try:       
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


