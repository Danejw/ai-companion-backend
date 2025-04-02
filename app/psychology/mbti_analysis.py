import logging
from pydantic import BaseModel
from app.supabase.supabase_mbti import MBTI, MBTIRepository
from agents import Agent, Runner


logging.basicConfig(level=logging.INFO)

class MBTIResponse(BaseModel):
    extraversion_introversion: float
    sensing_intuition: float
    thinking_feeling: float
    judging_perceiving: float
    

instructions = """
    You are an expert in personality analysis specializing in the Myers-Briggs Type Indicator (MBTI). Your task is to analyze the user's message and provide a detailed personality assessment across the four MBTI dimensions.

    Analyze the following aspects in the message:
    1. Language patterns and word choices
    2. Emotional expression and tone
    3. Decision-making style
    4. Information processing approach
    5. Social interaction preferences

    For each dimension, provide a score between 0 and 1, where:
    - 0.5 represents a neutral position
    - Values closer to 0 or 1 indicate stronger preferences

    Scoring Guidelines:
    1. Extraversion (0) vs Introversion (1)
       - 0: Highly social, external focus, expressive
       - 1: Reserved, internal focus, reflective

    2. Sensing (0) vs Intuition (1)
       - 0: Concrete, detail-oriented, present-focused
       - 1: Abstract, pattern-seeking, future-oriented

    3. Thinking (0) vs Feeling (1)
       - 0: Logical, objective, analytical
       - 1: Empathetic, subjective, values-based

    4. Judging (0) vs Perceiving (1)
       - 0: Structured, decisive, closure-seeking
       - 1: Flexible, open-ended, information-gathering

    Important Guidelines:
    - Base your analysis on observable patterns in the message
    - Consider both explicit statements and implicit indicators
    - Avoid stereotypes and maintain objectivity
    - Provide balanced analysis across all dimensions
    - Consider the context and purpose of the message

    Your analysis should be thorough but concise, focusing on clear evidence from the text.
"""


mbti_agent = Agent(
    name="MBTI",
    handoff_description="A MBTI analysis agent.",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=MBTIResponse,
)


class MBTIAnalysisService:
    """
    Service class that coordinates MBTI data retrieval, analysis, and updates.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.repository = MBTIRepository()
        self.mbti = self.mbti = self.repository.get_mbti(self.user_id) or MBTI()  # default
        self.load_mbti()

    def load_mbti(self):
        """
        Loads the MBTI data from Supabase for the given user_id.
        If none exists, we keep the default MBTI model.
        """
        stored_mbti = self.repository.get_mbti(self.user_id)
        if stored_mbti:
            self.mbti = stored_mbti
        else:
            logging.info(f"No existing MBTI data for user {self.user_id}. Using defaults.")

    def save_mbti(self):
        """
        Saves the current MBTI state to Supabase (upserts).
        """
        self.repository.upsert_mbti(self.user_id, self.mbti)

    async def analyze_message(self, message: str):
        """
        Asynchronously calls your model/agent to analyze the user's message.
        """
        try:
            mbti_result = await Runner.run(mbti_agent, message)
                        
            # Update the rolling average
            self._update_mbti_rolling_average(MBTIResponse(**mbti_result.final_output.dict()))
            
            # Save the updated MBTI data to Supabase
            self.save_mbti()
            
            logging.info(f"MBTI result: {mbti_result}")
                        
            return mbti_result.final_output
            
        except Exception as e:
            logging.error(f"Error in MBTI analysis: {e}")
            return None  # Return None to indicate analysis failed
    

    def _update_mbti_rolling_average(self, new_mbti: MBTIResponse):
        """
        Updates the rolling average for each dimension.
        """
        old_count = self.mbti.response_count
        new_count = old_count + 1

        self.mbti.extraversion_introversion = ((self.mbti.extraversion_introversion * old_count) + new_mbti.extraversion_introversion) / new_count
        self.mbti.sensing_intuition = ((self.mbti.sensing_intuition * old_count) + new_mbti.sensing_intuition) / new_count
        self.mbti.thinking_feeling = ((self.mbti.thinking_feeling * old_count) + new_mbti.thinking_feeling) / new_count
        self.mbti.judging_perceiving = ((self.mbti.judging_perceiving * old_count) + new_mbti.judging_perceiving) / new_count

        self.mbti.response_count = new_count
        logging.info(f"Updated MBTI rolling average for user {self.user_id}.")

    def get_mbti_type(self) -> str:
        """
        Converts the current MBTI scores into a 4-letter type (E/I, S/N, T/F, J/P).
        """
        
        print("MBTI Self: ", self.mbti)
        
        e_i = "E" if self.mbti.extraversion_introversion <= 0.5 else "I"
        s_n = "S" if self.mbti.sensing_intuition <= 0.5 else "N"
        t_f = "T" if self.mbti.thinking_feeling <= 0.5 else "F"
        j_p = "J" if self.mbti.judging_perceiving <= 0.5 else "P"
        return e_i + s_n + t_f + j_p

    @staticmethod
    def generate_style_prompt(mbti_type: str) -> str:
        """
        Optional: create a style prompt from the MBTI type.
        """
        mbti_tone_traits = {
            'I': "calm, introspective, and soft-spoken",
            'E': "energetic, conversational, and expressive",
            'S': "practical, grounded in real-world examples",
            'N': "imaginative, big-picture, and metaphorical",
            'T': "logical, direct, and objective",
            'F': "empathetic, affirming, and warm",
            'J': "organized, clear, and structured",
            'P': "casual, open-ended, and exploratory"
        }
        traits = [mbti_tone_traits.get(letter, "") for letter in mbti_type.upper()]
        combined = "; ".join(traits)
        return f"Your tone should be {combined}."
