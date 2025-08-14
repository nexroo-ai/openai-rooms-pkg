# FILE: src/openai_rooms_pkg/actions/chat_complete.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import time

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from openai_rooms_pkg.actions.base import ActionResponse, OutputBase, TokensSchema
from openai_rooms_pkg.configuration import CustomAddonConfig
from openai_rooms_pkg.services.credentials import CredentialsRegistry


class ActionInput(BaseModel):
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages in OpenAI format (role/content)")
    model: Optional[str] = Field(default=None)
    temperature: Optional[float] = Field(default=0.7)
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[List[str], str]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    seed: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ActionOutput(OutputBase):
    result: str
    raw: Optional[Dict[str, Any]] = None
    model: str
    usage: Optional[Dict[str, Any]] = None


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


def chat_complete(config: CustomAddonConfig, action_input: ActionInput) -> ActionResponse:
    logger.debug("chat_complete: starting with inputs")
    logger.debug(
        f"messages count={len(action_input.messages)}, model={action_input.model or config.model_default}, "
        f"temperature={action_input.temperature}, max_tokens={action_input.max_tokens}"
    )

    credentials = CredentialsRegistry()
    try:
        headers = _build_headers(config, credentials)
        redacted_headers = {**headers, "Authorization": "Bearer ****"}
        logger.debug(f"chat_complete: headers={redacted_headers}")

        base_url = (config.api_base or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        payload: Dict[str, Any] = {
            "model": action_input.model or config.model_default,
            "messages": action_input.messages,
            "temperature": action_input.temperature,
        }
        if action_input.top_p is not None:
            payload["top_p"] = action_input.top_p
        if action_input.max_tokens is not None:
            payload["max_tokens"] = action_input.max_tokens
        if action_input.stop is not None:
            payload["stop"] = action_input.stop
        if action_input.presence_penalty is not None:
            payload["presence_penalty"] = action_input.presence_penalty
        if action_input.frequency_penalty is not None:
            payload["frequency_penalty"] = action_input.frequency_penalty
        if action_input.seed is not None:
            payload["seed"] = action_input.seed
        if action_input.metadata is not None:
            payload["metadata"] = action_input.metadata

        logger.debug(f"chat_complete: POST {url}")
        max_attempts = max(1, config.max_retries + 1)
        last_err_msg = None
        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=config.request_timeout, proxies=config.proxies) as client:
                    resp = client.post(url, headers=headers, json=payload)
                status = resp.status_code
                logger.debug(f"chat_complete: status_code={status}")
                if status >= 400:
                    if status == 429 or 500 <= status < 600:
                        last_err_msg = resp.text
                        if attempt < max_attempts - 1:
                            time.sleep(0.8 * (2 ** attempt))
                            continue
                    output = ActionOutput(result="", raw=None, model=payload.get("model") or "", usage=None)
                    return ActionResponse(
                        output=output,
                        tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                        message=f"OpenAI error {status}: {resp.text}",
                        code=429 if status == 429 else (502 if 500 <= status < 600 else 400),
                    )

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
                usage = data.get("usage")
                step_tokens = 0
                if isinstance(usage, dict):
                    step_tokens = usage.get("total_tokens") or (
                        (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0)
                    ) or 0

                output = ActionOutput(
                    result=content,
                    raw=data,
                    model=data.get("model") or payload.get("model") or "",
                    usage=usage,
                )
                tokens = TokensSchema(stepAmount=int(step_tokens), totalCurrentAmount=int(step_tokens))
                return ActionResponse(output=output, tokens=tokens, message="ok", code=200)
            except httpx.RequestError as e:
                last_err_msg = str(e)
                logger.debug(f"chat_complete: request error on attempt {attempt+1}: {last_err_msg}")
                if attempt < max_attempts - 1:
                    time.sleep(0.8 * (2 ** attempt))
                    continue
                output = ActionOutput(result="", raw=None, model=payload.get("model") or "", usage=None)
                return ActionResponse(
                    output=output,
                    tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                    message=f"Request error: {last_err_msg}",
                    code=502,
                )
    except Exception as e:
        logger.debug(f"chat_complete: exception {e}")
        output = ActionOutput(result="", raw=None, model=action_input.model or (config.model_default or ""), usage=None)
        return ActionResponse(
            output=output,
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=str(e),
            code=400,
        )
