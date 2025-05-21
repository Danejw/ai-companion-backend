import json
from typing import cast
from agents import Runner
from fastapi import HTTPException
from pydantic import BaseModel
from supabase import create_client
import os

# Setup Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for writes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class SimplifiedFeedbackPayload(BaseModel):
    message_input: str
    message_output: str
    feedback_type: bool

class Metadata(BaseModel):
    reasoning: str
    topics: list[str]
    tone: str
    emotion: str

class FeedbackMetadata(BaseModel):
    tags: list[str]
    metadata: Metadata 

class FeedbackPayload(BaseModel):
    model_version: str
    payload: SimplifiedFeedbackPayload
    metadata: FeedbackMetadata
    

async def get_agent_metadata(payload: SimplifiedFeedbackPayload) -> FeedbackMetadata:
    from app.personal_agents.feedback_agent import finetune_feedback_agent
    feedback_str = json.dumps(payload.model_dump())
    feedback_payload = await Runner.run(finetune_feedback_agent, feedback_str)
    result : FeedbackMetadata = cast(FeedbackMetadata, feedback_payload.final_output)
    return result
    
async def build_feedback_payload(payload: SimplifiedFeedbackPayload, metadata: FeedbackMetadata) -> FeedbackPayload:
    return FeedbackPayload(
        model_version=os.getenv("OPENAI_MODEL"),
        payload=payload,
        metadata=metadata
    )

def submit_finetune_feedback(user_id: str, payload: FeedbackPayload):    
    try:
        response = supabase.table("finetune_feedback").insert({
            "user_id": user_id,
            "message_input": payload.payload.message_input,
            "message_output": payload.payload.message_output,
            "feedback_type": payload.payload.feedback_type,
            "model_version": payload.model_version,
            "tags": payload.metadata.tags,
            "metadata": payload.metadata.metadata.model_dump()
        }).execute()

        if response:
            return {"success": True}
        else:
            return {"success": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
