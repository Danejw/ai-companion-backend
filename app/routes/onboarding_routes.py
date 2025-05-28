from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Optional

from app.auth import verify_token
from app.supabase.onboarding_flows import OnboardingRepository

router = APIRouter()
onboarding_repo = OnboardingRepository()


class OnboardingUpdate(BaseModel):
    screen_id: str
    response: Optional[Dict] = None
    complete: Optional[bool] = False


@router.post("/onboarding/update")
async def update_onboarding(
    data: OnboardingUpdate, user=Depends(verify_token)
):
    """Update onboarding progress for the authenticated user."""
    user_id = user["id"]

    flow = onboarding_repo.get_flow(user_id)
    if flow is None:
        onboarding_repo.upsert_onboarding_flow(user_id)
        flow = onboarding_repo.get_flow(user_id) or {}

    flow.setdefault("responses", {})
    flow["responses"][data.screen_id] = data.response
    flow["last_screen"] = data.screen_id
    if data.complete:
        flow["status"] = "completed"

    onboarding_repo.update_flow(user_id, flow)
    return {"status": "ok"}
