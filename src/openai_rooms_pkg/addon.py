import importlib
from loguru import logger

from .actions import chat_completion
from .services.credentials import CredentialsRegistry

class OpenaiRoomsAddon:
    """
    Addon OpenAI – interface simple comme dans l’addon Anthropic.
    Expose chat_completion(message=..., system=..., ...) et supporte aussi messages=[...].
    """
    type = "openai"

    def __init__(self):
        self.modules = ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        self.config = {}
        self.credentials = CredentialsRegistry()
        self.tool_registry = None  # pas utilisé ici mais compatible
        self.observer_callback = None
        self.addon_id = None

    @property
    def logger(self):
        class PrefixedLogger:
            def __init__(self, addon_type):
                self.addon_type = addon_type
                self._logger = logger

            def debug(self, message): self._logger.debug(f"[TYPE: {self.addon_type.upper()}] {message}")
            def info(self, message): self._logger.info(f"[TYPE: {self.addon_type.upper()}] {message}")
            def warning(self, message): self._logger.warning(f"[TYPE: {self.addon_type.upper()}] {message}")
            def error(self, message): self._logger.error(f"[TYPE: {self.addon_type.upper()}] {message}")

        return PrefixedLogger(self.type)

    # Parité Anthropic
    def setObserverCallback(self, callback, addon_id: str):
        self.observer_callback = callback
        self.addon_id = addon_id

    # Point d’entrée ACTION
    def chat_completion(self, message: str = None, **kwargs) -> dict:
        """
        Compatible:
          - chat_completion(message="...", system="...", max_tokens=..., temperature=...)
          - chat_completion(messages=[{role, content}, ...], ...)
        """
        # injecte observer si présent
        if self.observer_callback and self.addon_id:
            kwargs["observer_callback"] = self.observer_callback
            kwargs["addon_id"] = self.addon_id

        # passe la config pydantic vers l’action
        return chat_completion(self.config, message=message, **kwargs)

    # Test loader (parité)
    def test(self) -> bool:
        self.logger.info("Running openai-rooms-pkg test...")
        total_components = 0
        for module_name in self.modules:
            try:
                module = importlib.import_module(f"openai_rooms_pkg.{module_name}")
                components = getattr(module, "__all__", [])
                total_components += len(components)
                self.logger.info(f"{len(components)} {module_name} loaded correctly, available imports: {', '.join(components)}")
            except ImportError as e:
                self.logger.error(f"Failed to import {module_name}: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Error testing {module_name}: {e}")
                return False
        self.logger.info("openai-rooms-pkg test completed successfully!")
        self.logger.info(f"Total components loaded: {total_components} across {len(self.modules)} modules")
        return True

    # Chargement config (style Anthropic)
    def loadAddonConfig(self, addon_config: dict) -> bool:
        try:
            from openai_rooms_pkg.configuration import CustomAddonConfig
            self.config = CustomAddonConfig(**addon_config)
            self.logger.info(f"Addon configuration loaded successfully: {self.config}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load addon configuration: {e}")
            return False

    # Chargement credentials (style Anthropic)
    def loadCredentials(self, **kwargs) -> bool:
        try:
            if self.config and hasattr(self.config, "secrets"):
                required = list(getattr(self.config, "secrets", {}).keys())
                missing = [k for k in required if k not in kwargs]
                if missing:
                    raise ValueError(f"Missing required secrets: {missing}")
            self.credentials.store_multiple(kwargs)
            self.logger.info(f"Loaded {len(kwargs)} credentials successfully")
            try:
                self.config.secrets.update(kwargs)
            except Exception:
                pass
            return True
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            return False
