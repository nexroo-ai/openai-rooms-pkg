from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig

class CustomAddonConfig(BaseAddonConfig):
    type: str = Field("openai", description="OpenAI addon type")
    
    # Paramètres OpenAI
    model: str = Field("gpt-3.5-turbo", description="OpenAI model")
    temperature: float = Field(0.7, description="Temperature")
    max_tokens: int = Field(1000, description="Max tokens")
    
    @model_validator(mode='after')
    def validate_openai_secrets(self):
        if "openai_api_key" not in self.secrets:
            raise ValueError("openai_api_key secret is required")
        return self