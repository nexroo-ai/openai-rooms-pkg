from loguru import logger
import openai
import os

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
room_id = f'room_{{workflow_id}}'

if not OPENAI_API_KEY:
    raise ValueError('OPENAI_API_KEY environment variable not set')

def audio_transcribe_action(file_path: str, secret_key: str = None, language: str = "fr"):
    openai.api_key = secret_key or OPENAI_API_KEY

    logger.info(f"Transcribing audio file: {file_path}")
    with open(file_path, "rb") as audio_file:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language=language
        )
    return response["text"]