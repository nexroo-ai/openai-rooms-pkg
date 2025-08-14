# FILE: src/openai_rooms_pkg/actions/audio_transcribe.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import base64
import io
import mimetypes
import os
import time

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from openai_rooms_pkg.actions.base import ActionResponse, OutputBase, TokensSchema
from ..configuration import CustomAddonConfig
from ..services.credentials import CredentialsRegistry


class ActionInput(BaseModel):
    audio: str = Field(..., description="Local path, http(s) URL, or base64 (optionally data URI)")
    model: Optional[str] = Field(default="whisper-1")
    language: Optional[str] = Field(default=None)
    prompt: Optional[str] = Field(default=None)
    temperature: Optional[float] = Field(default=None)


class ActionOutput(OutputBase):
    result: str
    segments: Optional[List[Dict[str, Any]]] = None
    model: str


def _build_headers(cfg: CustomAddonConfig, creds: CredentialsRegistry) -> Dict[str, str]:
    api_key_name = cfg.secrets.get("api_key", "")
    api_key_val = creds.get(api_key_name)
    if not api_key_val:
        raise ValueError("OpenAI api_key not found in CredentialsRegistry.")
    headers = {
        "Authorization": f"Bearer {api_key_val}",
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


def _read_audio_bytes(src: str, timeout: int, proxies: Optional[dict]) -> bytes:
    if src.startswith("http://") or src.startswith("https://"):
        with httpx.Client(timeout=timeout, proxies=proxies) as client:
            r = client.get(src)
            r.raise_for_status()
            return r.content
    # data URI?
    if src.startswith("data:"):
        header, b64data = src.split(",", 1)
        return base64.b64decode(b64data)
    # plain base64?
    try:
        # Try to decode as base64; if invalid, will raise
        return base64.b64decode(src, validate=True)
    except Exception:
        pass
    # local file path
    if os.path.isfile(src):
        with open(src, "rb") as f:
            return f.read()
    raise ValueError(
        "audio_transcribe: could not read audio source; provide a valid URL, base64, data URI, or file path."
    )


def audio_transcribe(config: CustomAddonConfig, action_input: ActionInput) -> ActionResponse:
    logger.debug("audio_transcribe: starting with inputs")
    logger.debug(
        f"audio source len={len(action_input.audio)}, model={action_input.model}, language={action_input.language}"
    )

    credentials = CredentialsRegistry()
    try:
        headers = _build_headers(config, credentials)
        redacted_headers = {**headers, "Authorization": "Bearer ****"}
        logger.debug(f"audio_transcribe: headers={redacted_headers}")

        base_url = (config.api_base or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/audio/transcriptions"

        audio_bytes = _read_audio_bytes(action_input.audio, config.request_timeout, config.proxies)
        # Guess a filename & mime
        guessed_ext = mimetypes.guess_extension(mimetypes.guess_type("file.mp3")[0] or "audio/mpeg") or ".mp3"
        file_name = f"audio{guessed_ext}"

        files = {
            "file": (file_name, io.BytesIO(audio_bytes), mimetypes.guess_type(file_name)[0] or "application/octet-stream"),
            "model": (None, action_input.model or "whisper-1"),
            "response_format": (None, "verbose_json"),
        }
        if action_input.language:
            files["language"] = (None, action_input.language)
        if action_input.prompt:
            files["prompt"] = (None, action_input.prompt)
        if action_input.temperature is not None:
            files["temperature"] = (None, str(action_input.temperature))

        logger.debug(f"audio_transcribe: POST {url}")
        max_attempts = max(1, config.max_retries + 1)
        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=config.request_timeout, proxies=config.proxies) as client:
                    resp = client.post(url, headers=headers, files=files)
                status = resp.status_code
                logger.debug(f"audio_transcribe: status_code={status}")
                if status >= 400:
                    if status == 429 or 500 <= status < 600:
                        if attempt < max_attempts - 1:
                            time.sleep(0.8 * (2 ** attempt))
                            continue
                    output = ActionOutput(result="", segments=None, model=action_input.model or "whisper-1")
                    return ActionResponse(
                        output=output,
                        tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                        message=f"OpenAI error {status}: {resp.text}",
                        code=429 if status == 429 else (502 if 500 <= status < 600 else 400),
                    )

                data = resp.json()
                text = data.get("text", "")
                segments = data.get("segments")
                output = ActionOutput(result=text, segments=segments, model=action_input.model or "whisper-1")
                tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
                return ActionResponse(output=output, tokens=tokens, message="ok", code=200)
            except httpx.RequestError as e:
                if attempt < max_attempts - 1:
                    time.sleep(0.8 * (2 ** attempt))
                    continue
                output = ActionOutput(result="", segments=None, model=action_input.model or "whisper-1")
                return ActionResponse(
                    output=output,
                    tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                    message=f"Request error: {e}",
                    code=502,
                )
    except Exception as e:
        logger.debug(f"audio_transcribe: exception {e}")
        output = ActionOutput(result="", segments=None, model=action_input.model or "whisper-1")
        return ActionResponse(
            output=output,
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=str(e),
            code=400,
        )
