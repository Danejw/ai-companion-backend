import logging
from fastapi import APIRouter, HTTPException, status, Path
from typing import List

from fastapi.params import Depends
from app.auth import verify_token
from app.supabase.conversation_history import get_or_create_conversation_history

# Initialize the router
router = APIRouter()

@router.get("/{user_id}/history")
async def get_conversation_history_route(user_id_from_path: str = Path(..., title="The User ID from the URL path"), user_id=Depends(verify_token)):
    """
    Retrieves the full conversation history for a specific user.
    If no history exists, a new record is created (if configured) and an empty list is returned.
    """
    try:
        token_user_id = user_id.get("id")
        if not token_user_id or token_user_id != user_id_from_path:
            logging.warning(f"Authorization denied: Token user '{token_user_id}' tried to access history for path user '{user_id_from_path}'")
            raise HTTPException(
                 status_code=status.HTTP_FORBIDDEN,
                 detail="You do not have permission to access this resource."
             )

        # --- Use the ID from the path parameter for the database query ---
        logging.info(f"Fetching history for user ID from path: {user_id_from_path}")
        history = get_or_create_conversation_history(user_id_from_path) # <-- Pass the string ID

        return history
    except HTTPException as http_exc:
         raise http_exc # Re-raise specific HTTP exceptions
    except Exception as e:
        logging.error(f"Unexpected error retrieving history for user {user_id_from_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred." # Avoid leaking too much detail
        )
