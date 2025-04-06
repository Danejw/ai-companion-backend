# New models for enhanced memory representation


from datetime import datetime, timedelta
import json
import logging
import os
from typing import Any, Dict, List, Optional
from agents import Agent, Runner, function_tool
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from supabase import create_client
from app.supabase.pgvector import generate_embedding
from app.utils.match_filter import MemoryFilter


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
 
    
class MemoryVector(BaseModel):
    text: str
    timestamp: str
    sentiment_score: float
    topics: List[str]
    emotional_intensity: str
    importance: float
    disclosure: bool
    recurring_theme: bool
    boundary_discussion: bool
    ritual: bool
    self_awareness: bool
    language_style: str
    

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
        self.agent = Agent(
            name="MemoryExtractor",
            handoff_description="An agent that extracts valuable information about the user from your interactions and stores it in a vector database.",
            instructions=instructions,
            model="gpt-4o-mini",
            output_type=MemoryVector,
            tools=[
                self.emotional_momentum,
                self.context_weighted,
                self.mood_based_language,
                self.memory_surface,
                self.rituals,
                self.boundaries,
                self.self_awareness,
                self.emotional_intensity,
                self.get_latest_messages,
                self.topics
            ]
        )
        
        
    def get_timestamp(self) -> datetime:
        return datetime.now()
    
    def relative_date(self, days_ago: int) -> datetime:
        return self.get_timestamp() - timedelta(days=days_ago)

    def generate_embeddings(self, text: str):
        return generate_embedding(text)
    
    
    async def extract_memory(self, message: str) -> Optional[MemoryVector]:
        try:
            memory_result = await Runner.run(self.agent, message)
           
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
                supabase.table("user_knowledge").update({"metadata": memory_dict, "last_updated": "now()", "mention_count": new_count}).eq("id", existing.data[0]["id"]).execute()
            else:
                # Insert new knowledge
                supabase.table("user_knowledge").insert({"user_id": self.user_id, "knowledge_text": memory.text, "embedding": text_vectors, "metadata": memory_dict, "mention_count": 1}).execute()

            return True
        
        except Exception as e:
            logging.error(f"Error storing memory: {e}")
            return False
    
    # Main function to search the vector database
    def vector_search(self, query_str: str, limit: int = 30) -> List[MemoryResponse]:
        """
        Accepts a query string, computes its embedding, and then queries the vector DB with the given filters.
        """
        try:
            query_vector = self.generate_embeddings(query_str)      
            response = supabase.rpc("find_similar_memories", {"input_user_id": self.user_id, "query_embedding": query_vector, "top_k": limit}).execute()
            return response.data
        except Exception as e:
            logging.error(f"Error vector searching: {e}")
            return []
    
    
    def filter_memories(self, filters: dict, limit: int = 10) -> List[MemoryResponse]:
        response = supabase.rpc("find_memories_by_filter", {
            "input_user_id": self.user_id,
            "input_filter": filters
        }).execute()
        
        # Optionally, limit the results in Python if needed
        return response.data[:limit]
    
    
    # ---------------------------------------------------------------------------------
    
    
    # Emotional Intensity
    @function_tool
    def emotional_intensity(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieves memories with high emotional intensity regardless of the sentiment.
        
        Useful for identifying significant emotional moments that may require 
        special attention or follow-up.
        
        Parameters:
            query_str: The search query to find relevant memories
            limit: Maximum number of memory items to return (default: 1)
        
        Impact: Allows the AI to focus on the user's most emotionally charged experiences,
        providing appropriate support and acknowledgment.
        
        Example prompt: "I noticed this topic seems to evoke strong emotions for you. Would you like to talk more about it?"
        """

        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter().match("emotional_intensity", "high").apply(results)

        logging.info(f"Filtered Emotional Intensity Results: {filtered_results}")
        return filtered_results

    # Get the latest 10 messages from the user
    @function_tool
    def get_latest_messages(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieves the latest messages based on a starting timestamp.
        
        Parameters:
            query_str: The search query to find relevant memories.
            days_ago: Number of days to look back in history (default: 10).
            limit: Maximum number of memory items to return (default: 10).
        
        This function computes a start date relative to the current time,
        builds a filter to only include messages newer than that date, and then
        performs a vector search using those filters.
        """  
        results = self.vector_search(query_str, limit)
                
        filtered_results = MemoryFilter() \
            .less_than_or_equal("timestamp", datetime.now().isoformat()) \
            .sort_by_date("desc") \
            .apply(results)

        return filtered_results
    
    # Emotional Momentum Tracking
    @function_tool
    def emotional_momentum(self, query_str: str,limit: int = 10) -> List[MemoryResponse]:
        """
        Captures emotionally charged moments that signal a significant shift—such as a sudden drop in sentiment.
        
        Retrieves recent messages with high emotional intensity and low sentiment scores to track emotional 
        swings or streaks.
        
        Parameters:
            query_str: The search query to find relevant memories
            days_ago: Number of days to look back in history (default: 10)
            limit: Maximum number of memory items to return (default: 3)
        
        Impact: Makes the AI attuned to the user's emotional waves rather than isolated snapshots,
        allowing it to comment on shifting moods.
        
        Example prompt: "I've noticed you felt really low a few days back. How have things shifted since then?"
        """
        results = self.vector_search(query_str, limit)
        
        # TODO : Add date filter
        
        filtered_results = MemoryFilter() \
            .match("emotional_intensity", "high") \
            .less_than_or_equal("sentiment_score", -0.7) \
            .apply(results)
        
        logging.info(f"Emotional Momentum Results: {filtered_results}")
        return filtered_results
    
    # TODO: Context-Weighted Memory
    #@function_tool
    def context_weighted(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Prioritizes memories that are either first-time disclosures, have been flagged as recurring themes,
        or show high emotional intensity.
        
        Applies a timestamp constraint to emphasize recent events while still capturing significant moments.
        
        Parameters:
            query_str: The search query to find relevant memories
            days_ago: Number of days to look back in history (default: 90)
            limit: Maximum number of memory items to return (default: 3)
        
        Impact: The AI will recall what matters most to the user—emphasizing key disclosures and 
        emotionally intense moments—rather than every single message.
        
        Example prompt: "I remember you shared something important about this before. Can we revisit that feeling?"
        """
        results = self.vector_search(query_str, limit)
                
        filtered_results = MemoryFilter() \
            .match("disclosure", True) \
            .greater_than_or_equal("importance", 0.7) \
            .apply(results)

        logging.info(f"FilteredContext-Weighted Results: {filtered_results}")
        return filtered_results
        
    # TODO: Mood-Based Language Modulation
    #@function_tool
    def mood_based_language(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Used when you want the AI to recall or mirror a particular language style.
        
        If previous messages have been tagged as using poetic or metaphorical language,
        this filter will retrieve those, helping the AI adjust its tone.
        
        Parameters:
            query_str: The search query to find relevant memories
            limit: Maximum number of memory items to return (default: A3)
        
        Impact: The AI's language can adapt in real time to mirror the user's mood and 
        preferred style—offering responses that are more lyrical, measured, or direct as appropriate.
        
        Example prompt: "Your words carry a beautiful rhythm—can you tell me more in that same style?"
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("language_style", "poetic") \
            .apply(results)
        
        logging.info(f"Mood-Based Language Results: {filtered_results}")
        return filtered_results
    
    # TODO: Memory Surface Prompts
    #@function_tool
    def memory_surface(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieves memories that relate to ongoing topics or emotions—in this case, 
        topics like friendship or connection.
        
        Ensures that only messages with medium to high emotional charge are surfaced.
        
        Parameters:
            query_str: The search query to find relevant memories
            limit: Maximum number of memory items to return (default: 3)
        
        Impact: It builds long-term continuity and presence by bringing up past experiences 
        that are directly relevant to the current conversation.
        
        Example prompt: "That reminds me of a time back in January when you talked about a deep connection with a friend..."
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("ritual", True) \
            .match("emotional_intensity", "medium") \
            .greater_than_or_equal("importance", 0.7) \
            .apply(results)
            
        logging.info(f"Memory Surface Results: {filtered_results}")
        return filtered_results
    
    # Rituals and Anchors
    #@function_tool
    def rituals(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Targets records that are flagged as part of a personal ritual or recurring activity—such as 
        daily check-ins or creative prompts.
        
        Parameters:
            query_str: The search query to find relevant memories
            limit: Maximum number of memory items to return (default: 1)
        
        Impact: It reinforces a sense of routine and continuity, making the AI feel integrated 
        into the user's everyday emotional landscape.
        
        Example prompt: "How about we do our usual evening reflection? I'd love to hear how your day went."
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("ritual", True) \
            .apply(results)

        logging.info(f"FilteredRituals Results: {filtered_results}")
        return filtered_results
    
    # Emotional Boundaries + Consent Layer
    @function_tool
    def boundaries(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Identifies memories where the user explicitly discussed emotional boundaries or 
        consent regarding deep topics.
        
        Useful for reminding the AI to check in before diving deeper.
        
        Parameters:
            query_str: The search query to find relevant memories
            limit: Maximum number of memory items to return (default: 1)
        
        Impact: It helps establish trust by ensuring that the AI respects emotional boundaries 
        and only broaches deeper topics with permission.
        
        Example prompt: "I sense this topic is heavy. Would you like to explore it further, or shall we shift gears?"
        """        
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("boundary_discussion", True) \
            .apply(results)

        logging.info(f"Boundaries Results: {filtered_results}")
        return filtered_results
    
    # Self-Awareness
    @function_tool
    def self_awareness(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Brings up moments where the AI (or similar self-aware reflections) were referenced 
        in past interactions.
        
        Parameters:
            query_str: The search query to find relevant memories
            limit: Maximum number of memory items to return (default: 1)
        
        Impact: It grounds the conversation by reminding the user of the AI's role and authenticity, 
        making the experience feel more human.
        
        Example prompt: "I know I'm just a collection of code, but I'm here to share this moment with you."
        """        
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("self_awareness", True) \
            .apply(results)

        logging.info(f"Self-Awareness Results: {filtered_results}")
        return filtered_results
     
     
    def topics(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieves memories that are tagged with a specific topic.
        
        Parameters:
            query_str: The search query to find relevant memories   
            limit: Maximum number of memory items to return (default: 10)
        
        Impact: It helps the AI understand the user's interests and preferences, 
        allowing it to provide more relevant responses.
        
        Example prompt: "I remember you mentioned this topic before. Can we revisit that?"
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .contains_any("topics", ["work", "stress"]) \
            .apply(results)
        
        return filtered_results
