from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig

class OpenAIAddonConfig(BaseAddonConfig):
    """Configuration for OpenAI addon"""
    
    type: str = Field("openai", description="OpenAI addon type")
    
    # OpenAI specific configuration
    default_model: str = Field("gpt-3.5-turbo", description="Default OpenAI model")
    default_temperature: float = Field(0.7, description="Default temperature for completions")
    default_max_tokens: int = Field(1500, description="Default max tokens for completions")
    default_image_size: str = Field("1024x1024", description="Default image size")
    default_audio_language: str = Field("fr", description="Default audio language")
    
    # API settings
    api_base: str = Field("https://api.openai.com/v1", description="OpenAI API base URL")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    
    @model_validator(mode='after')
    def validate_configuration(self):
        """Validate OpenAI addon configuration"""
        
        # Validate required secrets
        if "apiKey" not in self.secrets:
            raise ValueError("apiKey is missing from secrets")
        
        # Validate temperature range
        if not (0 <= self.default_temperature <= 2):
            raise ValueError("default_temperature must be between 0 and 2")
        
        # Validate max_tokens
        if self.default_max_tokens < 1 or self.default_max_tokens > 4096:
            raise ValueError("default_max_tokens must be between 1 and 4096")
        
        # Validate image size
        valid_sizes = ["256x256", "512x512", "1024x1024"]
        if self.default_image_size not in valid_sizes:
            raise ValueError(f"default_image_size must be one of: {valid_sizes}")
        
        # Validate timeout
        if self.timeout < 1:
            raise ValueError("timeout must be at least 1 second")
        
        # Validate max_retries
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        return self
