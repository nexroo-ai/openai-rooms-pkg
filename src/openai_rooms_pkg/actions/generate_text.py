from loguru import logger
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from .base import ActionResponse, OutputBase, TokensSchema
from openai_rooms_pkg.configuration import CustomAddonConfig  

from openai import OpenAI

class ActionInput(BaseModel):
    prompt: str
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class ActionOutput(OutputBase):
    generated_text: str
    model_used: str
    usage: dict
    timestamp: str

def generate_text(config: CustomAddonConfig, prompt: str, model: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> ActionResponse:
    logger.debug("OpenAI rooms package - Generate text action executed successfully!")
    logger.debug(f"Input received: {prompt}, {model}, {max_tokens}, {temperature}")
    logger.debug(f"Config: {config}")
    
    required = config.get_required_secrets()
    secret_key_name = getattr(required, "openai_api_key", "openai_api_key")
    access_token = config.secrets.get(secret_key_name) or config.secrets.get("openai_api_key")

    if not access_token:
        msg = "Missing OAuth access_token in secrets."
        logger.error(msg)
        return ActionResponse(
            output=ActionOutput(data={"error": msg}),
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=msg,
            code=401,
        )
    client = OpenAI(api_key=access_token)

    response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    tokens = TokensSchema(
        stepAmount=response.usage.total_tokens,
        totalCurrentAmount=response.usage.total_tokens
    )
        
    message = "Action executed successfully"
    
    code = 200

    output = ActionOutput(
        generated_text=response.choices[0].message.content,
        model_used=model,
        usage=response.usage.model_dump(),
        timestamp=datetime.now().isoformat()
    )    
    
    return ActionResponse(output=output, tokens=tokens, message=message, code=code)