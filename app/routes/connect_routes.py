import os
from typing import List
from agents import Agent, Runner
from fastapi import APIRouter, Depends
import requests
from pydantic import BaseModel
from app.auth import verify_token
from app.function.memory_extraction import MemoryExtractionService
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService
from app.supabase.knowledge_edges import get_connected_memories, pretty_print_memories
from app.supabase.profiles import ProfileRepository
from app.utils.geocode import reverse_geocode
from app.websockets.context.store import get_context

from app.mcp.mcp.memory.agent import memory_agent

# get connect server url from env
environment = os.getenv("ENV", "development")
development_url = os.getenv("CONNECT_SERVER_URL_DEV")
production_url = os.getenv("CONNECT_SERVER_URL_PROD")

connect_server_url = (
    development_url 
    if environment == "development"
    else production_url
)

print("Connect Server URL: ", connect_server_url)

# Initialize the router
router = APIRouter()

class SexualPreferences(BaseModel):
    orientation: str
    looking_for: str

class ConnectProfile(BaseModel):
    name: str
    age: int
    relationship_goals: str
    bio: str
    personality_tags: List[str]
    sexual_preferences: SexualPreferences
    location: str

profile_agent = Agent(
    name="Profile Agent",
    handoff_description="A profile agent that generates a user connect profile",
    instructions=f"""
    You are a profile agent that generates a user connect profile based on what you know about the user.
    Use the user's current location for the location field.

    Respond in UserProfile format:
        name: str - the user's name
        age: int - the user's age
        bio: str - a detailed bio of the user; including their hobbies, interests, and ambitions.
        relationship_goals: str - a description of the user's relationship goals and what they are looking in a romantic partner
        personality_tags: List[str] - a list of personality tags
        sexual_preferences: SexualPreferences:
            orientation: str - the user's gender: male, female, trans, bisexual, gay
            looking_for: str - what gender the user is looking for: male, female, trans, bisexual, gay
        location: str - the user's current location
    """,
    output_type=ConnectProfile
)

# generate a connect profile
@router.post("/generate_profile")
async def generate_connect_profile(user_id: str = Depends(verify_token)) -> ConnectProfile:
    """
    Creates a user profile with automatic generation of user ID, timestamps, and embedding vectors.
    """

    user_id = user_id["id"]

    print("User ID: ", user_id)


    # Initialize services
    profile_service = ProfileRepository()
    mbti_service = MBTIAnalysisService(user_id)
    ocean_service = OceanAnalysisService(user_id)
    memory_service = MemoryExtractionService(user_id)
    
    mbti_type = mbti_service.get_mbti_type()   
    ocean_traits = ocean_service.get_pretty_print_ocean_format()
    user_name = profile_service.get_user_name(user_id)

    # Get location from context
    context = get_context(user_id)
    location = context.get("gps")
    location_name = ""
    if location:
        location_name = await reverse_geocode(location['latitude'], location['longitude'])

    relationship_goals = memory_service.vector_search("What are the user's relationship goals and what they are looking for in a relationship?", limit=2)
    relationship_goals_context = get_connected_memories(user_id, relationship_goals[0]['id'])

    personality_desc = memory_service.vector_search("Describe the user's personality in detail?", limit=2)
    personality_desc_context = get_connected_memories(user_id, personality_desc[0]['id'])

    sexual_preferences = memory_service.vector_search("What are the user's gender oreintation and what gender are they interested in having a romantic relationship with?", limit=2)
    sexual_preferences_context = get_connected_memories(user_id, sexual_preferences[0]['id'])

    about_the_user = f"""
    Using the following information, generate a user profile for the user:

        User Name: {user_name}

        Relationship Goals: 
        {relationship_goals}
        {relationship_goals_context}

        Personality Description: 
        {personality_desc}
        {personality_desc_context}

        Sexual Preferences: 
        {sexual_preferences}
        {sexual_preferences_context}

        Location: {location_name}

        User's MBTI Type: {mbti_type}
        User's Ocean Traits: {ocean_traits}
    """
    
    print("About the User: ", about_the_user)
    
    response = await Runner.run(starting_agent=profile_agent, input=about_the_user)
    results = response.final_output

    print("Profile Agent Results: ", results)
    return results

# submit the profile to the connect server
@router.post("/create_profile")
async def submit_connect_profile(connect_profile: ConnectProfile, user_id=Depends(verify_token)):
    """
    Submits a user profile to the connect server
    """
    print("Submitting profile to connect server")
    user_id = user_id["id"]

    try:
        response = requests.post(
            url=f"{connect_server_url}/upsert_profile",
            json=connect_profile.model_dump(),
            params={"user_id": user_id}
        )
        return response.json()
    except Exception as e:
        print("Error submitting user profile: ", e)
        return {"error": "Failed to submit user profile"}
    
# remove the profile from the connect server
@router.delete("/remove_profile")
async def remove_connect_profile(user_id=Depends(verify_token)):
    """
    Removes a user profile from the connect server
    """
    user_id = user_id["id"]

    try:
        response = requests.delete(
            url=f"{connect_server_url}/delete_profile",
            params={"user_id": user_id}
        )
        return response.json()
    except Exception as e:
        print("Error removing user profile: ", e)
        return {"error": "Failed to remove user profile"}
