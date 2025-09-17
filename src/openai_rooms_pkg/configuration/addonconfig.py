from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig, RequiredSecretsBase
class CustomRequiredSecrets(RequiredSecretsBase):
    openai_api_key: str = Field(..., description="OpenAI API key environment variable name (key name expected in `secrets`).")

class CustomAddonConfig(BaseAddonConfig):
    type: str = Field("openai", description="OpenAI addon type")
    model: str = Field("gpt-3.5-turbo", description="OpenAI model")
    temperature: float = Field(0.7, description="Temperature")
    max_tokens: int = Field(1000, description="Max tokens")
    
    def get_required_secrets(cls) -> CustomRequiredSecrets:
        return CustomRequiredSecrets(openai_api_key="openai_api_key")

    @model_validator(mode="after")
    def validate_openai_secrets(self):
        required = self.get_required_secrets()
        required_secret_keys = [required.openai_api_key]

        missing = [k for k in required_secret_keys if not self.secrets.get(k)]
        if missing:
            raise ValueError("Missing OpenAI secrets: "f"{missing}. Put your OAuth access token under these keys in `secrets`.")
        return self
