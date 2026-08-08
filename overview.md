# Video Understanding Engine

> **A production-grade AI platform that transforms long-form videos — lectures, meetings, podcasts, and interviews — into searchable, interactive knowledge.**

---

## Overview

The **Video Understanding Engine (VUE)** is a full-stack, distributed AI system designed to ingest video content and extract deep, structured understanding from it. Users can upload videos and get back transcripts, chapter breakdowns, AI-generated summaries, flashcards, quizzes, semantic search, and a RAG-powered chat interface — all grounded in timestamps so answers can be traced back to the source.

The system is built with production engineering in mind: async job queues, containerized microservices, vector search, observability via Prometheus + Grafana, and a Kubernetes-ready infrastructure layer.

---

## Core Capabilities

| Feature | Description |
|---|---|
| **Video Upload & Storage** | Upload pipeline backed by MinIO (S3-compatible object storage) |
| **Async Processing** | Celery workers handle video ingestion, frame extraction, transcription, and AI analysis in the background |
| **Transcription** | Whisper-based speech-to-text with word-level timestamps and speaker diarization |
| **Vision Analysis** | FFmpeg frame extraction + Tesseract OCR for reading slides, whiteboards, and on-screen text |
| **AI Knowledge Extraction** | LLM-powered generation of summaries, chapters, flashcards, quizzes, and glossaries |
| **Semantic Search** | Embedding-based search (via FastEmbed + Qdrant) across transcripts, OCR, and chapters |
| **RAG Chat** | Ask natural-language questions about a video; answers are grounded with timestamp citations |
| **Analytics Dashboard** | Processing metrics, token usage, queue status, and search logs |
| **Observability** | Prometheus metrics exposed from FastAPI, visualized in a Grafana dashboard |

---

## Architecture

```
                    Frontend (Next.js / TypeScript)
                               │
                               ▼
                    FastAPI Gateway  (:8000)
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   Auth Service          Video API            Search / Chat
          │
          ▼
   MinIO Object Storage  (:9000)
          │
          ▼
    Celery + Redis Job Queue  (:6379)
          │
   ┌──────┼──────────────┬──────────────┐
   ▼      ▼              ▼              ▼
 Audio  Frame          OCR           AI / Embedding
Worker  Worker        Worker          Workers
          │
          ▼
  PostgreSQL (:5433) + Qdrant (:6333)
          │
          ▼
       RAG Chat API
```

---

## Tech Stack

### Backend

