from datetime import datetime
import logging
from typing import List, Optional
from agents import Agent, Runner
from app.supabase.pgvector import find_similar_knowledge, find_similar_slang, store_user_knowledge, store_user_slang
from pydantic import BaseModel



class SlangScore(BaseModel):
    value_score: float  # How valuable or unique is this slang expression (0 to 1)
    reason: str         # Explanation (e.g., "Common slang", "Unique phrase", etc.)

class SlangMetadata(BaseModel):
    score: SlangScore
    topics: List[str]   # Tags or categories for the slang, if applicable
    timestamp: str

class SlangResult(BaseModel):
    slang_text: str     # The extracted slang or informal expression
    metadata: SlangMetadata

# Instructions for the agent
instructions = (
    "You are an AI that extracts slang and informal language from user interactions. "
    "Your task is to identify unique or personalized slang phrases or informal expressions that the user uses, "
    "while filtering out any swear words. Evaluate the extracted slang on a scale from 0 to 1 based on its uniqueness and relevance. "
    "If the value score is below 0.3, do not store the slang. Return your result in the following JSON format:\n"
)

class SlangExtractionService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.extraction_agent = Agent(
            name="SlangExtractor",
            handoff_description="An agent that extracts slang and informal language from user interactions, filtering out swear words.",
            instructions=instructions,
            model="gpt-4o-mini",
            output_type=SlangResult
        )

    def get_timestamp(self) -> str:
        return datetime.now().isoformat()

    async def extract_slang(self, message: str) -> Optional[SlangResult]:
        try:
            slang_result = await Runner.run(self.extraction_agent, message)
            result = SlangResult(**slang_result.final_output.dict())
            
            logging.info(f"Extracted slang: {result}")
            
            if result.metadata.score.value_score < 0.3:
                logging.info("Extracted slang is not valuable enough to store.")
                return None
            
            result.metadata.timestamp = self.get_timestamp()
            self.store_slang(result)
            
            return result
        except Exception as e:
            logging.error(f"Error extracting slang: {e}")
            return None

    async def store_slang(self, slang: SlangResult):
        """
        Store extracted slang in the vector store using a similar function to your knowledge extraction.
        """
        store_user_slang(self.user_id, slang.slang_text, slang.metadata.dict())

    def retrieve_similar_slang(self, query: str, top_k: int = 2):
        """
        Retrieve stored slang that is similar to the given query.
        """
        return find_similar_slang(self.user_id, query, top_k)
