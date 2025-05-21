from pydantic import BaseModel
from typing import Literal, Union, Optional, Dict

from app.function.improv_form_filler.form_orhestration import ImprovForm


# TEXT
class TextMessage(BaseModel):
    type: Literal["text"]
    text: str

# AUDIO
class AudioMessage(BaseModel):
    type: Literal["audio"]
    audio: str  # base64 encoded audio
    voice: Optional[str] = "alloy"

# IMAGE
class ImageMessage(BaseModel):
    type: Literal["image"]
    format: Literal["jpeg", "png"]
    data: list[str]  # base64 encoded image
    input: Optional[str] = "what's in this image?"

# LOCATION (GPS)
class GPSCoords(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    altitudeAccuracy: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None

class GPSMessage(BaseModel):
    type: Literal["gps"]
    coords: GPSCoords
    timestamp: Optional[float] = None

# TIME
class TimeMessage(BaseModel):
    type: Literal["time"]
    timestamp: str
    timezone: str

# UI ACTIONS
class UIActionMessage(BaseModel):
    type: Literal["ui_action"]
    action: str
    target: str
    params: Optional[Dict[str, str]]

# Personality Message
class PersonalityMessage(BaseModel):
    type: Literal["personality"]
    empathy: int
    directness: int
    warmth: int
    challenge: int

# LOCAL LINGO
class LocalLingoMessage(BaseModel):
    type: Literal["local_lingo"]
    local_lingo: bool

# FEEDBACK
class FeedbackMessage(BaseModel):
    type: Literal["feedback"]
    feedback_type: bool


# ORCHESTRATE
class OrchestrateMessage(BaseModel):
    type: Literal["orchestrate"]
    user_input: str
    extract: Optional[bool] = True
    summarize: Optional[int] = 10

# IMPROV
class ImprovMessage(BaseModel):
    type: Literal["improv"]
    improv_form_name: str
    user_input: Optional[str] = None

# UNIFIED MESSAGE TYPE
Message = Union[TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage, UIActionMessage, PersonalityMessage, LocalLingoMessage, FeedbackMessage, OrchestrateMessage, ImprovMessage]
