import os
import json
import time
from groq import AsyncGroq
from typing import Union, Dict, List, Any

from backend.ai.providers.base import AIProvider, safe_format
from backend.ai.metrics import AI_TOKEN_USAGE_TOTAL, AI_API_COST_TOTAL, AI_REQUEST_LATENCY_SECONDS

class GroqProvider(AIProvider):
    def __init__(self, model_name: str = None):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_name = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    async def generate_json(self, prompt_template: str, **kwargs) -> Union[Dict[str, Any], List[Any]]:
        # Format the prompt using kwargs
        prompt = safe_format(prompt_template, **kwargs)
        
        start_time = time.time()
        
        response = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.model_name,
            response_format={"type": "json_object"},
        )
        
        duration = time.time() - start_time
        AI_REQUEST_LATENCY_SECONDS.labels(model=self.model_name, operation="generate_json").observe(duration)
        
        # Track Usage & Estimate Cost
        # Llama 3 70B pricing estimation (input: $0.59/1M tokens, output: $0.79/1M tokens)
        if hasattr(response, "usage") and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            # Increment Token Counters
            AI_TOKEN_USAGE_TOTAL.labels(model=self.model_name, operation="generate_json", token_type="prompt").inc(prompt_tokens)
            AI_TOKEN_USAGE_TOTAL.labels(model=self.model_name, operation="generate_json", token_type="completion").inc(completion_tokens)
            
            cost = (prompt_tokens / 1_000_000 * 0.59) + (completion_tokens / 1_000_000 * 0.79)
            AI_API_COST_TOTAL.labels(model=self.model_name, operation="generate_json").inc(cost)
            
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback if the model failed to return perfect JSON despite response_format
            import re
            cleaned_text = re.sub(r'```json\n?|```', '', content).strip()
            return json.loads(cleaned_text)
