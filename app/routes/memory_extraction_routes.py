from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import verify_token
from app.personal_agents.memory_extraction import MemoryExtractionService, MemoryResponse, MemoryVector
from app.supabase.conversation_history import Message

router = APIRouter()

class MemoryRequest(BaseModel):
    history: list[Message]

#TODO: Make routes protected to only allow authenticated users

@router.post("/extract-memory", response_model=MemoryVector)
async def extract_memory(user_id:str, request: str): #, user=Depends(verify_token)) -> MemoryVector:
    """
    Extracts memories from the given message
    """
    #user_id = user["id"]
    #history = request.history
    
    # # Filter to get only messages from this user
    # user_messages = [msg for msg in history if msg.user_id == user_id]
    
    # # Convert the history to a string
    # history_string = "\n".join([f"{msg.role}: {msg.content}" for msg in user_messages])
    
    # Instantiate the MemoryExtractionService   
    memory_service = MemoryExtractionService(user_id)
    
    # Extract memories from the message
    memories = await memory_service.extract_memory(request)
    
    return memories


@router.post("/store-memory", response_model=bool)
def store_memory(user_id:str, request: MemoryVector): #, user=Depends(verify_token)):
    """
    Stores memories from the given message and stores them if valuable.
    """
    #user_id = user["id"]

    
    # Instantiate the MemoryExtractionService   
    memory_service = MemoryExtractionService(user_id)
    
    # Extract memories from the message
    memories = memory_service.store_memory(request)
    
    return {"message": "Memory stored successfully."} if memories else {"message": "No valuable memories extracted."}



@router.post("/get-latest-messages")
def get_latest_messages(user_id:str, request: str):
    """
    Retrieves the latest messages from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.get_latest_messages(request)
    return memories


@router.post("/emotional-momentum")
def emotional_momentum(user_id:str, request: str):
    """
    Retrieves emotional momentum memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.emotional_momentum(request)
    return memories


@router.post("/context-weighted")
def context_weighted(user_id:str, request: str):
    """
    Retrieves context-weighted memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.context_weighted(request)
    return memories


@router.post("/mood-based-language")
def mood_based_language(user_id:str, request: str):
    """
    Retrieves mood-based language memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.mood_based_language(request)
    return memories


@router.post("/memory-surface")
def memory_surface(user_id:str, request: str):
    """
    Retrieves memory surface memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.memory_surface(request)
    return memories


@router.post("/rituals")
def rituals(user_id:str, request: str):
    """
    Retrieves rituals memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.rituals(request)
    return memories


@router.post("/boundaries")
def boundaries(user_id:str, request: str):
    """
    Retrieves boundaries memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.boundaries(request)
    return memories


@router.post("/self-awareness")
def self_awareness(user_id:str, request: str):
    """
    Retrieves self-awareness memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.self_awareness(request)
    return memories 


@router.post("/emotional-intensity")
def emotional_intensity(user_id:str, request: str):
    """
    Retrieves emotional intensity memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.emotional_intensity(request)
    return memories

@router.post("/topics")
def topics(user_id:str, request: str):
    """
    Retrieves topics memories from the given message.
    """
    memory_service = MemoryExtractionService(user_id)
    memories = memory_service.topics(request)
    return memories
