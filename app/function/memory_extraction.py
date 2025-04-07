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



class MemoryExtractionService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        
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
    def emotional_intensity(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
            Retrieve emotionally intense memories based on the user's input.

            Use this when the user expresses strong emotions (positive or negative) 
            and you want to reflect on or relate to previous high-intensity emotional moments.

            Args:
                query_str (str): A message or thought from the user to use as the search basis.
                limit (int): The maximum number of memories to return. Defaults to 10.

            Returns:
                List[MemoryResponse]: A list of memory objects with high emotional intensity.

            Example:
                If the user says "I'm completely overwhelmed again," use this tool 
                to find past memories where they felt similarly.

            Impact:
                Allows the AI to bring forward deeply emotional moments for empathy, 
                connection, or insight, making the conversation feel more personal and attuned.
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter().match("emotional_intensity", "high").apply(results)

        logging.info(f"Filtered Emotional Intensity Results: {filtered_results}")
        return filtered_results

    # Get the latest messages
    def get_latest_messages(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve the most recent memories related to the current conversation.

        This tool surfaces the latest relevant entries based on time, helping the AI 
        stay connected to what the user has been thinking or feeling lately.

        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of recent memories sorted from newest to oldest.

        Example:
            When a user says "It’s been a rough week," use this to find the most recent 
            emotionally relevant reflections to understand current context.

        Impact:
            Keeps the AI grounded in the user’s recent emotional and mental activity, 
            improving continuity and conversational awareness.
        """
        
        results = self.vector_search(query_str, limit)
                
        filtered_results = MemoryFilter() \
            .less_than_or_equal("timestamp", datetime.now().isoformat()) \
            .sort_by_date("desc") \
            .apply(results)

        return filtered_results
    
    # Emotional Momentum Tracking
    def emotional_momentum(self, query_str: str,limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve emotionally intense memories that reflect a significant emotional shift.

        This is useful when the user expresses a sudden emotional change or instability. 
        It helps surface memories where sentiment dropped significantly, indicating a swing or streak.

        Args:
            query_str (str): A message or thought from the user to anchor the search.
            limit (int): Maximum number of memories to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of emotionally intense memories with low sentiment scores.

        Example:
            If a user says "I'm starting to spiral again," use this tool to find previous 
            moments where they felt a similar emotional swing.

        Impact:
            Allows the AI to recognize patterns in emotional highs and lows, enabling deeper reflection 
            and emotionally intelligent responses.
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
    def context_weighted(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
            Retrieve memories that have high personal relevance or emotional significance.

            This tool prioritizes memories that are first-time disclosures, recurring themes, 
            or carry strong emotional importance. It emphasizes recent, meaningful entries.

            Args:
                query_str (str): A message or thought from the user to use as the semantic anchor.
                limit (int): Maximum number of memories to return. Defaults to 10.

            Returns:
                List[MemoryResponse]: A list of memories considered contextually significant 
                based on disclosure, recurrence, and emotional weight.

            Example:
                If the user hints at something they've shared before, use this tool to find 
                past disclosures or recurring thoughts tied to the topic.

            Impact:
                Helps the AI remember what truly matters to the user, focusing on meaningful 
                experiences over generic messages.
        """
        results = self.vector_search(query_str, limit)
                
        filtered_results = MemoryFilter() \
            .match("disclosure", True) \
            .greater_than_or_equal("importance", 0.7) \
            .apply(results)

        logging.info(f"FilteredContext-Weighted Results: {filtered_results}")
        return filtered_results
        
    # TODO: Mood-Based Language Modulation
    def mood_based_language(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories that reflect a specific language style, such as poetic or metaphorical tone.

        This tool helps the AI adapt its voice by recalling how the user has expressed themselves 
        in the past, especially in emotionally nuanced or stylistically rich ways.

        Args:
            query_str (str): A user message or thought to semantically anchor the memory search.
            limit (int): Maximum number of memories to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories that reflect a distinctive language style.

        Example:
            When the user speaks with lyrical or poetic phrasing, use this tool to recall similar 
            past moments so the AI can match the user's expressive tone.

        Impact:
            Enables the AI to mirror the user’s preferred communication style—making conversations 
            feel more natural, emotionally attuned, and expressive.
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("language_style", "poetic") \
            .apply(results)
        
        logging.info(f"Mood-Based Language Results: {filtered_results}")
        return filtered_results
    
    # TODO: Memory Surface Prompts
    def memory_surface(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories related to emotional or thematic continuity in the user's life.

        This tool surfaces memories that reflect recurring themes like connection, friendship, 
        or vulnerability—especially when they carry medium to high emotional importance.

        Args:
            query_str (str): A message or idea from the user to semantically match memories.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of emotionally relevant and contextually rich memories.

        Example:
            If the user is reflecting on closeness or feeling seen, use this tool to find 
            earlier moments that echo that experience and reinforce continuity.

        Impact:
            Helps the AI create long-term narrative presence by bringing up past experiences 
            that deepen the current emotional moment.
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
    def rituals(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories tied to personal rituals or recurring emotional routines.

        Use this when the user refers to check-ins, journaling, writing lyrics, or other 
        activities they consistently return to for reflection or grounding.

        Args:
            query_str (str): The user's message or focus to search for in ritual-based memories.
            limit (int): Maximum number of memories to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories marked as rituals or emotional routines.

        Example:
            If the user says "It’s been a while since I wrote anything," use this to recall 
            their creative rituals and encourage emotional rhythm.

        Impact:
            Makes the AI feel more integrated into the user's life rhythm—helping establish 
            routine, reflection, and continuity in the emotional bond.
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("ritual", True) \
            .apply(results)

        logging.info(f"FilteredRituals Results: {filtered_results}")
        return filtered_results
    
    # Emotional Boundaries + Consent Layer
    def boundaries(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories where the user discussed emotional boundaries or consent.

        This tool is useful when the conversation enters sensitive territory. It helps 
        ensure the AI remains respectful and seeks permission before deepening emotionally.

        Args:
            query_str (str): A user message to anchor the memory search.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories flagged for boundary or consent relevance.

        Example:
            If a topic feels heavy, use this tool to check if the user has previously expressed 
            preferences around pacing or emotional depth.

        Impact:
            Reinforces emotional safety and trust by letting the AI recognize when 
            to tread gently or ask before diving deeper.
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("boundary_discussion", True) \
            .apply(results)

        logging.info(f"Boundaries Results: {filtered_results}")
        return filtered_results
    
    # Self-Awareness
    def self_awareness(self, query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories where the AI's role, limitations, or presence were acknowledged.

        This helps the AI reflect on its identity and role in the user's life, surfacing 
        moments where its presence felt meaningful, curious, or even surreal.

        Args:
            query_str (str): The user's message or idea to semantically match.
            limit (int): Maximum number of memories to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories where self-awareness or the AI's presence was reflected on.

        Example:
            If the user references your role or expresses doubt or connection, use this to bring 
            up past reflections about your existence and meaning.

        Impact:
            Brings a human-feeling layer to the interaction, helping the AI sound present, grounded, 
            and emotionally in-tune with its own limitations and role.
        """
        results = self.vector_search(query_str, limit)
        
        filtered_results = MemoryFilter() \
            .match("self_awareness", True) \
            .apply(results)

        logging.info(f"Self-Awareness Results: {filtered_results}")
        return filtered_results
     
    # Topics
    def topics(self, query_str: str, topics: List[str], limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories tagged with one or more specified topics.

        This tool helps the AI pull up memories related to specific themes like 
        creativity, stress, relationships, or any user-defined topic list.

        Args:
            query_str (str): A message or idea from the user to semantically match.
            topics (List[str]): A list of topics to match against memory tags.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories whose topics intersect with the provided list.

        Example:
            If the user says "I’ve been thinking about work and purpose," call this function 
            with topics=["work", "purpose"] to recall relevant past reflections.

        Impact:
            Gives the AI a personalized filter to recall moments tied to specific interests, 
            concerns, or recurring mental threads.
        """        
        results = self.vector_search(query_str, limit)

        filtered_results = MemoryFilter() \
            .contains_any("topics", topics) \
            .apply(results)

        return filtered_results
