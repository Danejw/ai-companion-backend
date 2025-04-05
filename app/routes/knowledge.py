import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import verify_token
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.supabase.conversation_history import Message

router = APIRouter()

class KnowledgeRequest(BaseModel):
    history: list[Message]

@router.post("/extract-knowledge")
def knowledge_extract(data: KnowledgeRequest, user=Depends(verify_token)):
    """
    Extracts knowledge from the given message and stores it if valuable.
    """
    user_id = user["id"]
    history = data.history
    
    # Filter to get only messages from this user
    user_messages = [msg for msg in history if msg.user_id == user_id]
    
    # Convert the history to a string
    
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in user_messages])
    
    print("history_string", history_string)
    
    # Instantiate the KnowledgeExtractionService
    knowledge_service = KnowledgeExtractionService(user_id)
    
    # Extract knowledge from the message
    knowledge_result = knowledge_service.extract_knowledge(history_string)
    
    if not knowledge_result:
        return {"message": "No valuable knowledge extracted."}

    return knowledge_result

@router.post("/retrieve-knowledge")
def retrieve_knowledge(query: KnowledgeRequest, user=Depends(verify_token)):
    """
    Retrieves stored knowledge relevant to the user's message.
    """
    user_id = user["id"]
    
    # Convert the history to a string for similarity search
    history_string = query.model_dump()
    
    # Instantiate the KnowledgeExtractionService
    knowledge_service = KnowledgeExtractionService(user_id)

    # Find similar stored knowledge
    similar_knowledge = knowledge_service.retrieve_similar_knowledge(history_string, top_k=5)

    return {"similar_knowledge": similar_knowledge}