import json
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.chapter import Chapter
from backend.ai.prompts.chapter_prompt import CHAPTER_PROMPT
from backend.ai.providers import get_provider, ensure_list

async def generate_and_store_chapters(db: AsyncSession, video_id: str, transcript_chunks: List[Dict]) -> List[Chapter]:
    if not transcript_chunks:
        return []

    # Map chunks to include indices explicitly for the LLM
    formatted_chunks = []
    for idx, chunk in enumerate(transcript_chunks):
        formatted_chunks.append({
            "index": idx,
            "start_time": float(chunk.get("start_time", 0.0)),
            "end_time": float(chunk.get("end_time", 0.0)),
            "text": chunk.get("text", "")
        })

    # Format the chunks as a JSON string for the prompt
    transcript_json = json.dumps(formatted_chunks, indent=2)

    try:
        provider = get_provider()
        chapters_raw = await provider.generate_json(CHAPTER_PROMPT, transcript_json=transcript_json)
        chapters_data = ensure_list(chapters_raw)
    except Exception as e:
        print(f"Failed to generate chapters: {e}")
        return []

    # If the LLM returned index mappings, resolve them to actual timestamps
    resolved_chapters = []
    for ch_data in chapters_data:
        title = ch_data.get("title", "Untitled Chapter")
        summary = ch_data.get("summary", "")
        
        # Handle index-based mapping
        if "start_chunk_index" in ch_data and "end_chunk_index" in ch_data:
            try:
                start_idx = int(ch_data.get("start_chunk_index", 0))
                end_idx = int(ch_data.get("end_chunk_index", 0))
                
                # Clamp within boundaries
                start_idx = max(0, min(start_idx, len(transcript_chunks) - 1))
                end_idx = max(start_idx, min(end_idx, len(transcript_chunks) - 1))
                
                start_time = float(transcript_chunks[start_idx].get("start_time", 0.0))
                end_time = float(transcript_chunks[end_idx].get("end_time", 0.0))
            except (ValueError, TypeError):
                # Fallback to direct times if parsing failed
                start_time = float(ch_data.get("start_time", 0.0))
                end_time = float(ch_data.get("end_time", 0.0))
        else:
            # Fallback for old structure or legacy model outputs
            start_time = float(ch_data.get("start_time", 0.0))
            end_time = float(ch_data.get("end_time", 0.0))
            
        resolved_chapters.append({
            "title": title,
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time
        })

    # Sort chapters sequentially by start time
    resolved_chapters = sorted(resolved_chapters, key=lambda c: c["start_time"])

    created_chapters = []
    num_resolved = len(resolved_chapters)
    for i, ch_info in enumerate(resolved_chapters):
        start_time = ch_info["start_time"]
        end_time = ch_info["end_time"]

        # Ensure first chapter starts at exactly the beginning of the video
        if i == 0:
            start_time = float(transcript_chunks[0].get("start_time", 0.0))
            
        # Ensure last chapter ends at the end of the video
        if i == num_resolved - 1:
            end_time = float(transcript_chunks[-1].get("end_time", end_time))

        # Enforce continuity: end time of chapter i is start time of chapter i + 1
        if i < num_resolved - 1:
            end_time = resolved_chapters[i + 1]["start_time"]

        # If start and end are identical or reversed, auto-adjust
        if end_time <= start_time and i < num_resolved - 1:
            end_time = start_time + 1.0

        chapter = Chapter(
            video_id=video_id,
            title=ch_info["title"],
            summary=ch_info["summary"],
            start_time=start_time,
            end_time=end_time,
        )
        db.add(chapter)
        created_chapters.append(chapter)

    await db.commit()
    for ch in created_chapters:
        await db.refresh(ch)

    return created_chapters
