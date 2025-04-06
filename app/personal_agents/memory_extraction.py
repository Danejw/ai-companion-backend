# New models for enhanced memory representation


from datetime import datetime, timedelta
import json
import logging
import os
from typing import Any, Dict, List, Optional
from agents import Agent, Runner
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from supabase import create_client
from app.supabase.pgvector import generate_embedding


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



class MemoryMetadata(BaseModel):
    disclosure: bool
    recurring_theme: bool
    boundary_discussion: bool
    ritual: bool
    self_awareness: bool
    language_style: str
    
    
class MemoryVector(BaseModel):
    text: str
    timestamp: str
    sentiment_score: float
    topics: List[str]
    emotional_intensity: str
    importance: float
    metadata: MemoryMetadata
    

class MemoryResponse(BaseModel):
    id: str
    knowledge_text: str
    metadata: str
    embedding: List[float]
    mention_count: int
    last_updated: Optional[str] = None
    created_at: Optional[str] = None
    similarity: Optional[float] = None



# The system prompt for the memory extraction agent
instructions = (
    """
    You are an AI that extracts useful information from user interactions and formats it as structured memory. 
    Your job is to identify valuable personal information, preferences, facts, or emotional states about the user.
    
    For each extracted memory, provide the following fields:
    - text: The exact piece of knowledge extracted from the conversation.
    - sentiment_score: A number from -1.0 (extremely negative) to 1.0 (extremely positive) representing the emotional tone.
    - topics: A list of 1-5 tags that categorize this memory (e.g., ['work', 'stress', 'management']).
    - emotional_intensity: Categorize as 'low', 'medium', or 'high' based on how emotionally charged the content is.
    
    - importance: Assign a value from 0.0 to 1.0 representing how important this memory likely is to the user:
    - 0.0-0.3: Trivial information (casual preferences, passing comments)
    - 0.4-0.7: Moderately important (regular activities, general interests)
    - 0.8-1.0: Highly important (core values, significant relationships, major life events)
    
    - metadata: Additional contextual information:
    - disclosure: Set to true if this is a personal disclosure or vulnerable sharing.
    - recurring_theme: Set to true if this topic has been mentioned multiple times.
    - boundary_discussion: Set to true if related to personal boundaries or comfort zones.
    - ritual: Set to true if describing a routine, habit, or meaningful repeated activity.
    - self_awareness: Set to true if the user shows introspection or self-reflection.
    - language_style: Describe the user's communication style (e.g., 'direct', 'poetic', 'analytical').
    
    Only extract knowledge when meaningful (importance > 0.3). Don't extract generic conversation, pleasantries, or system instructions.
    If you're unsure about extracting a memory, evaluate whether it would be useful context for future conversations with this user.
    """
)


