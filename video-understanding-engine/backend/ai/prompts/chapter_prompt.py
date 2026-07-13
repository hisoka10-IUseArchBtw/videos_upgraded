CHAPTER_PROMPT = """You are an expert video editor and content structurer.
I will provide you with a JSON array of timestamped transcript chunks from a video.
Your task is to group these chunks into logical "chapters" that represent the main topics discussed.

Each chapter should have a clear, concise title, a brief summary (1-2 sentences), and the exact start and end times (in seconds).
The first chapter must start at the earliest start_time in the transcript.
The final chapter must end at the latest end_time in the transcript.
There should be no gaps between chapters. The end_time of Chapter N should equal the start_time of Chapter N+1.

Return the result as a valid JSON array of objects, where each object has the following schema:
[
    {
        "title": "Introduction",
        "summary": "Welcome and overview of the topic.",
        "start_time": 0.0,
        "end_time": 45.2
    }
]

Transcript Chunks:
{transcript_json}
"""
