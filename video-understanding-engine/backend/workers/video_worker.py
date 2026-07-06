import os
import time
import asyncio
import tempfile
import ffmpeg
import google.generativeai as genai
from typing import List, Dict

from backend.core.celery_app import celery_app
from backend.core.database import AsyncSessionLocal
from backend.models.Video.video_model import Video
from sqlalchemy.future import select

from backend.services.storage import download_video_file
from backend.ai.embeddings.embedder import embed_and_store_chunks
from backend.ai.summaries.generator import generate_and_store_summary
from backend.ai.flashcards.generator import generate_and_store_flashcards
from backend.ai.quiz.generator import generate_and_store_quiz
from backend.ai.metrics import AI_REQUEST_LATENCY_SECONDS

# Configure Gemini for transcription
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_audio(video_path: str, audio_path: str):
    """Uses ffmpeg to extract audio to a wav/mp3 file."""
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='libmp3lame', ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode() if e.stderr else e}")
        raise e

def transcribe_audio_with_gemini(audio_path: str) -> List[Dict]:
    """Uploads the audio to Gemini and gets a timestamped JSON transcript."""
    print(f"Uploading {audio_path} to Gemini...")
    audio_file = genai.upload_file(path=audio_path)
    
    # Wait for the file to be processed
    while audio_file.state.name == 'PROCESSING':
        print('.', end='')
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)
    
    if audio_file.state.name == 'FAILED':
        raise ValueError("Audio processing failed in Gemini.")
    
    print("\nTranscribing...")
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    
    prompt = """Please provide a complete transcript of this audio file.
Format your response as a valid JSON array of objects.
Each object should have:
- "text": The spoken text.
- "start_time": The start time in seconds (float).
- "end_time": The end time in seconds (float).

Do not include any other text besides the JSON array."""

    start_time = time.time()
    response = model.generate_content(
        [prompt, audio_file],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
        )
    )
    duration = time.time() - start_time
    AI_REQUEST_LATENCY_SECONDS.labels(model="gemini-1.5-flash", operation="transcribe").observe(duration)
    
    try:
        genai.delete_file(audio_file.name)
    except Exception as e:
        print(f"Failed to delete gemini file: {e}")
        
    import json
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to parse transcript JSON: {e}")
        raise e

async def async_process_video(video_id_str: str):
    async with AsyncSessionLocal() as db:
        # 1. Fetch video record
        result = await db.execute(select(Video).where(Video.id == video_id_str))
        video = result.scalars().first()
        if not video:
            print(f"Video {video_id_str} not found in DB.")
            return
            
        try:
            video.status = "PROCESSING"
            await db.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                video_file_path = os.path.join(temp_dir, f"video_{video_id_str}.mp4")
                audio_file_path = os.path.join(temp_dir, f"audio_{video_id_str}.mp3")
                
                # 2. Download from MinIO
                print("Downloading video from MinIO...")
                success = await asyncio.to_thread(download_video_file, video.filename, video_file_path)
                if not success:
                    raise Exception("Failed to download video from MinIO")
                
                # 3. Extract Audio
                print("Extracting audio...")
                await asyncio.to_thread(extract_audio, video_file_path, audio_file_path)
                
                # 4. Transcribe Audio
                print("Transcribing audio with Gemini...")
                transcript_chunks = await asyncio.to_thread(transcribe_audio_with_gemini, audio_file_path)
                
                full_transcript = " ".join([chunk.get("text", "") for chunk in transcript_chunks])
                
                # 5. Embeddings
                print("Generating and storing vector embeddings...")
                await embed_and_store_chunks(db, video.id, transcript_chunks)
                
                # 6. Generate AI Outputs sequentially to prevent AsyncSession concurrency issues
                print("Generating Summaries, Flashcards, and Quiz...")
                await generate_and_store_summary(db, video.id, full_transcript)
                await generate_and_store_flashcards(db, video.id, full_transcript)
                await generate_and_store_quiz(db, video.id, full_transcript)
                
                # 7. Complete
                video.status = "COMPLETED"
                await db.commit()
                print(f"Successfully processed video {video_id_str}")
                
        except Exception as e:
            print(f"Error processing video {video_id_str}: {e}")
            video.status = "FAILED"
            await db.commit()
            raise

@celery_app.task(name="process_video")
def process_video_task(video_id_str: str):
    """
    A Celery task to process the uploaded video asynchronously.
    """
    asyncio.run(async_process_video(video_id_str))
    return {"status": "success", "video_id": video_id_str}
