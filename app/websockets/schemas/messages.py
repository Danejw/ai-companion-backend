from pydantic import BaseModel
from typing import Literal, Union, Optional, Dict


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
    
class RawMessage(BaseModel):
    type: Literal["raw_mode"]
    is_raw: bool
    
# ORCHESTRATE
class OrchestrateMessage(BaseModel):
    type: Literal["orchestrate"]
    user_input: str
    extract: Optional[bool] = True
    summarize: Optional[int] = 10

# UNIFIED MESSAGE TYPE
Message = Union[TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage, UIActionMessage, RawMessage, OrchestrateMessage]
