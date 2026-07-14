FLASHCARD_PROMPT = """You are an expert educational assistant.
Based on the provided video transcript, generate a list of flashcards that capture the most important concepts, facts, and definitions.
Each flashcard should have a clear question and a concise answer.

Return a JSON object with a "flashcards" key containing an array of flashcard objects:
{{"flashcards": [
    {{
        "question": "Clear and specific question?",
        "answer": "Concise and accurate answer."
    }}
]}}

Transcript:
{transcript}
"""
