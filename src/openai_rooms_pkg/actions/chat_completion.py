from loguru import logger
import openai
import os

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
room_id = f'room_{{workflow_id}}'

if not OPENAI_API_KEY:
    raise ValueError('OPENAI_API_KEY environment variable not set')

def chat_completions_action(prompt: str, model: str = 'gpt-3.5-turbo', temperature: float = 0.7, max_tokens: int = 1500, secret_key: str = None):
    openai.api_key = secret_key or OPENAI_API_KEY

    logger.info("Sending chat completion request...")
    response = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]