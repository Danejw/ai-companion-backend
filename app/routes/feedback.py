





from agents import Agent, Runner
from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from app.auth import verify_token
from app.function.memory_extraction import MemoryExtractionService, MemoryMetadata
from app.supabase.conversation_history import get_or_create_conversation_history
from app.supabase.user_feedback import UserFeedback, UserFeedbackRepository



router = APIRouter()
user_feedback_repo = UserFeedbackRepository()

    
class FeedbackRequest(BaseModel):
    feedback: str

sentiment_agent = Agent(
        name="Sentiment",
        instructions="Analyze the sentiment of the user's message. return with a single word. Positive, Negative, or Neutral",
        model="gpt-4o-mini",
    )


@router.post("/create-user-feedback")
async def create_user_feedback(feedback: FeedbackRequest, user=Depends(verify_token)) -> bool:
    """
    Creates user feedback and stores it in the database
    """
    user_id = user["id"]
    
    sentiment = await Runner.run(sentiment_agent, feedback.feedback)
    history = get_or_create_conversation_history(user_id)
    summary = history[0].content
        
    user_feedback = UserFeedback(
        user_id=user_id,
        feedback=feedback.feedback,
        context=summary,
        sentiment=sentiment.final_output 
    )
    
    return user_feedback_repo.create_user_feedback(user_feedback)


@router.post("/store-feedback-memory")
async def store_feedback_memory(feedback: FeedbackRequest, user=Depends(verify_token)) -> bool:
    """
    Stores the feedback in the memory
    """
    user_id = user["id"]
    
    service = MemoryExtractionService(user_id)
    service.agent.output_type=MemoryMetadata
    sentiment = await Runner.run(service.agent, feedback.feedback)
    
    if "feedback" not in sentiment.final_output.topics:
        sentiment.final_output.topics.append("feedback")
    
    #print("Metadata Score: ", sentiment.final_output)
    service.store_memory(sentiment.final_output)
    return True

