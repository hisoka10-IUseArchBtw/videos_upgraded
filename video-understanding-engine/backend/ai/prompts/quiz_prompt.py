QUIZ_PROMPT = """You are an expert educational assistant.
Based on the provided video transcript, generate a multiple-choice quiz to test the user's understanding of the core material.
Each question should have 4 options, and exactly one correct answer. The correct answer must exactly match one of the provided options.

Return the result as a valid JSON array of objects with the following schema:
[
    {
        "question": "Clear multiple-choice question?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A"
    }
]

Transcript:
{transcript}
"""
