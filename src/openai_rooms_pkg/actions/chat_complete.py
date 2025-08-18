# FILE: src/openai_rooms_pkg/actions/chat_completion.py
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

__all__ = ["chat_completion"]


def _cfg_get(cfg: Any, key: str, default: Any = None):
    """Accès clé-valeure tolérant (Pydantic model OU dict)."""
    if cfg is None:
        return default
    # Pydantic model -> attribut
    if hasattr(cfg, key):
        try:
            val = getattr(cfg, key)
            return default if val is None else val
        except Exception:
            pass
    # dict-like
    if isinstance(cfg, dict):
        return cfg.get(key, default)
    return default


def _cfg_get_nested(cfg: Any, *keys, default=None):
    cur = cfg
    for k in keys:
        if cur is None:
            return default
        if hasattr(cur, k):
            cur = getattr(cur, k)
        elif isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return default
    return default if cur is None else cur


def _build_headers(api_key: str, project: Optional[str], organization: Optional[str]) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if api_key.startswith("sk-proj-"):
        proj = project or os.getenv("OPENAI_PROJECT")
        if proj:
            headers["OpenAI-Project"] = proj
    if organization:
        headers["OpenAI-Organization"] = organization
    return headers


def _normalize_messages(
    messages: Optional[List[Dict[str, str]]],
    system: Optional[str],
    user_message: Optional[str],
) -> List[Dict[str, str]]:
    if messages and isinstance(messages, list):
        return messages
    built: List[Dict[str, str]] = []
    if system:
        built.append({"role": "system", "content": system})
    if user_message:
        built.append({"role": "user", "content": user_message})
    return built


def chat_completion(
    config: Any,
    *,
    # deux styles d'entrée
    messages: Optional[List[Dict[str, str]]] = None,
    system: Optional[str] = None,
    message: Optional[str] = None,
    # options
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    # sources alternatives de clé
    api_key: Optional[str] = None,
    # compat no-op
    tools: Optional[Dict[str, Any]] = None,
    tool_registry: Optional[Any] = None,
    observer_callback: Optional[Any] = None,
    addon_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Implémentation simple style Anthropic mais pour OpenAI (/v1/chat/completions).
    Supporte:
      - messages=[...]
      - system + message
    Fonctionne avec config Pydantic OU dict.
    """

    model = _cfg_get(config, "model") or _cfg_get(config, "model_default") or "gpt-4o-mini"
    temperature = float(temperature if temperature is not None else _cfg_get(config, "temperature", 0.7))
    mt_from_cfg = _cfg_get(config, "max_tokens")
    max_tokens = int(max_tokens if max_tokens is not None else (mt_from_cfg or 0)) or None
    request_timeout = int(_cfg_get(config, "request_timeout", 60))
    max_retries = int(_cfg_get(config, "max_retries", 2))

    # clé API: priorité param -> config.secrets.api_key -> ENV
    api_key = (
        api_key
        or _cfg_get_nested(config, "secrets", "api_key")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_API_TOKEN")
    )
    if not api_key:
        err = "OpenAI api_key is missing (param api_key, config.secrets.api_key, or env OPENAI_API_KEY)."
        logger.error(f"[TYPE: OPENAI] {err}")
        return _error_payload(err)

    project = _cfg_get(config, "project") or os.getenv("OPENAI_PROJECT")
    organization = _cfg_get(config, "organization") or os.getenv("OPENAI_ORGANIZATION")
    api_base = _cfg_get(config, "api_base") or "https://api.openai.com/v1"
    url = f"{api_base.rstrip('/')}/chat/completions"

    norm_messages = _normalize_messages(messages, system, message)
    if not norm_messages:
        err = "No messages provided (use either 'messages' array or 'system' + 'message')."
        logger.error(f"[TYPE: OPENAI] {err}")
        return _error_payload(err)

    payload: Dict[str, Any] = {"model": model, "temperature": temperature, "messages": norm_messages}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = _build_headers(api_key=api_key, project=project, organization=organization)

    last_error_text: Optional[str] = None
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"[TYPE: OPENAI] chat_completion call with model={model}, temp={temperature}, max_tokens={max_tokens or 'default'}")
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=request_timeout)

            if 200 <= resp.status_code < 300:
                data = resp.json()
                choice = (data.get("choices") or [{}])[0]
                content = ""
                if isinstance(choice.get("message"), dict):
                    content = choice["message"].get("content") or ""
                elif "text" in choice:
                    content = choice.get("text") or ""

                usage = data.get("usage") or {}
                input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
                total_tokens = usage.get("total_tokens") or (input_tokens + output_tokens)

                return {
                    "output": {
                        "response": content,
                        "model": model,
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": total_tokens,
                        },
                        "stop_reason": choice.get("finish_reason") or data.get("finish_reason") or "stop",
                    },
                    "tokens": {"stepAmount": total_tokens, "totalCurrentAmount": total_tokens},
                    "message": "ok",
                    "code": 200,
                    "meta": {"id": data.get("id")},
                }

            try:
                last_error_text = json.dumps(resp.json(), ensure_ascii=False, indent=2)
            except Exception:
                last_error_text = resp.text

            logger.error(f"[TYPE: OPENAI] chat_completion failed: Error code: {resp.status_code} - {last_error_text}")

            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(0.75 * (attempt + 1))
                continue

            return _error_payload(f"Error code: {resp.status_code} - {last_error_text}")

        except requests.RequestException as e:
            last_error_text = str(e)
            logger.error(f"[TYPE: OPENAI] chat_completion exception: {last_error_text}")
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            return _error_payload(last_error_text)

    return _error_payload(last_error_text or "Unknown error")


def _error_payload(msg: str) -> Dict[str, Any]:
    return {
        "output": {
            "response": f"Error: {msg}",
            "model": None,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "stop_reason": "error",
        },
        "tokens": {"stepAmount": 0, "totalCurrentAmount": 0},
        "message": msg,
        "code": 500,
        "meta": None,
    }
