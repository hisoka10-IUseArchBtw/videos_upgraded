CHAPTER_PROMPT = """You are an expert video editor and content structurer.
I will provide you with a JSON array of timestamped transcript chunks from a video. Each chunk has an "index", "start_time", "end_time", and "text".
Your task is to group these chunks into logical "chapters" that represent the main topics discussed.

For each chapter, you must specify:
1. "title": A clear, concise title.
2. "summary": A brief summary (1-2 sentences).
3. "start_chunk_index": The integer "index" of the transcript chunk where this chapter begins.
4. "end_chunk_index": The integer "index" of the transcript chunk where this chapter ends.

Guidelines:
- The first chapter's "start_chunk_index" must be 0.
- The last chapter's "end_chunk_index" must be the index of the last transcript chunk.
- There must be no gaps or overlaps between chapters (the "start_chunk_index" of Chapter N+1 must be "end_chunk_index" of Chapter N + 1).

Return a JSON object with a "chapters" key containing an array of chapter objects:
{{"chapters": [
    {{
        "title": "Introduction",
        "summary": "Welcome and overview of the topic.",
        "start_chunk_index": 0,
        "end_chunk_index": 12
    }}
]}}

Transcript Chunks:
{transcript_json}
"""
