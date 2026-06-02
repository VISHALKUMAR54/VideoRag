import asyncio
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

_model: SentenceTransformer | None = None

# executor to run CPU-bound model encoding without blocking the loop
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bge_embedder")


# returns the cached model instance, loading it on first use
def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"  [Embedder] Loading model '{EMBEDDING_MODEL}' (first run downloads ~130MB)...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"  [Embedder] Model ready — dim={_model.get_sentence_embedding_dimension()}")
    return _model


# generates text embeddings synchronously
def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    model   = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


# runs embedding generation in executor for a list of chunk dicts
async def embed_chunks(chunks: list[dict]) -> list[dict]:
    if not chunks:
        return []

    texts  = [c["text"] for c in chunks]
    loop   = asyncio.get_event_loop()
    vectors = await loop.run_in_executor(_executor, embed_texts_sync, texts)

    print(f"  [Embedder] Embedded {len(chunks)} chunks | dim={len(vectors[0])}")
    return [
        {"vector": vec, **chunk}
        for vec, chunk in zip(vectors, chunks)
    ]


# embeds user query for similarity search
async def embed_question(question: str) -> list[float]:
    loop    = asyncio.get_event_loop()
    vectors = await loop.run_in_executor(_executor, embed_texts_sync, [question])
    return vectors[0]
