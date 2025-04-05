from app.supabase.supabase_mbti import MBTI
from fastapi import APIRouter, Request, Depends
from app.psychology.mbti_analysis import MBTIAnalysisService
from pydantic import BaseModel
from app.auth import verify_token
from app.supabase.conversation_history import Message

router = APIRouter()


class MBTIRequest(BaseModel):
    history: list[Message]
    
class MBTIUpdateRequest(BaseModel):
    extraversion_introversion: float
    sensing_intuition: float
    thinking_feeling: float
    judging_perceiving: float
    
class MBTIUpdateResponse(BaseModel):
    type: str
    extraversion_introversion: float
    sensing_intuition: float
    thinking_feeling: float
    judging_perceiving: float
    message_count: int
    
    
class MBTIAnalysisRequest(BaseModel):
    message: str
    
class MBTITypeRequest(BaseModel):
    user_id: str
    

@router.post("/mbti-analyze")
async def mbti_analyze(data: MBTIRequest, user=Depends(verify_token)):
    user_id =  user_id = user["id"] 
    
    # Filter to get only messages from this user
    user_messages = [msg for msg in data.history if msg.user_id == user_id]
    
    # Convert the history to a string
    history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in user_messages])
    
    # Create a new analysis service for this user
    service = MBTIAnalysisService(user_id)
    # Perform the analysis
    await service.analyze_message(history_string)

    # Get final MBTI type
    final_type = service.get_mbti_type()
    style_prompt = service.generate_style_prompt(final_type)

    return {
        "mbti_type": final_type,
        "style_prompt": style_prompt
    }


@router.get("/get-mbti")
async def get_mbti(user=Depends(verify_token)) -> MBTIUpdateResponse:
    user_id = user["id"] 
    service = MBTIAnalysisService(user_id)
    mbti_data = service.repository.get_mbti(user_id)
    
    mbti_response = MBTIUpdateResponse(
        type=service.get_mbti_type(),
        extraversion_introversion=mbti_data.extraversion_introversion, 
        sensing_intuition=mbti_data.sensing_intuition, 
        thinking_feeling=mbti_data.thinking_feeling, 
        judging_perceiving=mbti_data.judging_perceiving,
        message_count=mbti_data.message_count
    )

    if mbti_data:
        return mbti_response
    else:
        return {"error": "No MBTI data found for this user"}
    

@router.post("/mbti-update")
async def update_mbti(data: MBTIUpdateRequest, user=Depends(verify_token)):
    """
    Updates the MBTI data for a given user in Supabase,
    applying the rolling average before saving.
    """
    user_id =  user_id = user["id"] 

    # Initialize the MBTI Analysis Service
    service = MBTIAnalysisService(user_id)

    # Construct a new MBTI object with the incoming data
    new_mbti = MBTI(
        extraversion_introversion=data.extraversion_introversion,
        sensing_intuition=data.sensing_intuition,
        thinking_feeling=data.thinking_feeling,
        judging_perceiving=data.judging_perceiving,
        message_count=1  # This will be updated in the rolling average function
    )

    # Apply rolling average update
    service._update_mbti_rolling_average(new_mbti)

    # Save the updated MBTI data to Supabase
    service.save_mbti()

    return {
        "message": "MBTI data updated successfully",
        "mbti": service.mbti.dict()
    }
    

@router.get("/mbti-type")
async def get_mbti_type(user=Depends(verify_token)):
    user_id =  user_id = user["id"] 
    service = MBTIAnalysisService(user_id)
    mbti_type = service.get_mbti_type()
    return {"mbti_type": mbti_type}


