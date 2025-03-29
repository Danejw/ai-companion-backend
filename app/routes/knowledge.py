from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import verify_token
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService


router = APIRouter()

class KnowledgeRequest(BaseModel):
    message: str

@router.post("/extract-knowledge")
def knowledge_extract(data: KnowledgeRequest, user=Depends(verify_token)):
    """
    Extracts knowledge from the given message and stores it if valuable.
    """
    user_id = user["id"]
    message = data.message
    
    # Instantiate the KnowledgeExtractionService
    knowledge_service = KnowledgeExtractionService(user_id)
    
    # Extract knowledge from the message
    knowledge_result = knowledge_service.extract_knowledge(message)
    
    if not knowledge_result:
        return {"message": "No valuable knowledge extracted."}

    return knowledge_result

@router.post("/retrieve-knowledge")
def retrieve_knowledge(query: KnowledgeRequest, user=Depends(verify_token)):
    """
    Retrieves stored knowledge relevant to the user's message.
    """
    user_id = user["id"]
    
    # Instantiate the KnowledgeExtractionService
    knowledge_service = KnowledgeExtractionService(user_id)

    # Find similar stored knowledge
    similar_knowledge = knowledge_service.retrieve_similar_knowledge(query.message, top_k=5)

    return {"similar_knowledge": similar_knowledge }