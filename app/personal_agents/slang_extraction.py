from datetime import datetime
import logging
from typing import List, Optional, cast
from agents import Agent, Runner
from app.supabase.pgvector import find_similar_slang, store_user_slang
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


class SlangRetrieval(BaseModel):
    id: str
    slang_text: str
    metadata: SlangMetadata
    similarity: float
    
    # Custom model configuration to handle the metadata JSON string
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_raw_data(cls, data):
        # Handle case where data is a string
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except:
                # If it can't be parsed as JSON, create a simple structure
                return cls(id="unknown", slang_text=data, metadata=SlangMetadata(
                    score=SlangScore(value_score=0.5, reason="Imported slang"),
                    topics=[], timestamp=datetime.now().isoformat()
                ), similarity=0.0)
                
        # Convert the metadata string to dict if it's a string
        if isinstance(data.get('metadata'), str):
            import json
            data = dict(data)  # Create a copy to avoid modifying the original
            data['metadata'] = json.loads(data['metadata'])
        return cls(**data)

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
            result : SlangResult = cast(SlangResult, slang_result.final_output)
                        
            logging.info(f"Extracted slang: {result}")
            
            if result.metadata.score.value_score < 0.3:
                logging.info("Extracted slang is not valuable enough to store.")
                return None
            
            result.metadata.timestamp = self.get_timestamp()
            await self.store_slang(result)
            
            return result
        except Exception as e:
            logging.error(f"Error extracting slang: {e}")
            return None

    async def store_slang(self, slang: SlangResult):
        """
        Store extracted slang in the vector store using a similar function to your knowledge extraction.
        """
        store_user_slang(self.user_id, slang.slang_text, slang.metadata.model_dump())

    def retrieve_similar_slang(self, query: str, top_k: int = 2) -> List[SlangRetrieval]:
        """
        Retrieve stored slang that is similar to the given query.
        """
        try:
            slangs = find_similar_slang(self.user_id, query, top_k)
            
            if slangs and len(slangs) > 0:
                return [SlangRetrieval.from_raw_data(slang) for slang in slangs]
        except Exception as e:
            logging.error(f"Error retrieving slang: {e}")
        
        return []

    # TODO: Add a pretty print function for the slang results
    def pretty_print_slang_result(self, slangs: List[SlangRetrieval]) -> str:
        if not slangs:
            return "No slang patterns found."
            
        formatted_slangs = ""
        for slang in slangs:
            formatted_slangs += f"""
            Slang: {slang.slang_text} - Topics: {slang.metadata.topics} - Similarity: {slang.similarity}"""
        return formatted_slangs

