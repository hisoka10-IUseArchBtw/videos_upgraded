import os
import time
import asyncio
import tempfile
import ffmpeg
from google import genai
from google.genai import types
from typing import List, Dict

from backend.core.celery_app import celery_app
from backend.core.database import AsyncSessionLocal
from backend.models.Video.video_model import Video
from sqlalchemy.future import select

from backend.services.storage import download_video_file, upload_local_file
from backend.ai.vision.ocr import process_frames_for_ocr
from backend.ai.embeddings.embedder import embed_and_store_chunks, embed_and_store_single_chunk
from backend.ai.summaries.generator import generate_and_store_summary
from backend.ai.chapters.generator import generate_and_store_chapters
from backend.ai.flashcards.generator import generate_and_store_flashcards
from backend.ai.quiz.generator import generate_and_store_quiz
from backend.ai.metrics import AI_REQUEST_LATENCY_SECONDS

# Configure Gemini for transcription
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

def extract_metadata(video_path: str) -> dict:
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if not video_stream:
            return {}
        duration = float(probe['format'].get('duration', 0.0))
        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        resolution = f"{width}x{height}"
        fps_str = video_stream.get('r_frame_rate', '0/1')
        num, den = map(float, fps_str.split('/'))
        fps = num / den if den != 0 else 0.0
        codec = video_stream.get('codec_name', '')
        return {
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
            "codec": codec
        }
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {}

def extract_scene_keyframes(video_path: str, output_dir: str) -> list:
    """Extracts keyframes at scene changes and returns a list of frame paths."""
    try:
        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
        (
            ffmpeg
            .input(video_path)
            .filter('select', 'gt(scene,0.3)')
            .output(output_pattern, vsync='vfr', qscale=2)
            .overwrite_output()
            .run(quiet=True)
        )
        frames = []
        for filename in sorted(os.listdir(output_dir)):
            if filename.endswith('.jpg'):
                frames.append(os.path.join(output_dir, filename))
        return frames
    except ffmpeg.Error as e:
        print(f"FFmpeg error during frame extraction: {e.stderr.decode() if e.stderr else e}")
        return []

def transcribe_audio_with_gemini(audio_path: str) -> List[Dict]:
    """Uploads the audio to Gemini and gets a timestamped JSON transcript."""
    print(f"Uploading {audio_path} to Gemini...")
    audio_file = client.files.upload(file=audio_path)
    
    # Wait for the file to be processed
    while audio_file.state.name == 'PROCESSING':
        print('.', end='')
        time.sleep(2)
        audio_file = client.files.get(name=audio_file.name)
    
    if audio_file.state.name == 'FAILED':
        raise ValueError("Audio processing failed in Gemini.")
    
    print("\nTranscribing...")
    
    prompt = """Please provide a complete transcript of this audio file.
Format your response as a valid JSON array of objects.
Each object should have:
- "text": The spoken text.
- "start_time": The start time in seconds (float).
- "end_time": The end time in seconds (float).

Do not include any other text besides the JSON array."""

    start_time = time.time()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[prompt, audio_file],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    duration = time.time() - start_time
    AI_REQUEST_LATENCY_SECONDS.labels(model="gemini-1.5-flash", operation="transcribe").observe(duration)
    
    try:
        client.files.delete(name=audio_file.name)
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
                
                # 2.5 Extract Video Metadata
                print("Extracting metadata...")
                metadata = await asyncio.to_thread(extract_metadata, video_file_path)
                if metadata:
                    video.duration = metadata.get("duration")
                    video.resolution = metadata.get("resolution")
                    video.fps = metadata.get("fps")
                    video.codec = metadata.get("codec")
                    await db.commit()
                
                # 3. Extract Audio
                print("Extracting audio...")
                await asyncio.to_thread(extract_audio, video_file_path, audio_file_path)
                
                # 4. Transcribe Audio
                print("Transcribing audio with Gemini...")
                transcript_chunks = await asyncio.to_thread(transcribe_audio_with_gemini, audio_file_path)
                
                full_transcript = " ".join([chunk.get("text", "") for chunk in transcript_chunks])
                
                # 5. Embeddings — index transcript chunks in Qdrant
                print("Generating and storing vector embeddings (transcript)...")
                await embed_and_store_chunks(db, video.id, transcript_chunks, chunk_type="transcript")
                
                # 5.5 Vision Intelligence (Frames & OCR)
                print("Extracting frames...")
                frames_dir = os.path.join(temp_dir, "frames")
                os.makedirs(frames_dir, exist_ok=True)
                frame_paths = await asyncio.to_thread(extract_scene_keyframes, video_file_path, frames_dir)
                
                # Upload frames to MinIO
                for frame_path in frame_paths:
                    filename = os.path.basename(frame_path)
                    object_name = f"frames/{video.id}/{filename}"
                    await asyncio.to_thread(upload_local_file, frame_path, object_name)
                    
                print("Running OCR on extracted frames...")
                ocr_results = await asyncio.to_thread(process_frames_for_ocr, frame_paths)
                if ocr_results:
                    print("Indexing OCR chunks in Qdrant...")
                    await embed_and_store_chunks(db, video.id, ocr_results, chunk_type="ocr")
                
                # 6. Generate AI Outputs sequentially to prevent AsyncSession concurrency issues
                print("Generating Chapters, Summaries, Flashcards, and Quiz...")
                
                chapters = await generate_and_store_chapters(db, video.id, transcript_chunks)
                if chapters:
                    chapter_chunks = []
                    for ch in chapters:
                        chapter_chunks.append({
                            "text": f"{ch.title}\n{ch.summary}",
                            "start_time": ch.start_time,
                            "end_time": ch.end_time
                        })
                    print("Indexing chapters in Qdrant...")
                    await embed_and_store_chunks(db, video.id, chapter_chunks, chunk_type="chapter")

                analysis = await generate_and_store_summary(db, video.id, full_transcript)
                await db.commit()  # flush so analysis.summary is readable
                
                # 6b. Index the summary in Qdrant so it's searchable
                if analysis and analysis.summary:
                    print("Indexing summary chunk in Qdrant...")
                    await embed_and_store_single_chunk(
                        db,
                        video.id,
                        text=analysis.summary,
                        chunk_type="summary",
                    )
                
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
