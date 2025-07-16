class OpenAIAddonError(Exception):
    """Base exception for OpenAI addon errors"""
    pass

class ValidationError(OpenAIAddonError):
    """Raised when parameter validation fails"""
    pass

class ConfigurationError(OpenAIAddonError):
    """Raised when configuration is invalid"""
    pass

class APIError(OpenAIAddonError):
    """Raised when OpenAI API returns an error"""
    pass