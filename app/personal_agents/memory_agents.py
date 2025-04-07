








from typing import List
from agents import Agent, function_tool

from app.function.memory_extraction import MemoryResponse, MemoryVector
from app.function.memory_extraction import MemoryExtractionService



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

def create_memory_tools(user_id: str):
    memory_service = MemoryExtractionService(user_id)
       
    @function_tool
    def emotional_momentum(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve the most recent memories related to the current conversation.

        This tool surfaces the latest relevant entries based on time, helping the AI 
        stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of recent memories sorted from newest to oldest.
        """
        return memory_service.emotional_momentum(query_str, limit)


    @function_tool
    def context_weighted(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories based on their relevance to the current conversation context.

        This tool surfaces memories that are relevant to the current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the current conversation.
        """
        return memory_service.context_weighted(query_str, limit)


    @function_tool
    def mood_based_language(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories based on the user's mood at the time of the memory.

        This tool surfaces memories that are relevant to the user's current mood, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.      

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current mood.
        """
        return memory_service.mood_based_language(query_str, limit)


    @function_tool
    def memory_surface(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories that are relevant to the user's current conversation.

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.  

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        return memory_service.memory_surface(query_str, limit)


    @function_tool
    def rituals(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories that are relevant to the user's current conversation.

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        return memory_service.rituals(query_str, limit)


    @function_tool
    def boundaries(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories that are relevant to the user's current conversation.

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.  

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        return memory_service.boundaries(query_str, limit)


    @function_tool
    def self_awareness(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories that are relevant to the user's current conversation. 

        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.  

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        return memory_service.self_awareness(query_str, limit)


    @function_tool
    def emotional_intensity(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve memories that are relevant to the user's current conversation.
        
        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        return memory_service.emotional_intensity(query_str, limit)


    @function_tool
    def get_latest_messages(query_str: str, limit: int = 10) -> List[MemoryResponse]:
        """
        Retrieve the most recent memories related to the current conversation.
        
        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        return memory_service.get_latest_messages(query_str, limit)


    @function_tool
    def topics(query_str: str, topics: List[str], limit: int = 3) -> str:
        """
        Retrieve memories that are relevant to the user's current conversation.
        
        This tool surfaces memories that are relevant to the user's current conversation, 
        helping the AI stay connected to what the user has been thinking or feeling lately.
        
        Args:
            query_str (str): A message or idea from the user to semantically match.
            topics (List[str]): A list of topics to filter memories by.
            limit (int): Maximum number of memory items to return. Defaults to 10.

        Returns:
            List[MemoryResponse]: A list of memories sorted by relevance to the user's current conversation.
        """
        results = memory_service.topics(query_str, topics, limit)
        
        
        # get all the text from the results
        result_text = "\n".join([result.text for result in results])
        
        print("result_text: ", result_text)
        
        return result_text

    return [
        # emotional_intensity,
        # context_weighted,
        # mood_based_language,
        # memory_surface,
        # rituals,
        # boundaries,
        # self_awareness,
        # get_latest_messages,
        topics,
    ]


agent = Agent(
    name="MemoryExtractor",
    handoff_description="An agent that extracts valuable information about the user from your interactions and stores it in a vector database.",
    instructions=instructions,
    model="gpt-4o-mini",
    #output_type=MemoryVector,
)






