from abc import ABC, abstractmethod
from typing import Union, Dict, List, Any

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
