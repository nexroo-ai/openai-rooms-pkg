import openai
import os
from loguru import logger
from typing import Optional, Dict, Any
from ..configuration.addonconfig import OpenAIAddonConfig
from ..utils.exceptions import OpenAIAddonError

class OpenAIService:
    """Service for managing OpenAI API interactions"""
    
    def __init__(self, config: OpenAIAddonConfig):
        self.config = config
        self._setup_openai_client()
    
    def _setup_openai_client(self):
        """Setup OpenAI client with API key"""
        api_key = self.get_api_key()
        
        if not api_key:
            raise OpenAIAddonError('OpenAI API key not found')
        
        openai.api_key = api_key
        openai.api_base = self.config.api_base
        
        logger.info("OpenAI client configured")
    
    def get_api_key(self, override_key: Optional[str] = None) -> str:
        """Get API key with optional override"""
        if override_key:
            return override_key
        
        if self.config and self.config.secrets:
            api_key_env = self.config.secrets.get('apiKey')
            if api_key_env:
                api_key = os.environ.get(api_key_env)
                if api_key:
                    return api_key
        
        # Fallback to environment variable
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise OpenAIAddonError('OpenAI API key not found')
        
        return api_key
    
    def validate_model(self, model: str, model_type: str = 'chat') -> bool:
        """Validate if model is supported"""
        supported_models = {
            'chat': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'],
            'image': ['dall-e-2', 'dall-e-3'],
            'audio': ['whisper-1']
        }
        
        return model in supported_models.get(model_type, [])
    
    def handle_api_error(self, error: Exception) -> str:
        """Handle OpenAI API errors"""
        error_message = str(error)
        
        if "rate_limit" in error_message.lower():
            return "Rate limit exceeded. Please try again later."
        elif "invalid_api_key" in error_message.lower():
            return "Invalid API key provided."
        elif "insufficient_quota" in error_message.lower():
            return "Insufficient quota. Please check your OpenAI account."
        elif "context_length" in error_message.lower():
            return "Context length exceeded. Please reduce the input size."
        else:
            return f"OpenAI API error: {error_message}"