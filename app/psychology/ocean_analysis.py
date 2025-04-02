from pydantic import BaseModel
from agents import Agent, Runner
import logging
from app.supabase.supabase_ocean import Ocean, OceanRepository

    
logging.basicConfig(level=logging.INFO)

class OceanResponse(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

instructions = """
You are an expert in personality analysis using the OCEAN (Big Five) personality framework. You will analyze the given message and return a detailed personality assessment.

The OCEAN personality analysis consists of 5 core dimensions:

1. Openness to Experience (0-1):
   - High (>0.5): Curious, creative, imaginative, open to new ideas
   - Low (<0.5): Traditional, practical, conventional, prefers routine

2. Conscientiousness (0-1):
   - High (>0.5): Organized, responsible, goal-oriented, detail-focused
   - Low (<0.5): Spontaneous, flexible, less structured, more laid-back

3. Extraversion (0-1):
   - High (>0.5): Outgoing, energetic, sociable, enjoys being around people
   - Low (<0.5): Reserved, introspective, prefers solitude, less social

4. Agreeableness (0-1):
   - High (>0.5): Compassionate, cooperative, trusting, considerate
   - Low (<0.5): Competitive, skeptical, direct, self-focused

5. Neuroticism (0-1):
   - High (>0.5): Emotionally sensitive, anxious, moody, stress-reactive
   - Low (<0.5): Emotionally stable, calm, resilient, less reactive

Scoring Guidelines:
- Each dimension should be scored between 0 and 1
- 0.5 represents a neutral score
- Scores above 0.5 indicate high levels of the trait
- Scores below 0.5 indicate low levels of the trait
- Consider both explicit statements and implicit indicators in the message
- Be objective and consistent in your analysis
- Consider the context and intensity of the expressed traits
"""

ocean_agent = Agent(
    name="OCEAN",
    handoff_description="A Ocean framework sentiment analysis agent.",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=OceanResponse,
)

class OceanAnalysisService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.repository = OceanRepository()
        self.ocean = self.repository.get_ocean(self.user_id) or Ocean()
        self.load_ocean()

    def load_ocean(self):
        stored_ocean = self.repository.get_ocean(self.user_id)
        if stored_ocean:
            self.ocean = stored_ocean
        else:
            logging.ERROR(f"No existing OCEAN data for user {self.user_id}. Using defaults.")

    def save_ocean(self):
        self.repository.upsert_ocean(self.user_id, self.ocean)

    async def analyze_message(self, message: str):
        try:
            ocean_result = await Runner.run(ocean_agent, message)
            logging.info(f"OCEAN result: {ocean_result}")
                    
            # Update rolling average
            self.update_ocean_rolling_average(OceanResponse(**ocean_result.final_output.dict()))
            
            # Save the updated OCEAN data to Supabase
            self.save_ocean()
            
            return ocean_result.final_output
            
        except Exception as e:
            logging.error(f"Error in OCEAN analysis: {e}")
            return None  # Return None to indicate analysis failed

    def update_ocean_rolling_average(self, new_ocean: OceanResponse):
        old_count = self.ocean.response_count
        new_count = old_count + 1

        def update_dimension(old_avg: float, new_val: float) -> float:
            # If this is the first entry, use the new value directly
            if old_count == 0:
                return new_val
            
            # Calculate weighted average based on response count
            # Newer responses have slightly more weight (1.2x) to capture recent changes
            weight = 1.2
            old_weight = old_count
            new_weight = weight
            
            # Calculate weighted average
            weighted_sum = (old_avg * old_weight) + (new_val * new_weight)
            total_weight = old_weight + new_weight
            
            return weighted_sum / total_weight

        # Update each dimension with the new weighted average
        self.ocean.openness = update_dimension(self.ocean.openness, new_ocean.openness)
        self.ocean.conscientiousness = update_dimension(self.ocean.conscientiousness, new_ocean.conscientiousness)
        self.ocean.extraversion = update_dimension(self.ocean.extraversion, new_ocean.extraversion)
        self.ocean.agreeableness = update_dimension(self.ocean.agreeableness, new_ocean.agreeableness)
        self.ocean.neuroticism = update_dimension(self.ocean.neuroticism, new_ocean.neuroticism)
        self.ocean.response_count = new_count

    def get_personality_traits(self) -> dict:
        """
        Returns the current OCEAN scores as personality traits with detailed descriptions.
        """
        def get_trait_description(score: float, trait: str) -> dict:
            level = "High" if score >= 0.5 else "Low"
            descriptions = {
                "openness": {
                    "High": "Curious and open to new experiences",
                    "Low": "Traditional and prefers routine"
                },
                "conscientiousness": {
                    "High": "Organized and goal-oriented",
                    "Low": "Flexible and spontaneous"
                },
                "extraversion": {
                    "High": "Outgoing and sociable",
                    "Low": "Reserved and introspective"
                },
                "agreeableness": {
                    "High": "Compassionate and cooperative",
                    "Low": "Direct and self-focused"
                },
                "neuroticism": {
                    "High": "Emotionally sensitive",
                    "Low": "Emotionally stable"
                }
            }
            return {
                "level": level,
                "score": round(score, 2),
                "description": descriptions[trait][level]
            }

        return {
            "openness": get_trait_description(self.ocean.openness, "openness"),
            "conscientiousness": get_trait_description(self.ocean.conscientiousness, "conscientiousness"),
            "extraversion": get_trait_description(self.ocean.extraversion, "extraversion"),
            "agreeableness": get_trait_description(self.ocean.agreeableness, "agreeableness"),
            "neuroticism": get_trait_description(self.ocean.neuroticism, "neuroticism")
        }


