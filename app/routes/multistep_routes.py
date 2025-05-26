from fastapi import APIRouter
from app.psychology.multistep_service import flows

router = APIRouter()

@router.get("/flows")
async def get_multistep_flows() -> dict:
    """Return all available multistep flows."""
    return {flow_id: flow.model_dump() for flow_id, flow in flows.items()}
