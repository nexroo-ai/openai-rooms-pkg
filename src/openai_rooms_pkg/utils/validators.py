import os
from typing import Dict, Any
from pathlib import Path
from .exceptions import ValidationError

def validate_parameters(action_name: str, parameters: Dict[str, Any]) -> None:
    """Validate parameters for a specific action"""
    
    validators = {
        'chat_completions': _validate_chat_parameters,
        'image_generate': _validate_image_parameters,
        'audio_transcribe': _validate_audio_parameters,
    }
    
    if action_name not in validators:
        raise ValidationError(f"Unknown action: {action_name}")
    
    validators[action_name](parameters)

def _validate_chat_parameters(params: Dict[str, Any]) -> None:
    """Validate chat completion parameters"""
    
    # Required parameters
    if 'prompt' not in params:
        raise ValidationError("Missing required parameter: prompt")
    
    if not isinstance(params['prompt'], str) or not params['prompt'].strip():
        raise ValidationError("Parameter 'prompt' must be a non-empty string")
    
    # Optional parameters validation
    if 'model' in params:
        valid_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o']
        if params['model'] not in valid_models:
            raise ValidationError(f"Invalid model. Must be one of: {valid_models}")
    
    if 'temperature' in params:
        temp = params['temperature']
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
            raise ValidationError("Temperature must be a number between 0 and 2")
    
    if 'max_tokens' in params:
        max_tokens = params['max_tokens']
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 4096:
            raise ValidationError("max_tokens must be an integer between 1 and 4096")

def _validate_image_parameters(params: Dict[str, Any]) -> None:
    """Validate image generation parameters"""
    
    # Required parameters
    if 'prompt' not in params:
        raise ValidationError("Missing required parameter: prompt")
    
    if not isinstance(params['prompt'], str) or not params['prompt'].strip():
        raise ValidationError("Parameter 'prompt' must be a non-empty string")
    
    # Optional parameters validation
    if 'size' in params:
        valid_sizes = ['256x256', '512x512', '1024x1024']
        if params['size'] not in valid_sizes:
            raise ValidationError(f"Invalid size. Must be one of: {valid_sizes}")
    
    if 'n' in params:
        n = params['n']
        if not isinstance(n, int) or n < 1 or n > 10:
            raise ValidationError("Parameter 'n' must be an integer between 1 and 10")

def _validate_audio_parameters(params: Dict[str, Any]) -> None:
    """Validate audio transcription parameters"""
    
    # Required parameters
    if 'file_path' not in params:
        raise ValidationError("Missing required parameter: file_path")
    
    file_path = params['file_path']
    if not isinstance(file_path, str):
        raise ValidationError("Parameter 'file_path' must be a string")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise ValidationError(f"Audio file not found: {file_path}")
    
    # Check file extension
    valid_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
    file_extension = Path(file_path).suffix.lower()
    if file_extension not in valid_extensions:
        raise ValidationError(f"Invalid file extension. Must be one of: {valid_extensions}")
    
    # Optional parameters validation
    if 'language' in params:
        language = params['language']
        if not isinstance(language, str) or len(language) != 2:
            raise ValidationError("Language must be a 2-character language code (e.g., 'fr', 'en')")