| Layer | Technology | Purpose |
|---|---|---|
| **API Framework** | [FastAPI](https://fastapi.tiangolo.com/) `v0.138` | Async REST API gateway |
| **Task Queue** | [Celery](https://docs.celeryq.dev/) `v5.6` | Distributed background workers |
| **Message Broker / Cache** | [Redis](https://redis.io/) `7-alpine` | Celery broker + caching layer |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) `v2.0` (async) | Database modeling and queries |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) | Schema versioning |
| **Validation** | [Pydantic](https://docs.pydantic.dev/) `v2` | Request/response schemas |
| **Auth** | [PyJWT](https://pyjwt.readthedocs.io/) + [Argon2](https://github.com/hynek/argon2-cffi) | JWT authentication + password hashing |

### Database & Storage

| Layer | Technology | Purpose |
|---|---|---|
| **Relational DB** | [PostgreSQL](https://www.postgresql.org/) `16` | Users, videos, analysis metadata |
| **Vector DB** | [Qdrant](https://qdrant.tech/) | Semantic embeddings for search & RAG |
| **Object Storage** | [MinIO](https://min.io/) | S3-compatible video & asset storage |

### AI / ML

| Layer | Technology | Purpose |
|---|---|---|
| **LLM Provider (Primary)** | [Google Gemini](https://ai.google.dev/) (`google-genai`) | Summaries, quizzes, chapters, flashcards |
| **LLM Provider (Secondary)** | [Groq](https://groq.com/) | Fast inference alternative |
| **Embeddings** | [FastEmbed](https://github.com/qdrant/fastembed) | Text embeddings for semantic search |
| **Speech-to-Text** | Whisper (planned) | Transcription with word timestamps |
| **Speaker Diarization** | Pyannote (planned) | Multi-speaker attribution |
| **Video Processing** | [FFmpeg](https://ffmpeg.org/) via `ffmpeg-python` | Frame extraction, audio splitting |
| **OCR** | [Tesseract](https://github.com/tesseract-ocr/tesseract) via `pytesseract` | Slide and whiteboard text reading |
| **Image Processing** | [Pillow](https://python-pillow.org/) + NumPy | Frame manipulation and analysis |

### Frontend

| Layer | Technology | Purpose |
|---|---|---|
| **Framework** | [Next.js](https://nextjs.org/) `14` | React-based SSR/SPA frontend |
| **Language** | TypeScript `5` | Type-safe component development |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/) `3.4` | Utility-first styling |

### Infrastructure & Observability

| Layer | Technology | Purpose |
|---|---|---|
| **Containerization** | [Docker](https://www.docker.com/) + Docker Compose | Local dev and service orchestration |
| **Orchestration** | [Kubernetes](https://kubernetes.io/) | Production cluster deployment (planned) |
| **Metrics** | [Prometheus](https://prometheus.io/) + `prometheus-fastapi-instrumentator` | API and system metrics scraping |
| **Dashboards** | [Grafana](https://grafana.com/) | Visualizing metrics with custom dashboards |
| **Error Tracking** | [Sentry](https://sentry.io/) SDK | Runtime error capture |

---

## Project Structure

```
videos_upgraded/
├── video-understanding-engine/
│   ├── backend/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/                 # Routers: auth, video, analytics
│   │   ├── ai/                  # AI modules
│   │   │   ├── chapters/        # Chapter detection
│   │   │   ├── embeddings/      # Embedding generation
│   │   │   ├── flashcards/      # Flashcard generation
│   │   │   ├── quiz/            # Quiz generation
│   │   │   ├── summaries/       # Summarization
│   │   │   ├── vision/          # Frame/OCR analysis
│   │   │   ├── prompts/         # LLM prompt templates
│   │   │   └── providers/       # Gemini / Groq clients
│   │   ├── auth/                # JWT auth logic
│   │   ├── chat/                # RAG chat router
│   │   ├── search/              # Qdrant semantic search
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── services/            # Business logic services
│   │   ├── workers/             # Celery task definitions
│   │   │   ├── video_worker.py  # Main processing pipeline
│   │   │   ├── ingestion/       # Upload & storage tasks
│   │   │   ├── intelligence/    # AI enrichment tasks
│   │   │   ├── indexing/        # Embedding indexing tasks
│   │   │   └── exports/         # Export tasks
│   │   ├── core/                # Settings, DB, config
│   │   └── utils/               # Shared utilities
│   ├── frontend/
│   │   └── src/
│   │       ├── app/             # Next.js app router pages
│   │       ├── components/      # Reusable UI components
│   │       ├── providers/       # React context providers
│   │       └── services/        # API client calls
│   └── infrastructure/
│       ├── monitoring/
│       │   ├── prometheus.yml   # Prometheus scrape config
│       │   └── grafana/         # Grafana dashboards & datasources
│       └── kubernetes/          # K8s manifests (in progress)
├── roadmap.md                   # Full phased build plan
├── directories.md               # Detailed directory reference
└── map.md                       # Project map
```

---

## Development Phases

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation — auth, upload, job queue | ✅ Done |
| 2 | Video Processing — frames, audio, metadata | ✅ Done |
| 3 | Speech Intelligence — transcription, diarization | 🔄 In Progress |
| 4 | Vision Intelligence — OCR, scene detection, captioning | 🔄 In Progress |
| 5 | AI Knowledge Extraction — summaries, quizzes, flashcards | ✅ Done |
| 6 | Semantic Search — Qdrant embeddings + vector search | ✅ Done |
| 7 | AI Chat — RAG pipeline with citations | ✅ Done |
| 8 | Interactive Timeline — chapter navigation | 🔄 In Progress |
| 9 | Analytics — dashboards and usage tracking | ✅ Done |
| 10 | Production Engineering — Docker, K8s, Prometheus, Grafana | 🔄 In Progress |

---

## Running Locally

```bash
# Start all backend services (Postgres, Redis, MinIO, Qdrant, Prometheus, Grafana)
cd video-understanding-engine
docker compose up -d

# Run the FastAPI backend (outside Docker for dev)
cd backend
uvicorn backend.main:app --reload --port 8000

# Run the Celery worker
celery -A backend.workers.video_worker worker --loglevel=info --concurrency=2

# Run the Next.js frontend
cd frontend
npm run dev
```

### Service Ports

| Service | Port |
|---|---|
| FastAPI API | `8000` |
| Next.js Frontend | `3000` |
| PostgreSQL | `5433` |
| Redis | `6379` |
| MinIO API | `9000` |
| MinIO Console | `9001` |
| Qdrant | `6333` |
| Prometheus | `9090` |
| Grafana | `3001` |
