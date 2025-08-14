# FILE: src/openai_rooms_pkg/actions/audio_tts.py
from __future__ import annotations

from typing import Any, Dict, Optional
import base64
import time

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from openai_rooms_pkg.actions.base import ActionResponse, OutputBase, TokensSchema
from ..configuration import CustomAddonConfig
from ..services.credentials import CredentialsRegistry


class ActionInput(BaseModel):
    text: str = Field(..., min_length=1)
    model: Optional[str] = Field(default="gpt-4o-mini-tts")
    voice: Optional[str] = Field(default="alloy")
    format: Optional[str] = Field(default=None, description="mp3|wav|flac etc.")
    speed: Optional[float] = Field(default=1.0)


class ActionOutput(OutputBase):
    result: str
    audio_b64: str
    model: str


def _build_headers(cfg: CustomAddonConfig, creds: CredentialsRegistry) -> Dict[str, str]:
    api_key_name = cfg.secrets.get("api_key", "")
    api_key_val = creds.get(api_key_name)
    if not api_key_val:
        raise ValueError("OpenAI api_key not found in CredentialsRegistry.")
    headers = {
        "Authorization": f"Bearer {api_key_val}",
        "Content-Type": "application/json",
    }
    org_key = cfg.secrets.get("organization_key")
    proj_key = cfg.secrets.get("project_key")
    org = cfg.organization or (creds.get(org_key) if org_key else None)
    proj = cfg.project or (creds.get(proj_key) if proj_key else None)
    if org:
        headers["OpenAI-Organization"] = org
    if proj:
        headers["OpenAI-Project"] = proj
    return headers


def audio_tts(config: CustomAddonConfig, action_input: ActionInput) -> ActionResponse:
    logger.debug("audio_tts: starting with inputs")
    logger.debug(
        f"len(text)={len(action_input.text)}, model={action_input.model}, format={action_input.format}, speed={action_input.speed}"
    )

    credentials = CredentialsRegistry()
    try:
        headers = _build_headers(config, credentials)
        redacted_headers = {**headers, "Authorization": "Bearer ****"}
        logger.debug(f"audio_tts: headers={redacted_headers}")

        base_url = (config.api_base or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/audio/speech"

        payload: Dict[str, Any] = {
            "model": action_input.model or "gpt-4o-mini-tts",
            "voice": action_input.voice or "alloy",
            "input": action_input.text,
        }
        fmt = action_input.format or config.audio_format_default
        if fmt:
            payload["format"] = fmt
        if action_input.speed is not None:
            payload["speed"] = action_input.speed

        logger.debug(f"audio_tts: POST {url}")
        max_attempts = max(1, config.max_retries + 1)
        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=config.request_timeout, proxies=config.proxies) as client:
                    resp = client.post(url, headers=headers, json=payload)
                status = resp.status_code
                logger.debug(f"audio_tts: status_code={status}")
                if status >= 400:
                    if status == 429 or 500 <= status < 600:
                        if attempt < max_attempts - 1:
                            time.sleep(0.8 * (2 ** attempt))
                            continue
                    output = ActionOutput(result="", audio_b64="", model=payload["model"])
                    return ActionResponse(
                        output=output,
                        tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                        message=f"OpenAI error {status}: {resp.text}",
                        code=429 if status == 429 else (502 if 500 <= status < 600 else 400),
                    )

                # Binary audio bytes
                audio_bytes = resp.content
                b64 = base64.b64encode(audio_bytes).decode("utf-8")
                output = ActionOutput(result="audio generated", audio_b64=b64, model=payload["model"])
                tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
                return ActionResponse(output=output, tokens=tokens, message="ok", code=200)
            except httpx.RequestError as e:
                if attempt < max_attempts - 1:
                    time.sleep(0.8 * (2 ** attempt))
                    continue
                output = ActionOutput(result="", audio_b64="", model=payload["model"])
                return ActionResponse(
                    output=output,
                    tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                    message=f"Request error: {e}",
                    code=502,
                )
    except Exception as e:
        logger.debug(f"audio_tts: exception {e}")
        output = ActionOutput(result="", audio_b64="", model=action_input.model or "gpt-4o-mini-tts")
        return ActionResponse(
            output=output,
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=str(e),
            code=400,
        )
