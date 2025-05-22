from fastapi import APIRouter, HTTPException, status
from typing import List

from fastapi.params import Depends
from app.auth import verify_token
from app.supabase.conversation_history import get_or_create_conversation_history, Message

# Initialize the router
router = APIRouter()

@router.get("/history", response_model=List[Message])
async def get_conversation_history_route(user_id=Depends(verify_token)):
    """
    Retrieves the full conversation history for a specific user.
    If no history exists, a new record is created (if configured) and an empty list is returned.
    
    Returns:
        List[Message]: A list of Message objects containing role, content, and timestamp
    """
    try:
        user_id = user_id["id"]
        history = get_or_create_conversation_history(user_id)
        # The function now returns list[Message] objects
        return history
    except Exception as e:
        # Catch any unexpected errors during the process
        # The underlying function already logs errors, but we raise an HTTP exception for the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving conversation history for user {user_id}: {str(e)}"
        )
