import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, AnyUrl
from typing import Optional
from app.utils.moderation import ModerationService

router = APIRouter()
moderation_service = ModerationService()

class ImageModerationRequest(BaseModel):
    image_url: HttpUrl

class ContentModerationRequest(BaseModel):
    text: Optional[str] = None
    image_url: Optional[AnyUrl] = None

class ModerationResponse(BaseModel):
    safe: bool
    reason: str


@router.post("/check-text")
async def check_text_content(text: str) -> ModerationResponse:
    """
    Check if text content is safe according to OpenAI's content policy.
    """
    try:
        moderation = moderation_service.check_content(text)

        if moderation is None:
            raise HTTPException(status_code=503, detail="Content moderation check failed. See server logs for details.")
            
        is_flagged = moderation["flagged"]
        reason_str = "Content appears safe." # Default reason
        if is_flagged:
            categories_dict = moderation.get('categories', {})
            flagged_categories = [cat for cat, flagged in categories_dict.items() if flagged]
            
            if flagged_categories:
                reason_str = f"Flagged for {', '.join(flagged_categories)}"
            else:
                reason_str = "Content flagged for unspecified reasons." # Fallback
            
        simpleResponse = ModerationResponse(safe=is_flagged,reason=reason_str)
        
        return simpleResponse
    except Exception as e:
        simpleResponse = ModerationResponse(safe=False,reason=str(e))
        return simpleResponse
    

@router.post("/check-image")
async def check_image_content(request: ImageModerationRequest) -> ModerationResponse:
    """
    Check if image content is safe according to OpenAI's content policy
    """
    try:
        moderation = moderation_service.check_image(request.image_url)

        if moderation is None:
            raise HTTPException(status_code=503, detail="Content moderation check failed. See server logs for details.")
            
        is_flagged = moderation["flagged"]
        reason_str = "Content appears safe." # Default reason
        if is_flagged:
            categories_dict = moderation.get('categories', {})
            flagged_categories = [cat for cat, flagged in categories_dict.items() if flagged]
            
            if flagged_categories:
                reason_str = f"Flagged for {', '.join(flagged_categories)}"
            else:
                reason_str = "Content flagged for unspecified reasons." # Fallback
            
        simpleResponse = ModerationResponse(safe=is_flagged,reason=reason_str)
        
        return simpleResponse
    except Exception as e:
        simpleResponse = ModerationResponse(safe=False,reason=str(e))
        return simpleResponse
    

@router.post("/is-safe")
async def is_safe(request: ContentModerationRequest) -> bool:
    """
    Check if text or image content is safe
    """
    try:
        is_safe = moderation_service.is_safe(request.text, request.image_url)
        return is_safe
    except Exception as e:
        raise HTTPException(status_code=503, detail="Content moderation check failed. See server logs for details.")