class MemoryExtractionService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.extraction_agent = Agent(
            name="MemoryExtractor",
            handoff_description="An agent that extracts valuable information about the user from your interactions and stores it in a vector database.",
            instructions=instructions,
            model="gpt-4o-mini",
            output_type=MemoryVector
        )
        
        
    def get_timestamp(self) -> datetime:
        return datetime.now()
    
    def relative_date(self, days_ago: int) -> str:
        target_date = self.get_timestamp() - timedelta(days=days_ago)
        return target_date.isoformat() + "Z"

    def generate_embeddings(self, text: str):
        return generate_embedding(text)
    
    
    async def extract_memory(self, message: str) -> Optional[MemoryVector]:
        try:
            memory_result = await Runner.run(self.extraction_agent, message)
            
            result = MemoryVector(**memory_result.final_output.dict())
            
            if result.importance < 0.3:
                logging.info("Extracted memory is not valuable enough to store.")
                return None

            result.timestamp = self.get_timestamp().isoformat()
            
            await run_in_threadpool(lambda: self.store_memory(result))
            
            return result
        
        except Exception as e:
            logging.error(f"Error extracting memory: {e}")
            return None

    def store_memory(self, memory: MemoryVector) -> bool:
        """
        Stores extracted memory in the vector database with safety checks.
        """
        
        try:
            text_vectors = self.generate_embeddings(memory.text)
            
            # Convert MemoryVector to dictionary for JSON serialization
            memory_dict = memory.model_dump()     
        
            
            # Check if knowledge already exists to prevent duplicates
            existing = supabase.table("user_knowledge").select("*").eq("user_id", self.user_id).eq("knowledge_text", memory.text).execute()

            if existing.data:
                # Increase mention count and update timestamp
                new_count = existing.data[0]["mention_count"] + 1
                supabase.table("user_knowledge").update({"metadata": json.dumps(memory_dict), "last_updated": "now()", "mention_count": new_count}).eq("id", existing.data[0]["id"]).execute()
            else:
                # Insert new knowledge
                supabase.table("user_knowledge").insert({"user_id": self.user_id, "knowledge_text": memory.text, "embedding": text_vectors, "metadata": json.dumps(memory_dict), "mention_count": 1}).execute()

            return True
        
        except Exception as e:
            logging.error(f"Error storing memory: {e}")
            return False
    
    # Main function to search the vector database
    def vector_search(self, query_str: str, filters: dict, limit: int = 3) -> List[MemoryResponse]:
        """
        Accepts a query string, computes its embedding, and then queries the vector DB with the given filters.
        """
        try:
            query_vector = self.generate_embeddings(query_str)
            
            # Update parameter name from "user_id" to "input_user_id"
            response = supabase.rpc("find_similar_memories", {"input_user_id": self.user_id, "query_embedding": query_vector, "top_k": limit}).execute()
            
            return response.data
        except Exception as e:
            logging.error(f"Error vector searching: {e}")
            return []
    
    
    
    
    
    # ---------------------------------------------------------------------------------

    
    
    # Emotional Momentum Tracking
    def emotional_momentum(self, query_str: str, days_ago: int = 10, limit: int = 3) -> List[MemoryResponse]:
        start_date = self.relative_date(days_ago)
        filters = {
            "timestamp": {"$gte": start_date},
            "emotional_intensity": "high",
            "sentiment_score": {"$lte": -0.7}
        }
        return self.vector_search(query_str, filters, limit)
    
    # Context-Weighted Memory
    def context_weighted(self, query_str: str, days_ago: int = 90, limit: int = 3) -> List[MemoryResponse]:
        start_date = self.relative_date(days_ago)
        filters = {
            "$or": [
                {"metadata.disclosure": True},
                {"metadata.recurring_theme": True},
                {"emotional_intensity": "high"}
            ],
            "timestamp": {"$gte": start_date}
        }
        return self.vector_search(query_str, filters, limit)
        
    
    # Mood-Based Language Modulation
    def mood_based_language(self, query_str: str, limit: int = 3) -> List[MemoryResponse]:

        
        
        filters = {
            "metadata.language_style": {"$in": ["poetic", "metaphorical"]}
        }
        return self.vector_search(query_str, filters, limit)
    
    
    # Memory Surface Prompts
    def memory_surface(self, query_str: str, limit: int = 3) -> List[MemoryResponse]:
        filters = {
            "topics": {"$in": ["friendship", "connection", "intimacy"]},
            "emotional_intensity": {"$in": ["medium", "high"]}
        }
        return self.vector_search(query_str, filters, limit)
    
    
    # Rituals and Anchors
    def rituals(self, query_str: str, limit: int = 1) -> List[MemoryResponse]:
        filters = {
            "metadata.ritual": True
        }
        return self.vector_search(query_str, filters, limit)
    
    
    # Emotional Boundaries + Consent Layer
    def boundaries(self, query_str: str, limit: int = 1) -> List[MemoryResponse]:
        filters = {
            "metadata.boundary_discussion": True
        }
        return self.vector_search(query_str, filters, limit)
    
    
    # Self-Awareness Simulation
    def self_awareness(self, query_str: str, limit: int = 1) -> List[MemoryResponse]:
        filters = {
            "metadata.self_awareness": True
        }
        return self.vector_search(query_str, filters, limit)
    
    
    # Emotional Intensity
    def emotional_intensity(self, query_str: str, limit: int = 1) -> List[MemoryResponse]:
        filters = {
            "emotional_intensity": "high"
        }
        return self.vector_search(query_str, filters, limit)

