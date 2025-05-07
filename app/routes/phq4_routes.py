# phq4_routes.py
from fastapi import APIRouter, Depends
from app.auth import verify_token
from app.supabase.phq4 import Phq4Questionaire, Phq4Repository

router = APIRouter()

phq4 = Phq4Repository()

@router.post("/create_response")
def create_response(response: Phq4Questionaire, user_id=Depends(verify_token)):
    user_id = user_id["id"]
    response.user_id = user_id
    
    phq4.create_phq4(response)
    return response

@router.get("/get_responses")
def get_responses(user_id=Depends(verify_token)):
    user_id = user_id["id"]
    
    responses = phq4.get_phq4(user_id)
    return responses

