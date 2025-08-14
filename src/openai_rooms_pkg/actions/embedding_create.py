# FILE: src/openai_rooms_pkg/actions/embedding_create.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import time

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from openai_rooms_pkg.actions.base import ActionResponse, OutputBase, TokensSchema
from ..configuration import CustomAddonConfig
from ..services.credentials import CredentialsRegistry


class ActionInput(BaseModel):
    input: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    model: Optional[str] = Field(default=None, description="e.g. text-embedding-3-small/large")
    dimensions: Optional[int] = Field(default=None, description="Optional custom dimensions")


class ActionOutput(OutputBase):
    result: str
    vectors: List[List[float]]
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


def embedding_create(config: CustomAddonConfig, action_input: ActionInput) -> ActionResponse:
    logger.debug("embedding_create: starting with inputs")
    length = len(action_input.input) if isinstance(action_input.input, list) else 1
    logger.debug(f"inputs={length}, model={action_input.model}")

    credentials = CredentialsRegistry()
    try:
        headers = _build_headers(config, credentials)
        redacted_headers = {**headers, "Authorization": "Bearer ****"}
        logger.debug(f"embedding_create: headers={redacted_headers}")

        base_url = (config.api_base or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/embeddings"

        payload: Dict[str, Any] = {
            "model": action_input.model or "text-embedding-3-small",
            "input": action_input.input,
        }
        if action_input.dimensions is not None:
            payload["dimensions"] = action_input.dimensions

        logger.debug(f"embedding_create: POST {url}")
        max_attempts = max(1, config.max_retries + 1)
        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=config.request_timeout, proxies=config.proxies) as client:
                    resp = client.post(url, headers=headers, json=payload)
                status = resp.status_code
                logger.debug(f"embedding_create: status_code={status}")
                if status >= 400:
                    if status == 429 or 500 <= status < 600:
                        if attempt < max_attempts - 1:
                            time.sleep(0.8 * (2 ** attempt))
                            continue
                    output = ActionOutput(result="", vectors=[], model=payload["model"])
                    return ActionResponse(
                        output=output,
                        tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                        message=f"OpenAI error {status}: {resp.text}",
                        code=429 if status == 429 else (502 if 500 <= status < 600 else 400),
                    )

                data = resp.json()
                vectors: List[List[float]] = []
                for item in data.get("data", []):
                    emb = item.get("embedding")
                    if isinstance(emb, list):
                        vectors.append(emb)
                msg = f"{len(vectors)} vectors generated"
                output = ActionOutput(result=msg, vectors=vectors, model=payload["model"])
                tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
                return ActionResponse(output=output, tokens=tokens, message="ok", code=200)
            except httpx.RequestError as e:
                if attempt < max_attempts - 1:
                    time.sleep(0.8 * (2 ** attempt))
                    continue
                output = ActionOutput(result="", vectors=[], model=payload["model"])
                return ActionResponse(
                    output=output,
                    tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                    message=f"Request error: {e}",
                    code=502,
                )
    except Exception as e:
        logger.debug(f"embedding_create: exception {e}")
        output = ActionOutput(result="", vectors=[], model=action_input.model or "text-embedding-3-small")
        return ActionResponse(
            output=output,
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=str(e),
            code=400,
        )
