from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel

@dataclass
class Message:
    role: str
    content: str

@dataclass
class RequiredField:
    name: str
    type: type
    description: str = ""

@dataclass
class ImprovForm:
    name: str
    required_fields: list[RequiredField]
    theme: Optional[str] = None
    intro: Optional[str] = None
    outro: Optional[str] = None

class ExtractedField(BaseModel):
    name: str
    value: str

class ExtractionResults(BaseModel):
    did_extract: bool
    extracted_fields: List[ExtractedField]
