# FILE: src/openai_rooms_pkg/actions/image_generate.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import time

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from openai_rooms_pkg.actions.base import ActionResponse, OutputBase, TokensSchema
from ..configuration import CustomAddonConfig
from ..services.credentials import CredentialsRegistry


class ActionInput(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = Field(default=None, description="e.g. gpt-image-1")
    size: Optional[str] = None
    quality: Optional[str] = None  # "standard" | "hd"
    n: Optional[int] = Field(default=1, ge=1, le=10)
    style: Optional[str] = None
    background: Optional[str] = None  # e.g., "transparent"


class ActionOutput(OutputBase):
    result: str
    images: List[Dict[str, Any]]
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


def image_generate(config: CustomAddonConfig, action_input: ActionInput) -> ActionResponse:
    logger.debug("image_generate: starting with inputs")
    logger.debug(
        f"prompt_len={len(action_input.prompt)}, size={action_input.size or config.image_size_default}, "
        f"n={action_input.n}, model={action_input.model}"
    )

    credentials = CredentialsRegistry()
    try:
        headers = _build_headers(config, credentials)
        redacted_headers = {**headers, "Authorization": "Bearer ****"}
        logger.debug(f"image_generate: headers={redacted_headers}")

        base_url = (config.api_base or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/images/generations"

        payload: Dict[str, Any] = {
            "prompt": action_input.prompt,
            "model": action_input.model or "gpt-image-1",
            "n": action_input.n or 1,
            "size": action_input.size or config.image_size_default,
        }
        if action_input.quality:
            payload["quality"] = action_input.quality
        if action_input.style:
            payload["style"] = action_input.style
        if action_input.background:
            payload["background"] = action_input.background

        logger.debug(f"image_generate: POST {url}")
        max_attempts = max(1, config.max_retries + 1)
        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=config.request_timeout, proxies=config.proxies) as client:
                    resp = client.post(url, headers=headers, json=payload)
                status = resp.status_code
                logger.debug(f"image_generate: status_code={status}")
                if status >= 400:
                    if status == 429 or 500 <= status < 600:
                        if attempt < max_attempts - 1:
                            time.sleep(0.8 * (2 ** attempt))
                            continue
                    output = ActionOutput(result="", images=[], model=payload["model"])
                    return ActionResponse(
                        output=output,
                        tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                        message=f"OpenAI error {status}: {resp.text}",
                        code=429 if status == 429 else (502 if 500 <= status < 600 else 400),
                    )

                data = resp.json()
                items = data.get("data", []) or []
                images: List[Dict[str, Any]] = []
                for it in items:
                    # keep either url or b64_json
                    if "url" in it:
                        images.append({"url": it["url"]})
                    elif "b64_json" in it:
                        images.append({"b64_json": it["b64_json"]})
                msg = f"{len(images)} images generated"
                output = ActionOutput(result=msg, images=images, model=payload["model"])
                tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
                return ActionResponse(output=output, tokens=tokens, message="ok", code=200)
            except httpx.RequestError as e:
                if attempt < max_attempts - 1:
                    time.sleep(0.8 * (2 ** attempt))
                    continue
                output = ActionOutput(result="", images=[], model=payload["model"])
                return ActionResponse(
                    output=output,
                    tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                    message=f"Request error: {e}",
                    code=502,
                )
    except Exception as e:
        logger.debug(f"image_generate: exception {e}")
        output = ActionOutput(result="", images=[], model=action_input.model or "gpt-image-1")
        return ActionResponse(
            output=output,
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=str(e),
            code=400,
        )
