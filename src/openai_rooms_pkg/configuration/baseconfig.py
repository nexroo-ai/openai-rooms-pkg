from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class BaseAddonConfig(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True

    # champs courants
    model: Optional[str] = None
    model_default: Optional[str] = None
    api_base: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    request_timeout: int = 60
    max_retries: int = 2

    # secrets & misc
    secrets: Dict[str, Any] = Field(default_factory=dict)
    organization: Optional[str] = None
    project: Optional[str] = None
    proxies: Optional[Dict[str, str]] = None

    # defaults pour autres actions éventuelles
    image_size_default: str = "1024x1024"
    audio_format_default: str = "mp3"
    package: Optional[str] = None
