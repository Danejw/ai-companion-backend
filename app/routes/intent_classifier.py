from app.auth import verify_token
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.psychology.intent_classification import IntentClassification, IntentClassificationService

router = APIRouter()

class IntentRequest(BaseModel):
    message: str

@router.post("/classify", response_model=IntentClassification)
async def classify_intent(request: IntentRequest, user_id: str = Depends(verify_token)) -> IntentClassification:
    """
    Classify the intent of a user's message.
    
    Args:
        request (IntentRequest): The request containing the message to classify
        user_id (str): The authenticated user's ID
        
    Returns:
        IntentClassification: The classification result containing confidence score, intent, and clarifying question
        
    Raises:
        HTTPException: If classification fails
    """
    try:
        service = IntentClassificationService(user_id)
        result = await service.classify_intent(request.message)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to classify intent"
            )
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during intent classification: {str(e)}"
        )
