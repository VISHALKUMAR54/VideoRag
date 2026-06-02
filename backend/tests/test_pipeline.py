import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ingestion import ingest_youtube
from services.chunker import chunk_video
from services.embedder import embed_chunks, embed_question
from services.vector_store import setup_collection, upsert_chunks, search, get_collection_info

YT_URL = "https://www.youtube.com/shorts/XnjiprcNurg"


# test full pipeline: ingest, chunk, embed, store, search
async def main():
    print("=" * 60)
    print("TEST: Full Ingestion Pipeline → Qdrant")
    print("=" * 60)

    # qdrant collection setup
    print("── Step 1: Qdrant collection setup ──────────────────────")
    await setup_collection(recreate=True)
    info = await get_collection_info()
    print(f"  Collection '{info['name']}' ready — {info['points']} points")
    assert info['points'] == 0, "FAIL: collection should be empty after recreate"
    print("  ✓ Collection is empty (clean start)")

    # ingest youtube
    print("\n── Step 2: YouTube ingestion ────────────────────────────")
    t0      = time.perf_counter()
    yt_data = await ingest_youtube(YT_URL, video_id="A")
    print(f"  Ingested in {time.perf_counter()-t0:.2f}s")

    # chunking
    print("\n── Step 3: Chunking ─────────────────────────────────────")
    chunks = chunk_video(yt_data)
    print(f"  {len(yt_data['transcript'])} chars → {len(chunks)} chunks")
    assert len(chunks) > 0, "FAIL: chunking produced 0 chunks"

    # embedding
    print("\n── Step 4: Embedding ────────────────────────────────────")
    t0       = time.perf_counter()
    embedded = await embed_chunks(chunks)
    print(f"  Embedded {len(embedded)} chunks in {time.perf_counter()-t0:.2f}s")
    print(f"  Vector dim: {len(embedded[0]['vector'])}")
    assert len(embedded[0]['vector']) == 384, "FAIL: wrong embedding dimension"

    # store in qdrant
    print("\n── Step 5: Storing in Qdrant ────────────────────────────")
    t0    = time.perf_counter()
    count = await upsert_chunks(embedded)
    print(f"  Stored {count} points in {time.perf_counter()-t0:.3f}s")

    info = await get_collection_info()
    assert info['points'] == count, \
        f"FAIL: Qdrant has {info['points']} points but we upserted {count}"
    print(f"  ✓ Qdrant confirms {info['points']} points stored")

    # semantic search
    print("\n── Step 6: Semantic search ──────────────────────────────")
    queries = [
        "what did the creator say about consistency?",
        "how to improve engagement rate?",
        "tips for growing followers on social media",
    ]

    for q in queries:
        q_vector = await embed_question(q)
        results  = await search(q_vector, video_id="A", k=3)

        print(f"\n  Query: \"{q}\"")
        print(f"  Results ({len(results)}):")
        for r in results:
            print(f"    score={r['score']:.4f} | chunk={r['chunk_index']:02d} | \"{r['text'][:70]}...\"")

        assert len(results) > 0, f"FAIL: no results for query '{q}'"
        assert results[0]['score'] > 0.3, \
            f"FAIL: top score {results[0]['score']:.4f} too low"
        assert all(r['video_id'] == "A" for r in results), \
            "FAIL: results contain wrong video_id"

    print("\n── Final verification ───────────────────────────────────")
    print("  ✓ All queries returned results")
    print("  ✓ All results have video_id='A'")
    print("  ✓ Scores above minimum threshold")

    # verify wrong video_id returns 0 results
    print("\n── Step 7: video_id filter isolation ───────────────────")
    q_vector = await embed_question("anything")
    results_b = await search(q_vector, video_id="B", k=3)
    assert len(results_b) == 0, \
        f"FAIL: video_id='B' search returned results"
    print("  ✓ Searching video_id='B' returns 0 results")

    print("\n" + "=" * 60)
    print("✓ PASSED — Full pipeline works: ingest → chunk → embed → store → search")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
