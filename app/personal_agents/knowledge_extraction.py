import datetime
import logging
from typing import List, Optional, Dict, Any
from agents import Agent, Runner
from app.supabase.pgvector import find_similar_knowledge, store_user_knowledge
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool


class KnowledgeScore(BaseModel):
    value_score: float
    reason: str

class KnowledgeMetadata(BaseModel):
    score: KnowledgeScore
    topic: List[str]
    timestamp: str
    
class KnowledgeResult(BaseModel):
    knowledge_text: str
    metadata: KnowledgeMetadata



instructions = (
    "You are an AI that extracts useful knowledge from user interactions. "
    "Before extracting knowledge, check if the message contains any valuable personal information, preferences, or facts about the user. "
    "Assign a value score (0-1) based on how meaningful the extracted knowledge is:\n"
    "- 0.0 → No valuable knowledge (greetings, generic phrases)\n"
    "- 0.5 → Somewhat useful (general interests, common topics)\n"
    "- 1.0 → Very useful (specific preferences, unique facts about the user)\n"
    "If the value score is below 0.3, do not extract knowledge.\n\n"
)


class KnowledgeExtractionService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.extraction_agent = Agent(
            name="KnowledgeExtractor",
            handoff_description="An agent that extracts valuable information about the user from your interactions.",
            instructions=instructions,
            model="gpt-4o-mini",
            output_type=KnowledgeResult
        )

    def get_timestamp(self):
        return datetime.datetime.now().isoformat()

    async def extract_knowledge(self, message: str) -> Optional[KnowledgeResult]:
        try:
            knowledge_result = await Runner.run(self.extraction_agent, message)
            result = KnowledgeResult(**knowledge_result.final_output.dict())
            
            logging.info(f"Extracted knowledge: {result}")  

            if result.metadata.score.value_score < 0.3:
                logging.info("Extracted knowledge is not valuable enough to store.")
                return None

            result.metadata.timestamp = self.get_timestamp()
            await run_in_threadpool(self.store_knowledge, result)
            return result
        except Exception as e:
            logging.error(f"Error extracting knowledge: {e}")
            return None

    def store_knowledge(self, knowledge: KnowledgeResult):
        """
        Store extracted knowledge in the pgvector-powered Supabase table.
        """
        store_user_knowledge(self.user_id, knowledge.knowledge_text, knowledge.metadata.dict())

    def retrieve_similar_knowledge(self, query: str, top_k=5):
        """
        Retrieve stored knowledge that is similar to the given query.
        """
        return find_similar_knowledge(self.user_id, query, top_k)
