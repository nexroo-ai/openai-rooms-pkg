import importlib

from loguru import logger

from .actions.generate_text import generate_text
from .services.credentials import CredentialsRegistry


class OpenaiRoomsAddon:
    def __init__(self):
        self.modules = ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        self.config = {}
        self.credentials = CredentialsRegistry()

    def generate_text(self, prompt: str) -> dict:
        return generate_text(self.config, prompt=prompt)

    def test(self) -> bool:
        logger.info("Running OpenAI rooms package test...")
        total_components = 0
        for module_name in self.modules:
            try:
                module = importlib.import_module(f"openai_rooms_pkg.{module_name}")
                components = getattr(module, '__all__', [])
                component_count = len(components)
                total_components += component_count
                for component_name in components:
                    logger.info(f"Processing component: {component_name}")
                    if hasattr(module, component_name):
                        component = getattr(module, component_name)
                        if callable(component):
                            try:
                                skip_instantiation = False
                                try:
                                    from pydantic import BaseModel
                                    if hasattr(component, '__bases__') and any(
                                        issubclass(base, BaseModel) for base in component.__bases__ if isinstance(base, type)
                                    ):
                                        skip_instantiation = True
                                except (ImportError, TypeError):
                                    pass
                                if component_name in ['ActionInput', 'ActionOutput', 'ActionResponse', 'OutputBase', 'TokensSchema']:
                                    skip_instantiation = True
                                if not skip_instantiation:
                                    pass
                            except Exception as e:
                                logger.error(f"Exception details for {component_name}: {str(e)}")
                                raise e
                logger.info(f"{module_name} loaded correctly")
            except ImportError as e:
                logger.error(f"Failed to import {module_name}: {e}")
                return False
            except Exception as e:
                logger.error(f"Error testing {module_name}: {e}")
                return False
        logger.info("OpenAI rooms package test completed successfully!")
        logger.info(f"Total components loaded: {total_components} across {len(self.modules)} modules")
        return True

    def loadAddonConfig(self, addon_config: dict):
        try:
            from openai_rooms_pkg.configuration import CustomAddonConfig
            self.config = CustomAddonConfig(**addon_config)
            logger.info(f"Addon configuration loaded successfully: {self.config}")
            return True
        except Exception as e:
            logger.error(f"Failed to load addon configuration: {e}")
            return False

    def loadCredentials(self, **kwargs) -> bool:
        logger.debug("Loading credentials...")
        logger.debug(f"Received credentials: {kwargs}")
        try:
            if self.config and hasattr(self.config, 'secrets'):
                required_secrets = list(self.config.secrets.keys())
                missing_secrets = [secret for secret in required_secrets if secret not in kwargs]
                if missing_secrets:
                    raise ValueError(f"Missing required secrets: {missing_secrets}")
            self.credentials.store_multiple(kwargs)
            logger.info(f"Loaded {len(kwargs)} credentials successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return False
