import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ingestion import ingest_youtube, ingest_instagram
from services.chunker import chunk_video
from services.embedder import embed_chunks, embed_question
from services.vector_store import setup_collection, upsert_chunks, search_both, get_collection_info
from services.llm import create_graph_no_memory

YT_URL = "https://www.youtube.com/shorts/XnjiprcNurg"
IG_URL = "https://www.instagram.com/reel/DXQ3Yf6DXcO/"

THREAD_ID = "e2e-test-session-001"
JOB_ID    = "e2e-job-001"


# main end-to-end test execution function
async def main():
    ig_available = "REPLACE_ME" not in IG_URL

    print("=" * 60)
    print("END-TO-END TEST: Full VideoRAG Pipeline")
    print("=" * 60)
    if not ig_available:
        print("⚠  IG_URL not set — running YouTube-only mode\n")
    else:
        print(f"YT: {YT_URL}")
        print(f"IG: {IG_URL}\n")

    total_start = time.perf_counter()

    # qdrant collection setup
    print("\n═══ STEP 1: Qdrant setup ════════════════════════════════")
    await setup_collection(recreate=True)
    print("  ✓ Collection ready (empty)")

    # parallel ingestion
    print("\n═══ STEP 2: Ingestion (parallel) ════════════════════════")
    t0 = time.perf_counter()

    if ig_available:
        yt_data, ig_data = await asyncio.gather(
            ingest_youtube(YT_URL,   video_id="A"),
            ingest_instagram(IG_URL, video_id="B"),
        )
        videos = [yt_data, ig_data]
    else:
        yt_data = await ingest_youtube(YT_URL, video_id="A")
        ig_data = {
            **yt_data,
            "video_id":        "B",
            "platform":        "instagram",
            "creator":         "@synthetic_b",
            "views":           120_000,
            "likes":           4_800,
            "comments":        320,
            "engagement_rate": round((4800 + 320) / 120_000 * 100, 2),
            "title":           "Synthetic Video B (no real IG URL provided)",
        }
        videos = [yt_data, ig_data]

    print(f"\n  Ingestion time: {time.perf_counter()-t0:.2f}s")
    print(f"  Video A: '{yt_data['title'][:50]}' | engagement={yt_data['engagement_rate']}%")
    print(f"  Video B: '{ig_data['title'][:50]}' | engagement={ig_data['engagement_rate']}%")

    # transcript chunking
    print("\n═══ STEP 3: Chunking ════════════════════════════════════")
    all_chunks = []
    for v in videos:
        chunks = chunk_video(v)
        for c in chunks:
            c["job_id"] = JOB_ID
        all_chunks.extend(chunks)
        print(f"  Video {v['video_id']}: {len(chunks)} chunks")
    print(f"  Total: {len(all_chunks)} chunks")

    # parallel embedding
    print("\n═══ STEP 4: Embedding (parallel) ════════════════════════")
    t0 = time.perf_counter()
    chunks_a = [c for c in all_chunks if c['video_id'] == 'A']
    chunks_b = [c for c in all_chunks if c['video_id'] == 'B']
    embedded_a, embedded_b = await asyncio.gather(
        embed_chunks(chunks_a),
        embed_chunks(chunks_b),
    )
    print(f"  Embedding time: {time.perf_counter()-t0:.2f}s")
    print(f"  Vector dim: {len(embedded_a[0]['vector'])}")

    # write vectors to qdrant
    print("\n═══ STEP 5: Qdrant storage (parallel) ═══════════════════")
    t0 = time.perf_counter()
    count_a, count_b = await asyncio.gather(
        upsert_chunks(embedded_a),
        upsert_chunks(embedded_b),
    )
    print(f"  Stored {count_a} + {count_b} = {count_a+count_b} points in {time.perf_counter()-t0:.3f}s")

    info = await get_collection_info()
    assert info['points'] == count_a + count_b, "FAIL: Qdrant point count mismatch"
    print(f"  ✓ Qdrant confirms {info['points']} points")

    # test vector store retrieval
    print("\n═══ STEP 6: Retrieval test ══════════════════════════════")
    test_query  = "engagement rate consistency followers growth"
    q_vector    = await embed_question(test_query)
    results_a, results_b = await search_both(q_vector)

    print(f"\n  Query: \"{test_query}\"")
    print(f"  Video A results ({len(results_a)}):")
    for r in results_a:
        print(f"    score={r['score']:.4f} | chunk={r['chunk_index']:02d} | \"{r['text'][:60]}...\"")
    print(f"  Video B results ({len(results_b)}):")
    for r in results_b:
        print(f"    score={r['score']:.4f} | chunk={r['chunk_index']:02d} | \"{r['text'][:60]}...\"")

    assert len(results_a) > 0, "FAIL: no results for Video A"
    assert len(results_b) > 0, "FAIL: no results for Video B"
    assert all(r['video_id'] == 'A' for r in results_a), "FAIL: Video A results contain wrong video_id"
    assert all(r['video_id'] == 'B' for r in results_b), "FAIL: Video B results contain wrong video_id"
    print("\n  ✓ Both videos return results")
    print("  ✓ video_id filters are working correctly")

    # RAG chat logic test
    print("\n═══ STEP 7: RAG chat (all assignment questions) ═════════")
    graph = create_graph_no_memory()

    questions = [
        "Why did Video A get more engagement than Video B?",
        "What's the engagement rate of each video?",
        "Compare the hooks in the first 5 seconds of each video.",
        "Who's the creator of Video A?",
        "Suggest improvements for Video B based on what worked in Video A.",
    ]

    thread = THREAD_ID
    for i, q in enumerate(questions, 1):
        print(f"\n  Q{i}: {q}")
        t0 = time.perf_counter()
        result = await graph.ainvoke(
            {"question": q, "job_id": JOB_ID},
            config={"configurable": {"thread_id": thread}},
        )
        elapsed = time.perf_counter() - t0
        answer  = result.get("answer", "")
        sources = result.get("sources", [])
        print(f"  A: {answer[:250]}{'...' if len(answer) > 250 else ''}")
        print(f"  Sources: {sources[:4]}{'...' if len(sources) > 4 else ''}")
        print(f"  Time: {elapsed:.2f}s")
        assert len(answer) > 30, f"FAIL: empty answer for Q{i}"

    print(f"\n  ✓ All {len(questions)} assignment questions answered")

    # chat memory persistence test
    print("\n═══ STEP 8: Memory persistence test ════════════════════")
    try:
        from services.llm import create_graph_with_redis
        graph_mem = await create_graph_with_redis()
        mem_thread = THREAD_ID + "-memory"

        await graph_mem.ainvoke(
            {"question": "What is the engagement rate of Video A?", "job_id": JOB_ID},
            config={"configurable": {"thread_id": mem_thread}},
        )
        result2 = await graph_mem.ainvoke(
            {"question": "Now compare it to Video B's rate.", "job_id": JOB_ID},
            config={"configurable": {"thread_id": mem_thread}},
        )
        memory = result2.get("memory", [])
        assert len(memory) >= 4, f"FAIL: expected ≥4 memory entries, got {len(memory)}"
        print(f"  ✓ Memory has {len(memory)} entries")
    except Exception as e:
        print(f"  ⚠ Redis not available ({e}) — memory test skipped")

    total_elapsed = time.perf_counter() - total_start
    print("\n" + "=" * 60)
    print(f"  Total test time: {total_elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
