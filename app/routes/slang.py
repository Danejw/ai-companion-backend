from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import verify_token
from app.personal_agents.slang_extraction import SlangExtractionService
from app.supabase.conversation_history import Message
router = APIRouter()

class SlangRequest(BaseModel):
    history: list[Message]

@router.post("/extract-slang")
async def slang_extract(data: SlangRequest, user=Depends(verify_token)):
    """
    Extracts slang from the given message and stores it if valuable.
    """
    user_id = user["id"]
    
    # Filter to get only messages from this user
    user_messages = [msg for msg in data.history if msg.user_id == user_id]
    
    # Convert the history to a string
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in user_messages])
    
    # Instantiate the SlangExtractionService
    slang_service = SlangExtractionService(user_id)
    
    # Extract slang from the message
    slang_result = await slang_service.extract_slang(history_string)
    
    if not slang_result:
        return {"message": "No valuable slang extracted."}
    
    return slang_result

@router.post("/retrieve-slang")
def retrieve_slang(query: SlangRequest, user=Depends(verify_token)):
    """
    Retrieves stored slang relevant to the user's message.
    """
    user_id = user["id"]
    
    # Instantiate the SlangExtractionService
    slang_service = SlangExtractionService(user_id)
    
    # Convert the history to a string for similarity search
    history_string = query.model_dump()
    
    # Find similar stored slang
    similar_slang = slang_service.retrieve_similar_slang(history_string, top_k=5)
    
    return { "similar_slang": similar_slang }


