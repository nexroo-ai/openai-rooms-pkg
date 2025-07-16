from loguru import logger
import openai
import os

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
room_id = f'room_{{workflow_id}}'

if not OPENAI_API_KEY:
    raise ValueError('OPENAI_API_KEY environment variable not set')

def image_generate_action(prompt: str, size: str = "1024x1024", n: int = 1, secret_key: str = None):
    openai.api_key = secret_key or OPENAI_API_KEY

    logger.info("Sending image generation request...")
    response = openai.Image.create(
        prompt=prompt,
        n=n,
        size=size,
        response_format="url"
    )
    return [img["url"] for img in response["data"]]