FLASHCARD_PROMPT = """You are an expert educational assistant.
Based on the provided video transcript, generate a list of flashcards that capture the most important concepts, facts, and definitions.
Each flashcard should have a clear question and a concise answer.

Return the result as a valid JSON array of objects with the following schema:
[
    {
        "question": "Clear and specific question?",
        "answer": "Concise and accurate answer."
    }
]

Transcript:
{transcript}
"""
