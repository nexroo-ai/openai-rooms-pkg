from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig, RequiredSecretsBase

class CustomRequiredSecrets(RequiredSecretsBase):
    openai_api_key: str = Field(..., description="OpenAI API key environment variable name stored under `secrets`.")

class CustomAddonConfig(BaseAddonConfig):
    type: str = Field("openai", description="OpenAI addon type")
    model: str = Field("gpt-3.5-turbo", description="Default OpenAI model")
    temperature: float = Field(0.7, description="Default temperature")
    max_tokens: int = Field(1000, description="Default maximum tokens")

    def get_required_secrets(self) -> CustomRequiredSecrets:
        return CustomRequiredSecrets(openai_api_key="openai_api_key")

    @model_validator(mode="after")
    def validate_openai_secrets(self):
        required = self.get_required_secrets()
        required_secret_keys = [required.openai_api_key]
        missing = [k for k in required_secret_keys if not self.secrets.get(k)]
        if missing:
            raise ValueError(f"Missing OpenAI secrets: {missing}. Put your API key under these keys in `secrets`.")
        return self
