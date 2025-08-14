# FILE: src/openai_rooms_pkg/addon.py
from __future__ import annotations

import importlib
from typing import Optional

from loguru import logger

from .configuration import CustomAddonConfig
from .services.credentials import CredentialsRegistry
from .tools.base import ToolRegistry

# Actions (only importing the callables; engine will call instance methods here)
from .actions.chat_complete import chat_complete


class OpenaiRoomsAddon:
    """
    Rooms Addon class for OpenAI.
    Mirrors the working Anthropic addon API so the engine can use the same integration:
      - loadAddonConfig(dict) -> bool
      - loadCredentials(**kwargs) -> bool
      - loadTools(dict, dict|None, dict|None)
      - getTools() / clearTools()
      - setObserverCallback(callback, addon_id)
      - test() -> bool
      - action methods delegate to action functions with self.config
    """
    # Engine may read this attribute
    type = "openai"

    def __init__(self):
        self.modules = ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        self.config: Optional[CustomAddonConfig] = None
        self.credentials = CredentialsRegistry()
        self.tool_registry = ToolRegistry()
        self.observer_callback = None
        self.addon_id: Optional[str] = None

    @property
    def logger(self):
        """Logger with addon type prefix (parity with working addon)."""
        class PrefixedLogger:
            def __init__(self, addon_type):
                self.addon_type = addon_type
                self._logger = logger

            def debug(self, message): self._logger.debug(f"[TYPE: {self.addon_type.upper()}] {message}")
            def info(self, message): self._logger.info(f"[TYPE: {self.addon_type.upper()}] {message}")
            def warning(self, message): self._logger.warning(f"[TYPE: {self.addon_type.upper()}] {message}")
            def error(self, message): self._logger.error(f"[TYPE: {self.addon_type.upper()}] {message}")

        return PrefixedLogger(self.type)

    # ---- Tools lifecycle ----
    def loadTools(self, tool_functions, tool_descriptions=None, tool_max_retries=None):
        self.logger.debug(f"Tool functions provided: {list(tool_functions.keys())}")
        self.logger.debug(f"Tool descriptions provided: {tool_descriptions}")
        self.logger.debug(f"Tool max retries provided: {tool_max_retries}")
        self.tool_registry.register_tools(tool_functions, tool_descriptions, tool_max_retries)
        registered = self.tool_registry.get_tools_for_action()
        self.logger.info(f"Successfully registered {len(registered)} tools: {list(registered.keys())}")

    def getTools(self):
        return self.tool_registry.get_tools_for_action()

    def clearTools(self):
        self.tool_registry.clear()

    def setObserverCallback(self, callback, addon_id: str):
        self.observer_callback = callback
        self.addon_id = addon_id

    # ---- Engine hooks ----
    def loadAddonConfig(self, addon_config: dict) -> bool:
        """
        Load configuration (with resolved secret references).
        The engine may pass its own dict; we validate with CustomAddonConfig.
        """
        try:
            self.config = CustomAddonConfig(**addon_config)
            self.logger.info(f"Addon configuration loaded successfully: {self.config}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load addon configuration: {e}")
            return False

    def loadCredentials(self, **kwargs) -> bool:
        """
        Store actual secret values into the registry.
        The config's `secrets` contains secret KEYS; here we get the VALUES.
        """
        self.logger.debug("Loading credentials...")
        self.logger.debug(f"Received credentials keys: {list(kwargs.keys())}")
        try:
            if self.config and hasattr(self.config, "secrets"):
                required_refs = list(self.config.secrets.values()) if isinstance(self.config.secrets, dict) else []
                # For OpenAI addon we expect at least the value for the key referenced by secrets.api_key
                # This check is best-effort; the engine may supply different names.
                missing = [ref for ref in required_refs if ref not in kwargs]
                if missing:
                    raise ValueError(f"Missing required credential values for keys: {missing}")

            self.credentials.store_multiple(kwargs)
            self.logger.info(f"Loaded {len(kwargs)} credentials successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            return False

    def test(self) -> bool:
        """
        Load & introspect modules similarly to the working addon to satisfy the engine's healthcheck.
        """
        self.logger.info("Running openai-rooms-pkg test...")
        try:
            total_components = 0
            for module_name in self.modules:
                module = importlib.import_module(f"openai_rooms_pkg.{module_name}")
                components = getattr(module, "__all__", [])
                total_components += len(components)
                self.logger.info(f"{len(components)} {module_name} loaded correctly, available imports: {', '.join(components)}")
            self.logger.info("openai-rooms-pkg test completed successfully!")
            self.logger.info(f"Total components loaded: {total_components} across {len(self.modules)} modules")
            return True
        except Exception as e:
            self.logger.error(f"Error during openai-rooms-pkg test: {e}")
            return False

    # ---- Actions (delegate to functions) ----
    def chat_complete(self, **kwargs):
        """
        We support tools similarly to the Anthropic addon: if tools are registered,
        pass them to the action. Observer callback is forwarded if present.
        """
        if self.config is None:
            raise RuntimeError("OpenaiRoomsAddon: config is not loaded. Call loadAddonConfig first.")
        tools = self.getTools()
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_registry"] = self.tool_registry
        if self.observer_callback and self.addon_id:
            kwargs["observer_callback"] = self.observer_callback
            kwargs["addon_id"] = self.addon_id
        return chat_complete(self.config, **kwargs)
