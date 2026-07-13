import os
import json
import time
from google import genai
from google.genai import types
from typing import Union, Dict, List, Any

from backend.ai.providers.base import AIProvider
from backend.ai.metrics import AI_TOKEN_USAGE_TOTAL, AI_API_COST_TOTAL, AI_REQUEST_LATENCY_SECONDS

class GeminiProvider(AIProvider):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = model_name

    async def generate_json(self, prompt_template: str, **kwargs) -> Union[Dict[str, Any], List[Any]]:
        # Format the prompt using kwargs
        prompt = prompt_template.format(**kwargs)
        
        start_time = time.time()
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        duration = time.time() - start_time
        AI_REQUEST_LATENCY_SECONDS.labels(model=self.model_name, operation="generate_json").observe(duration)
        
        # Track Usage & Estimate Cost
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            prompt_tokens = response.usage_metadata.prompt_token_count
            completion_tokens = response.usage_metadata.candidates_token_count
            
            # Increment Token Counters
            AI_TOKEN_USAGE_TOTAL.labels(model=self.model_name, operation="generate_json", token_type="prompt").inc(prompt_tokens)
            AI_TOKEN_USAGE_TOTAL.labels(model=self.model_name, operation="generate_json", token_type="completion").inc(completion_tokens)
            
            # Estimate cost (Gemini 1.5 Flash: ~$0.075/1M input, ~$0.30/1M output as of 2024)
            cost = (prompt_tokens / 1_000_000 * 0.075) + (completion_tokens / 1_000_000 * 0.3)
            AI_API_COST_TOTAL.labels(model=self.model_name, operation="generate_json").inc(cost)
            
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback if the model failed to return perfect JSON despite mime_type
            import re
            cleaned_text = re.sub(r'```json\n?|```', '', response.text).strip()
            return json.loads(cleaned_text)
