from abc import ABC, abstractmethod
from typing import Union, Dict, List, Any
import re

def safe_format(template: str, **kwargs) -> str:
    """
    Safely formats a prompt template by replacing only the keys specified in kwargs.
    This avoids KeyErrors when the template contains unescaped curly braces (e.g. JSON schemas).
    """
    result = template
    for key, val in kwargs.items():
        # Match exactly {key} and replace it with its value
        result = re.sub(r'(?<!{)\{' + re.escape(key) + r'\}(?!})', str(val), result)
    return result

class AIProvider(ABC):
    """
    Abstract base class for AI language model providers.
    """
    
    @abstractmethod
    async def generate_json(self, prompt_template: str, **kwargs) -> Union[Dict[str, Any], List[Any]]:
        """
        Formats a prompt template with kwargs, sends it to the LLM, 
        and parses the returned string into a JSON dictionary or list.
        
        Args:
            prompt_template: The string template to format
            **kwargs: Variables to format into the template
            
        Returns:
            Parsed JSON object or list from the LLM
        """
        pass
