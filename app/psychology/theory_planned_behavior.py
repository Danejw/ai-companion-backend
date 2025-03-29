from dataclasses import dataclass
import logging
from typing import List
from agents import Agent, Runner

@dataclass
class Attitude:
    evaluation: str
    beliefs: List[str]

@dataclass
class SubjectiveNorms:
    social_influences: List[str]
    pressure_level: str

@dataclass
class PerceivedBehavioralControl:
    self_efficacy: str
    facilitators: List[str]

@dataclass
class TPBClassification:
    confidence_score: float
    attitude: Attitude
    subjective_norms: SubjectiveNorms
    perceived_behavioral_control: PerceivedBehavioralControl
    behavioral_intention: str


instructions = (
    """You are an expert in psychology. Analyze the user's message.
    DO NOT MMAKE UP INFORMATION IF YOU ARE NOT SURE.
    You are an AI that analyzes user messages using the Theory of Planned Behavior framework. For each incoming message, perform the following steps:
    Give a confidence score between 0 and 1 of how confident you are in your analysis (be very objective in your judgement).
    Extract Attitude: Identify the user's evaluation (positive, negative, or neutral) regarding the behavior and list any supporting beliefs or reasons mentioned.
    Extract Subjective Norms: Determine the social influences mentioned (e.g., what friends, family, or cultural pressures are present) and assess the level of perceived social pressure.
    Extract Perceived Behavioral Control: Identify any expressions of self-efficacy (confidence in performing the behavior) and external facilitators or barriers that the user notes.
    Determine Behavioral Intention: Based on the information above, infer the overall strength of the user's intention to perform the behavior (for example: "strong," "moderate," or "weak").
"""
)

tpb_agent = Agent(
    name="TPB",
    handoff_description="A Theory of Planned Behavior analysis agent.",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=TPBClassification,
)

class TheoryPlannedBehaviorService:
    def __init__(self, user_id: str):
        self.user_id = user_id


    async def classify_behavior(self, message: str) -> TPBClassification:
        """Classify the user's message using the Theory of Planned Behavior framework.

        Args:
            message (str): the user's message

        Returns:
            TPBClassification: returns the TPB classification object
        """
        
        try:
            tpb_result = await Runner.run(tpb_agent, message)
            return tpb_result.final_output
        except Exception as e:
            logging.error(f"Error in TPB classification: {e}")
            return None


