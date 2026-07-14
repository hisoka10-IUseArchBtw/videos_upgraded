QUIZ_PROMPT = """You are an expert educational assistant.
Based on the provided video transcript, generate a multiple-choice quiz to test the user's understanding of the core material.
Each question should have 4 options, and exactly one correct answer. The correct answer must exactly match one of the provided options.

Return a JSON object with a "questions" key containing an array of question objects:
{{"questions": [
    {{
        "question": "Clear multiple-choice question?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A"
    }}
]}}

Transcript:
{transcript}
"""
