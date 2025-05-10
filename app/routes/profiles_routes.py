from fastapi import APIRouter, HTTPException, status
from app.supabase.profiles import ProfileRepository
from app.auth import verify_token
from fastapi.params import Depends
from pydantic import BaseModel

# Initialize the router
router = APIRouter()


class PasswordResetRequest(BaseModel):
    email: str
    
class UpdatePasswordRequest(BaseModel):
    new_password: str
    token: str


class UserPilotRequest(BaseModel):
    is_pilot: bool

@router.get("/credits")
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

@router.get("/credits_used")
async def get_user_credits_used_route(user_id=Depends(verify_token)):
    """1
    Retrieves the credit balance for a specific user.
    """

    user_id = user_id["id"]
    repo = ProfileRepository()
    credits_used = repo.get_user_credits_used(user_id)
    if credits_used is None:
        # This could mean the user doesn't exist or an error occurred fetching credits
        # The repository logs specific errors, here we return a generic not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find credits for user with id {user_id}"
        )
    return {"user_id": user_id, "credits_used": credits_used}


@router.get("/profile")
async def get_user_profile_route(user_id=Depends(verify_token)):
    """
    Retrieves the profile for a specific user.
    """
    user_id = user_id["id"]
    repo = ProfileRepository()
    profile = repo.get_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find profile for user with id {user_id}"
        )
    return profile

@router.delete("/delete_account")
async def delete_user_account_route(user_id=Depends(verify_token)):
    """
    Deletes the user account from the profile record in Supabase.
    """
    user_id = user_id["id"]
    repo = ProfileRepository()
    results = repo.complete_account_deletion(user_id)
    return results


@router.post("/send_password_reset")
async def send_password_reset_route(password_reset_request: PasswordResetRequest):
    """
    Sends a password reset email to the user.
    """
    repo = ProfileRepository()
    results = repo.send_password_reset(password_reset_request.email)
    return results

@router.post("/change_password")
async def update_password(request: UpdatePasswordRequest):
    """
    Updates a user's password.
    
    This endpoint can be used in two scenarios:
    1. After password reset (using token)
    2. When user is logged in and wants to change password
    
    Request body should contain:
    - new_password: The new password to set
    - Either user_id or token depending on the scenario
    """
    try:
        profile_repo = ProfileRepository()
        
        # Check if this is a reset flow (with token) or regular update
        if request.token:
            # For password reset flow, exchange token for user ID
            auth_response = profile_repo.supabase.auth.get_user(request.token)
            user_id = auth_response.user.id
            
        # Update the password
        result = profile_repo.update_user_password(user_id, request.new_password)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating password: {e}"
        }

@router.post("/set_user_pilot")
async def set_user_pilot(request: UserPilotRequest, user_id=Depends(verify_token)):
    """
    Sets the user as a pilot or not.
    """
    user_id = user_id["id"]
    repo = ProfileRepository()
    results = repo.set_user_pilot(user_id=user_id, is_pilot=request.is_pilot)
    return results

@router.get("/get_user_pilot")
async def get_pilot(user_id=Depends(verify_token)) -> bool:
    """
    Gets if the user is opted in to the pilot program.
    """
    user_id = user_id["id"]
    repo = ProfileRepository()
    results = repo.get_user_pilot(user_id=user_id)
    return results



