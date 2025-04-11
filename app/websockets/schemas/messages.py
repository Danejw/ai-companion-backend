from pydantic import BaseModel
from typing import Literal, Union, Optional, Dict


# TEXT
class TextMessage(BaseModel):
    type: Literal["text"]
    text: str
    extract: Optional[bool] = True
    summarize: Optional[int] = 10

# AUDIO
class AudioMessage(BaseModel):
    type: Literal["audio"]
    audio: str  # base64 encoded audio
    voice: Optional[str] = "alloy"
    extract: Optional[bool] = True
    summarize: Optional[int] = 10

# IMAGE
class ImageMessage(BaseModel):
    type: Literal["image"]
    format: Literal["jpeg", "png"]
    data: str  # base64 encoded image

# LOCATION (GPS)
class GPSMessage(BaseModel):
    type: Literal["gps"]
    latitude: float
    longitude: float
    accuracy: Optional[float]

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
    
# ORCHESTRATE
class OrchestrateMessage(BaseModel):
    type: Literal["orchestrate"]
    user_input: str

# UNIFIED MESSAGE TYPE
Message = Union[TextMessage, AudioMessage, ImageMessage, GPSMessage, TimeMessage, UIActionMessage, OrchestrateMessage]
