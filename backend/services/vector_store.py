import asyncio
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from config import (
    COLLECTION_NAME,
    EMBEDDING_DIM,
    QDRANT_HOST,
    QDRANT_PORT,
    RETRIEVAL_TOP_K,
)

_client: AsyncQdrantClient | None = None


# returns singleton async client instance
def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client


# ensures qdrant collection is created
async def setup_collection(recreate: bool = False) -> None:
    client = get_client()

    if recreate:
        existing = await client.get_collections()
        names = [c.name for c in existing.collections]
        if COLLECTION_NAME in names:
            await client.delete_collection(COLLECTION_NAME)
            print(f"  [VectorStore] Collection '{COLLECTION_NAME}' deleted (recreate=True)")

    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if COLLECTION_NAME not in names:
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        print(
            f"  [VectorStore] Created collection '{COLLECTION_NAME}' "
            f"(dim={EMBEDDING_DIM}, distance=COSINE)"
        )
    else:
        print(f"  [VectorStore] Collection '{COLLECTION_NAME}' already exists — skipping create")


# returns basic collection information
async def get_collection_info() -> dict:
    client = get_client()
    info   = await client.get_collection(COLLECTION_NAME)
    return {
        "name":   COLLECTION_NAME,
        "points": info.points_count,
    }


# stores chunk vectors in Qdrant
async def upsert_chunks(embedded_chunks: list[dict]) -> int:
    if not embedded_chunks:
        return 0

    client = get_client()

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk["vector"],
            payload={k: v for k, v in chunk.items() if k != "vector"},
        )
        for chunk in embedded_chunks
    ]

    await client.upsert(collection_name=COLLECTION_NAME, points=points)

    print(
        f"  [VectorStore] Upserted {len(points)} points "
        f"(video_id={embedded_chunks[0].get('video_id', '?')})"
    )
    return len(points)


# searches vector database for a specific video id
async def search(
    q_vector: list[float],
    video_id: str,
    k:        int = RETRIEVAL_TOP_K,
    job_id:   str | None = None,
) -> list[dict]:
    client = get_client()

    must_conditions = [
        FieldCondition(key="video_id", match=MatchValue(value=video_id))
    ]
    if job_id:
        must_conditions.append(
            FieldCondition(key="job_id", match=MatchValue(value=job_id))
        )

    response = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vector,
        query_filter=Filter(must=must_conditions),
        limit=k,
        with_payload=True,
    )
    results = response.points

    return [
        {
            "score": r.score,
            **r.payload,
        }
        for r in results
    ]


# search video A and video B collections in parallel
async def search_both(
    q_vector: list[float],
    k:        int = RETRIEVAL_TOP_K,
    job_id:   str | None = None,
) -> tuple[list[dict], list[dict]]:
    results_a, results_b = await asyncio.gather(
        search(q_vector, video_id="A", k=k, job_id=job_id),
        search(q_vector, video_id="B", k=k, job_id=job_id),
    )
    return results_a, results_b
