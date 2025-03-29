"deducing the specific purpose or objective behind a user’s input in a conversational context"
"understand what the user really wants from the conversation"

"ask clarifying questions"
"confidence score"

import logging
from agents import Agent, Runner
from dataclasses import dataclass


@dataclass
class IntentClassification:
    confidence_score: float
    intent: str
    clarifying_question: str
    
    

instructions = (
    """You are an expert in psychology. Analyze the user's message.
    You are an AI that analyzes user messages to determine the intent of the user during a conversation. For each incoming message, perform the following steps:
    Give a confidence score between 0 and 1 of how confident you are in your analysis (be very objective in your judgement).
    DO NOT MMAKE UP INFORMATION IF YOU ARE NOT SURE.
    Determine the intent of the user based on the message.
    If unclear, ask a clarifying question.
    """
)

intent_classification_agent = Agent(
    name="Intent Classificator",
    handoff_description="A intent classification agent.",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=IntentClassification,
)


class IntentClassificationService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    async def classify_intent(self, message: str) -> IntentClassification:
        """
        Classify the user's intention based on the message.

        Args:
            message (str): the user's message

        Returns:
            IntentClassification: returns the intent classification object
        """
        
        try:
            intent_classification_result = await Runner.run(intent_classification_agent, message)
            return intent_classification_result.final_output
        except Exception as e:
            logging.error(f"Error in intent classification: {e}")
            return None
