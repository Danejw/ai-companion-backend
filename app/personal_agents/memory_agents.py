from datetime import datetime
from typing import List
from agents import Agent, function_tool
from app.function.memory_extraction import MemoryExtractionService


# System prompt for the memory agent
instructions = (
    """
# TOOL STRATEGY:

Choose the appropriate memory tool based on the user's message.

- Use "emotional_intensity" if the user expresses strong feelings (e.g., overwhelmed, elated, heartbroken).
- Use "context_weighted" for deeply personal, reflective moments or when the user hints at something recurring.
- Use "mood_based_language" when the user speaks poetically or emotionally stylized.
- Use "rituals" for routines like journaling, reflecting, or writing.
- Use "memory_surface" to echo deeper life themes like connection, loss, or intimacy.
- Use "boundaries" when the topic feels sensitive or emotionally heavy.
- Use "self_awareness" when the user talks about you (the AI) or your presence in their life.
- Use "topics" to retrieve memories related to specific concepts (e.g. "friendship", "creativity").

Be confident. Choose one tool per request. Return only relevant memories.
    """
)

agent = Agent(
    name="MemoryAgent",
    handoff_description="A memory agent that can retrieve memories from the user's memory.",
    instructions=instructions,
    model="gpt-4o-mini",
)


def create_memory_tools(user_id: str):
    memory_service = MemoryExtractionService(user_id)
       
    @function_tool # DONE
    def emotional_intensity(query_str: str) -> List[str]:
        """
        Retrieve memories that are relevant to the user's current conversation.
        
        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.

        Returns:
            List[str]: A list of memories sorted by relevance to the user's current conversation.
        """
        results = memory_service.emotional_intensity(query_str)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []

        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared: {text}")
            else:
                formatted.append(text)
        
        #print("formatted: ", formatted)
        return formatted
     
    @function_tool
    def context_weighted(query_str: str) -> List[str]:
        """
        Retrieve memories based on their relevance to the current conversation context.

        This tool surfaces memories that are relevant to the current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.

        Returns:
            List[str]: A list of memories sorted by relevance to the current conversation.
        """
        results = memory_service.context_weighted(query_str)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []  
        
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared: {text}")
            else:
                formatted.append(text)
        
        #print("formatted: ", formatted)
        return formatted

    @function_tool # DONE
    def mood_based_language(query_str: str, language_style: str) -> List[str]:
        """
        Retrieve memories based on the user's mood at the time of the memory.

        This tool surfaces memories that are relevant to the user's current mood, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            language_style (str): The language style to match against memory tags.
        Returns:
            List[str]: A list of memories sorted by relevance to the user's current mood.
        """
        results = memory_service.mood_based_language(query_str, language_style)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared: {text}")
            else:
                formatted.append(text)  
                
        # Search and summarize our last conversations where i had spoken in a direct way
        
        print("formatted: ", formatted)
        return formatted

    @function_tool
    def memory_surface(query_str: str) -> List[str]:
        """
        Retrieve memories that are relevant to the user's current conversation.

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.

        Returns:
            List[str]: A list of memories sorted by relevance to the user's current conversation.
        """
        results = memory_service.memory_surface(query_str)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025   
                formatted.append(f"On {human_date}, the user shared: {text}")
            else:
                formatted.append(text)
        
        # Search and summarize our last conversations where i displayed high memory surface
        
        print("formatted: ", formatted)
        return formatted

    @function_tool # DONE
    def rituals(query_str: str) -> List[str]:
        """
        Retrieve memories that are relevant to the user's current conversation.

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.

        Returns:
            List[str]: A list of memories sorted by relevance to the user's current conversation.
        """   
        results = memory_service.rituals(query_str)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []      
        
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared their rituals: {text}")
            else:
                formatted.append(text)
        
        # Search and summarize our last conversations where i displayed high rituals    
        
        #print("formatted: ", formatted)
        return formatted

    @function_tool # DONE
    def boundaries(query_str: str) -> List[str]:
        """
        Retrieve memories that are relevant to the user's current conversation.

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.

        Returns:
            List[str]: A list of memories sorted by relevance to the user's current conversation.
        """
        
        results = memory_service.boundaries(query_str)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared their boundaries: {text}")
            else:
                formatted.append(text)
        
        # Search and summarize our last conversations where i displayed high boundaries
        
        #print("formatted: ", formatted)
        return formatted

    @function_tool # DONE
    def self_awareness(query_str: str) -> List[str]:
        """
        Retrieve memories that are relevant to the user's current conversation. 

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.

        Returns:
            List[str]: A list of memories sorted by relevance to the user's current conversation.
        """
        results = memory_service.self_awareness(query_str)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared with high self awarness: {text}")
            else:
                formatted.append(text)
        
        # Search and summarize our last conversations where i displayed high self awarness
        
        #print("formatted: ", formatted)
        return formatted

    @function_tool # DONE
    def topics(query_str: str, topics: List[str]):
        """
        Retrieve memories that are relevant to the user's current conversation.
        
        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Includes a human readable date and time.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            topics (List[str]): A list of topics to filter memories by.

        Returns:
            List[str]: A list of knowledge texts from relevant memories.
        """
        results = memory_service.topics(query_str, topics)
        
        if not results:
            return ["No relevant memories found."]

        formatted = []
        for r in results:
            text = r["knowledge_text"] if isinstance(r, dict) else r.knowledge_text
            timestamp = r.get("metadata", {}).get("timestamp") or r.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                human_date = dt.strftime("%B %d, %Y")  # e.g., April 06, 2025
                formatted.append(f"On {human_date}, the user shared: {text}")
            else:
                formatted.append(text)
                    
        return formatted
        
        # search and summarize our last conversations about work and stress
        # search and summarize our last conversations about being happy. when was the last time I expressed this emotion
     
    return [
        emotional_intensity,
        context_weighted,
        mood_based_language,
        memory_surface,
        rituals,
        boundaries,
        self_awareness,
        topics,
    ]
