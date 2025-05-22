from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.supabase.google_oauth import sign_in_with_google_id_token

router = APIRouter()


class GoogleAuthRequest(BaseModel):
    id_token: str


@router.post("/google")
def google_login(payload: GoogleAuthRequest):
    """Sign in or sign up a user with a Google ID token via Supabase."""
    try:
        session = sign_in_with_google_id_token(payload.id_token)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
