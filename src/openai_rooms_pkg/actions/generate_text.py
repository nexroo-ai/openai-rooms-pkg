from loguru import logger
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from .base import ActionResponse, OutputBase, TokensSchema
from openai_rooms_pkg.configuration import CustomAddonConfig  
from openai_rooms_pkg.services.credentials import CredentialsRegistry

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

# entrypoint is always the same name as the action file name.
# the script use the function name, to simplify we will use the same name as the file.
def generate_text(config: CustomAddonConfig, prompt: str, model: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> ActionResponse:


    # if not isinstance(inputs, ActionInput):
    #     raise ValueError("Invalid input type. Expected ActionInput.")
    logger.debug("OpenAI rooms package - Generate text action executed successfully!")
    logger.debug(f"Input received: {prompt}, {model}, {max_tokens}, {temperature}")
    logger.debug(f"Config: {config}")
    
    
    credentials = CredentialsRegistry()
    if credentials.get("openai_key"):
        logger.debug(f"openai_key available: {credentials.get('openai_key')}")
    
    api_key = credentials.get("openai_key")
    client = OpenAI(api_key=api_key)
    
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