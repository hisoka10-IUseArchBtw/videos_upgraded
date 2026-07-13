import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "video_chunks")
VECTOR_SIZE = 768  # Gemini text-embedding-004 output dimension

# ---------------------------------------------------------------------------
# Singleton client — reused across the entire application lifetime
# ---------------------------------------------------------------------------
_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Return the module-level AsyncQdrantClient singleton."""
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=QDRANT_URL)
    return _client


async def ensure_collection() -> None:
    """
    Creates the Qdrant collection if it doesn't already exist.

    Called once during FastAPI lifespan startup so the application is always
    ready to index and search without manual setup steps.

    Collection config:
    - 768-dimensional vectors (Gemini text-embedding-004)
    - Cosine distance (best for semantic similarity of unit-normalised embeddings)
    - Payload indexes on `video_id` and `chunk_type` for fast filtered search
    """
    client = get_qdrant_client()
    collections = await client.get_collections()
    existing_names = {c.name for c in collections.collections}

    if QDRANT_COLLECTION_NAME not in existing_names:
        await client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[Qdrant] Created collection '{QDRANT_COLLECTION_NAME}'")

        # Index payload fields used in every filtered search
        await client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="video_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="chunk_type",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("[Qdrant] Payload indexes created on 'video_id' and 'chunk_type'")
    else:
        print(f"[Qdrant] Collection '{QDRANT_COLLECTION_NAME}' already exists — skipping creation")
