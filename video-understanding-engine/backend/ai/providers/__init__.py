import os
from typing import List, Union, Dict, Any

from .base import AIProvider
from .gemini import GeminiProvider
from .groq import GroqProvider

class FallbackProvider(AIProvider):
    def __init__(self, providers: List[AIProvider]):
        self.providers = providers

    async def generate_json(self, prompt_template: str, **kwargs) -> Union[Dict[str, Any], List[Any]]:
        last_error = None
        for provider in self.providers:
            try:
                return await provider.generate_json(prompt_template, **kwargs)
            except Exception as e:
                print(f"FallbackProvider: Provider {provider.__class__.__name__} failed: {e}. Trying next provider...")
                last_error = e
        if last_error:
            raise last_error
        raise RuntimeError("No AI providers were able to handle the request.")

def get_provider() -> AIProvider:
    return GroqProvider()

def ensure_list(data: Any) -> List[Any]:
    """
    Ensures that the returned data is a list.
    If the data is a dictionary containing a list, it extracts and returns that list.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for val in data.values():
            if isinstance(val, list):
                return val
        return [data]
    return []

__all__ = ["AIProvider", "GeminiProvider", "GroqProvider", "FallbackProvider", "get_provider", "ensure_list"]
