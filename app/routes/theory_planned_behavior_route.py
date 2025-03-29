from app.auth import verify_token
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.psychology.theory_planned_behavior import TPBClassification, TheoryPlannedBehaviorService

router = APIRouter()

class TPBRequest(BaseModel):
    message: str

@router.post("/analyze", response_model=TPBClassification)
async def analyze_behavior(request: TPBRequest, user_id: str = Depends(verify_token)) -> TPBClassification:
    """
    Analyze a user's message using the Theory of Planned Behavior framework.
    
    Args:
        request (TPBRequest): The request containing the message to analyze
        user_id (str): The authenticated user's ID
        
    Returns:
        TPBClassification: The analysis result containing:
            - confidence_score: float
            - attitude: Attitude (evaluation and beliefs)
            - subjective_norms: SubjectiveNorms (social influences and pressure)
            - perceived_behavioral_control: PerceivedBehavioralControl (self-efficacy and facilitators)
            - behavioral_intention: str
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        service = TheoryPlannedBehaviorService(user_id=user_id)
        result = await service.classify_behavior(request.message)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze behavior using TPB framework"
            )
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during TPB analysis: {str(e)}"
        )
