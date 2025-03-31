from fastapi import APIRouter, HTTPException, status
from app.supabase.profiles import ProfileRepository
from app.auth import verify_token
from fastapi.params import Depends


# Initialize the router
router = APIRouter()


@router.get("/users/credits")
async def get_user_credits_route(user_id=Depends(verify_token)):
    """1
    Retrieves the credit balance for a specific user.
    """

    user_id = user_id["id"]
    repo = ProfileRepository()
    credits = repo.get_user_credit(user_id)
    if credits is None:
        # This could mean the user doesn't exist or an error occurred fetching credits
        # The repository logs specific errors, here we return a generic not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find credits for user with id {user_id}"
        )
    return {"user_id": user_id, "credits": credits}

