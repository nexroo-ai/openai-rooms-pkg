# FILE: src/openai_rooms_pkg/configuration/addonconfig.py
from __future__ import annotations

from typing import Dict, Optional
from pydantic import Field, HttpUrl, model_validator

from .baseconfig import BaseAddonConfig


class CustomAddonConfig(BaseAddonConfig):
    """
    OpenAI addon configuration compatible with the engine & working Anthropic addon style.
    Accepts either `model` or legacy `model_default` from previous specs.
    """
    # Fixed addon type (engine uses this for classification)
    type: str = Field("llm", description="Addon category (fixed)")

    # Model settings
    model: Optional[str] = Field(default=None, description="Model to use (e.g., gpt-4.1-mini, o4-mini)")
    model_default: Optional[str] = Field(default=None, description="(Legacy) Default model if `model` not set")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Max tokens for generation")

    # API / HTTP settings
    api_base: Optional[HttpUrl] = Field(default=None, description="OpenAI API base URL (e.g., https://api.openai.com/v1)")
    organization: Optional[str] = Field(default=None, description="Optional OpenAI organization header value")
    project: Optional[str] = Field(default=None, description="Optional OpenAI project header value")
    request_timeout: int = Field(60, gt=0, description="HTTP timeout in seconds")
    max_retries: int = Field(2, ge=0, description="Max retry attempts on 429/5xx")
    proxies: Optional[Dict[str, str]] = Field(default=None, description="Optional httpx proxies mapping")

    # Media defaults
    image_size_default: str = Field("1024x1024", description="Default image generation size")
    audio_format_default: str = Field("mp3", description="Default TTS audio format")

    @model_validator(mode="after")
    def harmonize_and_validate(self):
        # Ensure `model` is set (accept legacy model_default)
        if not self.model and self.model_default:
            self.model = self.model_default

        # Validate required secret reference
        required = ["api_key"]
        missing = [k for k in required if k not in self.secrets]
        if missing:
            raise ValueError(f"Missing OpenAI secrets: {missing}. Expected `secrets.api_key` to be a registry key.")

        # request_timeout/max_retries already constrained by Field; just be explicit if needed
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be > 0")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        return self
