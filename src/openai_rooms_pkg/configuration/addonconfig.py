from typing import Any, Dict, Optional
from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig, RequiredSecretsBase
class CustomRequiredSecrets(RequiredSecretsBase):
    openai_api_key: str = Field(..., description="OpenAI API key environment variable name (key name expected in `secrets`).")

class CustomAddonConfig(BaseAddonConfig):
<<<<<<< Updated upstream
    # override/fusions simples si besoin
    config: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _merge_config(self):
        """
        Permet de supporter le JSON style:
          "config": {"model": "...", "temperature": ...}
        en fusionnant dans les champs top-level pydantic.
        """
        cfg = self.config or {}
        for k, v in cfg.items():
            if getattr(self, k, None) in (None, [], {}, ""):
                try:
                    setattr(self, k, v)
                except Exception:
                    pass
        return self

    @model_validator(mode="after")
    def _normalize_secrets(self):
        """
        S’assure que la clé attendue est 'api_key'.
        Accepte aussi 'OPENAI_API_KEY' si fourni.
        """
        if not self.secrets:
            self.secrets = {}
        if "api_key" not in self.secrets and "OPENAI_API_KEY" in self.secrets:
            self.secrets["api_key"] = self.secrets["OPENAI_API_KEY"]
=======
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
>>>>>>> Stashed changes
        return self
