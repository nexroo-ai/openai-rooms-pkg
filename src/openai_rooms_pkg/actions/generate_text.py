from datetime import datetime
from typing import Any

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel

from openai_rooms_pkg.configuration import CustomAddonConfig

from .base import ActionResponse, OutputBase, TokensSchema


class ActionInput(BaseModel):
    prompt: str

class ActionOutput(OutputBase):
    generated_text: str
    model_used: str
    usage: dict[str, Any]
    timestamp: str

class ErrorOutput(OutputBase):
    error: str
    timestamp: str

def generate_text(config: CustomAddonConfig, prompt: str) -> ActionResponse:
    logger.debug("OpenAI rooms package - Generate text action executed.")
    logger.debug(f"Input received: prompt length={len(prompt)}")
    logger.debug(f"Config defaults: model={config.model}, max_tokens={config.max_tokens}, temperature={config.temperature}")

    required = config.get_required_secrets()
    secret_key_name = required.openai_api_key
    access_token = config.secrets.get(secret_key_name)

    if not access_token:
        msg = "Missing OpenAI API key in secrets."
        logger.error(msg)
        return ActionResponse(
            output=ErrorOutput(error=msg, timestamp=datetime.now().isoformat()),
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=msg,
            code=401,
        )

    client = OpenAI(api_key=access_token)

    response = client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )

    tokens = TokensSchema(
        stepAmount=response.usage.total_tokens,
        totalCurrentAmount=response.usage.total_tokens,
    )

    usage_obj: dict[str, Any] = {
        "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
        "completion_tokens": getattr(response.usage, "completion_tokens", None),
        "total_tokens": getattr(response.usage, "total_tokens", None),
    }

    output = ActionOutput(
        generated_text=response.choices[0].message.content,
        model_used=config.model,
        usage=usage_obj,
        timestamp=datetime.now().isoformat(),
    )

    return ActionResponse(output=output, tokens=tokens, message="OK", code=200)
