from loguru import logger
from .configuration.addonconfig import OpenAIAddonConfig
from .services.openai_service import OpenAIService
from .actions.chat_completion import chat_completions_action
from .actions.image_generation import image_generate_action
from .actions.audio_transcription import audio_transcribe_action
from .utils.validators import validate_parameters
from .utils.exceptions import OpenAIAddonError

class OpenAIRoomsAddon:
    """OpenAI Rooms Addon for AI rooms script"""
    
    def __init__(self, config: OpenAIAddonConfig = None):
        self.config = config
        self.service = OpenAIService(self.config) if config else None
        
        # Register available actions
        self.actions = {
            'chat_completions': chat_completions_action,
            'image_generate': image_generate_action,
            'audio_transcribe': audio_transcribe_action,
        }
        
        logger.info("OpenAI Rooms Addon initialized")
    
    def test(self) -> dict:
        """Test method required by AI rooms script"""
        try:
            # Test basic functionality
            logger.info("Testing OpenAI Rooms Addon...")
            
            # Check if configuration is valid
            if not self.config:
                return {
                    'success': False,
                    'error': 'No configuration provided'
                }
            
            # Check if API key is available
            if not self.service:
                return {
                    'success': False,
                    'error': 'OpenAI service not initialized'
                }
            
            # Test API key validation
            try:
                api_key = self.service.get_api_key()
                if not api_key:
                    return {
                        'success': False,
                        'error': 'No API key found'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'API key validation failed: {str(e)}'
                }
            
            # Test actions availability
            available_actions = self.get_available_actions()
            
            return {
                'success': True,
                'message': 'OpenAI Rooms Addon test passed',
                'available_actions': available_actions,
                'config_type': self.config.type
            }
            
        except Exception as e:
            logger.error(f"OpenAI Rooms Addon test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_action(self, action_name: str, parameters: dict, workflow_id: str = None) -> dict:
        """Execute an OpenAI action with given parameters"""
        try:
            if action_name not in self.actions:
                raise OpenAIAddonError(f"Action '{action_name}' not found")
            
            # Validate parameters
            validate_parameters(action_name, parameters)
            
            # Add secret key to parameters if available
            if 'secret_key' not in parameters and self.config and self.config.secrets:
                api_key_env = self.config.secrets.get('apiKey')
                if api_key_env:
                    import os
                    parameters['secret_key'] = os.environ.get(api_key_env)
            
            # Execute action
            logger.info(f"Executing action: {action_name}")
            result = self.actions[action_name](**parameters)
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error executing action {action_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': action_name
            }
    
    def get_available_actions(self) -> list:
        """Get list of available actions"""
        return list(self.actions.keys())
    
    def get_action_info(self, action_name: str) -> dict:
        """Get information about a specific action"""
        if action_name not in self.actions:
            return None
        
        action_info = {
            'chat_completions': {
                'description': 'Generate text using OpenAI chat completion',
                'parameters': ['prompt', 'model', 'temperature', 'max_tokens', 'secret_key']
            },
            'image_generate': {
                'description': 'Generate images using OpenAI DALL-E',
                'parameters': ['prompt', 'size', 'n', 'secret_key']
            },
            'audio_transcribe': {
                'description': 'Transcribe audio using OpenAI Whisper',
                'parameters': ['file_path', 'language', 'secret_key']
            }
        }
        
        return action_info.get(action_name, {})