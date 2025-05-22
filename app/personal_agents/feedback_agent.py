from agents import Agent
from app.supabase.finetune_feedback import FeedbackMetadata

instructions = """
Given an input, you will need to extract the tags and metadata from the input.

Schema:
class FeedbackMetadata(BaseModel):
    tags: list[str] <-- list of tags to be used for the feedback
    metadata: dict <-- metadata to be used for the feedback

"""

finetune_feedback_agent = Agent(
    name="Finetune Feedback Agent",
    handoff_description="A feedback agent that uses the user's feedback to improve the model",
    instructions=instructions,
    output_type=FeedbackMetadata
)

