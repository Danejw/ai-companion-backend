from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from app.auth import verify_token
from app.supabase.finetune_feedback import SimplifiedFeedbackPayload, build_feedback_payload, get_agent_metadata, submit_finetune_feedback

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(feedback: SimplifiedFeedbackPayload, user: str = Depends(verify_token)):
    try:
        user_id = user["id"]
        metadata = await get_agent_metadata(feedback)
        feedback_payload = await build_feedback_payload(feedback, metadata)
        response = submit_finetune_feedback(user_id=user_id, payload=feedback_payload)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
