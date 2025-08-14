# FILE: src/openai_rooms_pkg/configuration/baseconfig.py
from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseAddonConfig(BaseModel):
    """
    Common config for all addons (Pydantic v2 ONLY).
    The engine expects these common fields and allows extra keys.
    """
    id: str = Field(..., description="Unique identifier for the addon")
    type: str = Field(..., description="Addon type (e.g., llm, api, storage)")
    name: str = Field(..., description="Display name of the addon")
    description: Optional[str] = Field(None, description="Description of the addon")
    enabled: bool = Field(True, description="Whether the addon is enabled")

    # Free-form bags for extra runtime configuration and secret key references.
    config: Dict[str, Any] = Field(default_factory=dict, description="General configuration settings")
    secrets: Dict[str, str] = Field(default_factory=dict, description="Secret key references (to CredentialsRegistry)")

    # Pydantic v2 configuration (NO inner `Config` class!)
    model_config = ConfigDict(extra="allow", validate_assignment=True)
