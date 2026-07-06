# Phase 2 — What You Need

## What Phase 2 Adds

Replace the fake `time.sleep(5)` in `video_worker.py` with a **real AI pipeline** that:
1. Downloads the video from MinIO
2. Transcribes it (audio → text)
3. Sends the transcript to an LLM to produce summaries, flashcards, quizzes
4. Generates vector embeddings and stores them for semantic search
5. Exposes APIs for chat-with-video and search

---

## 1. New Infrastructure (Docker Services)

You need two new containers added to `docker-compose.yml`:

| Service | Image | Why |
|---|---|---|
| **pgvector** (replace Postgres) | `pgvector/pgvector:pg16` | Store vector embeddings in Postgres itself |
| **Qdrant** (alternative) | `qdrant/qdrant` | Dedicated vector DB (pick one of the two above) |

> [!IMPORTANT]
> Pick either **pgvector** (simpler, already have Postgres) or **Qdrant** (more scalable). pgvector is the recommended starting point.

Also needed as **Python packages** (no new containers):
- `google-generativeai` — Gemini API (transcription + LLM)
- `openai` — alternative provider (if needed)
- `sentence-transformers` or `google-generativeai` embed endpoint — embeddings
- `pgvector` — SQLAlchemy integration for vector columns
- `ffmpeg-python` — extract audio from video before transcription

---

## 2. New DB Models

Three new tables on top of `videos`:

### `video_analyses` — AI outputs per video
```
id, video_id (FK), summary (Text), key_topics (JSON), created_at
```

### `flashcards` — per video
```
id, video_id (FK), question (Text), answer (Text), created_at
```

### `quiz_questions` — per video
```
id, video_id (FK), question (Text), options (JSON), correct_answer (str), created_at
```

### `video_chunks` — transcript segments + embeddings (for search/chat)
```
id, video_id (FK), chunk_index (int), text (Text), embedding (Vector(768)), start_time (float), end_time (float)
```

---

## 3. AI Module — `backend/ai/`

All empty directories need to be filled:

### `ai/providers/` — LLM clients
- `gemini.py` — Gemini client init (uses `GEMINI_API_KEY` from `.env`)
- `base.py` — abstract `AIProvider` interface

### `ai/prompts/` — Prompt templates
- `summary_prompt.py`
- `flashcard_prompt.py`
- `quiz_prompt.py`
- `chat_prompt.py`

### `ai/summaries/`
- `generator.py` — calls LLM with transcript, returns summary + key topics

### `ai/flashcards/`
- `generator.py` — calls LLM, returns list of `{question, answer}`

### `ai/quiz/`
- `generator.py` — calls LLM, returns list of `{question, options[], correct_answer}`

### `ai/embeddings/`
- `embedder.py` — chunks transcript, generates embedding per chunk, stores in DB

### `ai/routing/`
- `analysis.py` — FastAPI router: `GET /ai/{video_id}/summary`, `/flashcards`, `/quiz`

---

## 4. Real Worker Pipeline — `video_worker.py`

Replace `time.sleep(5)` with actual steps:

```
process_video(video_id)
  ├── 1. Download video from MinIO → temp file
  ├── 2. Extract audio (ffmpeg)
  ├── 3. Transcribe audio (Gemini / Whisper)
  ├── 4. Chunk transcript → generate embeddings → store in video_chunks
  ├── 5. Generate summary → store in video_analyses
  ├── 6. Generate flashcards → store in flashcards table
  ├── 7. Generate quiz → store in quiz_questions table
  └── 8. Set video.status = COMPLETED
```

---

## 5. Chat Module — `backend/chat/`

- `router.py` — `POST /chat/{video_id}` accepts a user question
- `engine.py` — RAG pipeline:
  1. Embed the question
  2. Similarity search in `video_chunks`
  3. Stuff top-k chunks into prompt
  4. Call LLM → return answer

---

## 6. Search Module — `backend/search/`

- `router.py` — `GET /search?q=...` or `POST /search`
- `engine.py` — embeds query, does vector similarity search across all video chunks for the current user

---

## 7. New API Routes to Register in `main.py`

```python
from backend.ai.routing import analysis
from backend.chat import router as chat_router
from backend.search import router as search_router

app.include_router(analysis.router)   # /ai/...
app.include_router(chat_router.router) # /chat/...
app.include_router(search_router.router) # /search/...
```

---

## 8. New Env Variables Needed

Add to `backend/core/.env`:
```
GEMINI_API_KEY=your_key_here
```

---

## Build Order (Recommended Sequence)

```
1. Add pgvector to docker-compose + enable extension in DB
2. Create new DB models (video_analyses, flashcards, quiz_questions, video_chunks)
3. Build ai/providers/gemini.py (LLM client)
4. Build ai/summaries, ai/flashcards, ai/quiz generators
5. Build ai/embeddings/embedder.py
6. Wire real pipeline into video_worker.py
7. Build ai/routing (GET endpoints for AI outputs)
8. Build chat/ (RAG Q&A)
9. Build search/ (semantic search)
10. Register all routers in main.py
```
