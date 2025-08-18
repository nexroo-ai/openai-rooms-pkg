from typing import Any, Dict, Optional
from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig

class CustomAddonConfig(BaseAddonConfig):
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
        return self
