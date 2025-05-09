from dataclasses import dataclass
from typing import Optional

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
