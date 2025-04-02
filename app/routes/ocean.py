from app.auth import verify_token
from app.supabase.supabase_ocean import Ocean
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from app.psychology.ocean_analysis import OceanAnalysisService


router = APIRouter()


class OceanRequest(BaseModel):
    message: str
    
class OceanUpdateRequest(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    
    

@router.post("/ocean-analyze")
async def ocean_analyze(data: OceanRequest, user=Depends(verify_token)):
    message = data.message
    user_id = user["id"]

    # Create a new analysis service for this user
    service = OceanAnalysisService(user_id)
    # Perform the analysis
    await service.analyze_message(message)

    # Get personality traits
    traits = service.get_personality_traits()

    return {
        "personality_traits": traits,
        "raw_scores": service.ocean.dict()
    }


@router.get("/get-ocean")
async def get_ocean(user=Depends(verify_token)) -> Ocean:
    user_id = user["id"]
    service = OceanAnalysisService(user_id)
    ocean_data = service.repository.get_ocean(user_id)
    
    if ocean_data:
        return ocean_data
    else:
        return {"error": "No OCEAN data found for this user"}
    

@router.post("/ocean-update")
async def update_ocean(data: OceanUpdateRequest, user=Depends(verify_token)):
    """
    Updates the OCEAN data for a given user in Supabase,
    applying the rolling average before saving.
    """
    user_id = user["id"]

    # Initialize the OCEAN Analysis Service
    service = OceanAnalysisService(user_id)

    # Construct a new Ocean object with the incoming data
    new_ocean = Ocean(
        openness=data.openness,
        conscientiousness=data.conscientiousness,
        extraversion=data.extraversion,
        agreeableness=data.agreeableness,
        neuroticism=data.neuroticism,
        response_count=1  # This will be updated in the rolling average function
    )

    # Apply rolling average update
    service._update_ocean_rolling_average(new_ocean)

    # Save the updated OCEAN data to Supabase
    service.save_ocean()

    return {
        "message": "OCEAN data updated successfully",
        "ocean": service.ocean.dict()
    }
    

@router.get("/ocean-traits")
async def get_ocean_traits(user=Depends(verify_token)):
    user_id = user["id"]
    service = OceanAnalysisService(user_id)
    traits = service.get_personality_traits()
    return {
        "personality_traits": traits,
        "raw_scores": service.ocean.dict()
    }


