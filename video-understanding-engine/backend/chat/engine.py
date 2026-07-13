import uuid
from backend.search.service import SearchService
from backend.ai.providers.gemini import GeminiProvider
from backend.ai.prompts.chat_prompt import CHAT_PROMPT

class ChatEngine:
    """
    RAG pipeline for chatting with a video.
    """
    def __init__(self):
        self.search_service = SearchService()
        self.ai_provider = GeminiProvider()
        
    async def generate_chat_response(self, video_id: str, question: str) -> str:
        # Retrieve relevant chunks using existing semantic search
        results = await self.search_service.semantic_search(
            query=question,
            video_id=video_id,
            limit=5,
            score_threshold=0.3
        )
        
        # Build context from chunks
        if not results:
            context = "No relevant transcript chunks found for this video."
        else:
            context_parts = []
            for i, res in enumerate(results):
                context_parts.append(f"[Chunk {i+1} | Time: {res.start_time:.1f}s - {res.end_time:.1f}s]: {res.text}")
            context = "\n\n".join(context_parts)
            
        # Query LLM with the formulated context and question
        response_data = await self.ai_provider.generate_json(
            prompt_template=CHAT_PROMPT,
            context=context,
            question=question
        )
        
        return response_data.get("answer", "I could not generate an answer.")
