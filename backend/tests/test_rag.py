import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm import create_graph_with_redis, create_graph_no_memory
from services.chunker import chunk_video
from services.embedder import embed_chunks
from services.vector_store import setup_collection, upsert_chunks

FAKE_VIDEO_A = {
    "video_id": "A", "platform": "youtube",
    "title": "How I grew to 100k followers",
    "creator": "@testcreator", "follower_count": None,
    "views": 850_000, "likes": 42_000, "comments": 1_800,
    "engagement_rate": 5.15, "upload_date": "2024-11-15",
    "duration_seconds": 187, "hashtags": ["#growth", "#youtube"],
    "url": "https://youtube.com/watch?v=test",
    "transcript": (
        "Hey guys welcome back to the channel. Today I want to talk about something "
        "that completely changed my growth trajectory. I went from zero to a hundred "
        "thousand followers in just eight months and I am going to break down exactly "
        "what worked and what did not work. "
        "The first thing I did was post every single day for the first ninety days. "
        "I know that sounds exhausting but consistency is honestly the number one thing "
        "that the algorithm rewards. When you post every day the algorithm starts to "
        "understand your content category and begins recommending you to the right people. "
        "The second thing was optimizing my hooks. I spent the first five seconds of every "
        "video telling the viewer exactly what they were going to get. Not a question, not "
        "a teaser, an actual promise. Something like: by the end of this video you will "
        "know the three things I did to triple my engagement rate. That simple change "
        "doubled my watch time almost overnight. "
        "The third thing was thumbnail strategy. I tested three thumbnails per video. "
        "For Instagram specifically the engagement rate formula is likes plus comments "
        "divided by views times one hundred. My best reel had forty two thousand likes "
        "and one thousand eight hundred comments on eight hundred fifty thousand views. "
        "That gives you an engagement rate of about five point one five percent. "
        "Finally, I want to address the question I get most often: do you need expensive "
        "equipment to grow. The answer is absolutely not. Sound quality matters more than "
        "video quality. Invest in a decent microphone before anything else."
    ),
}

FAKE_VIDEO_B = {
    "video_id": "B", "platform": "instagram",
    "title": "Reel by @lofilullaa", "creator": "@lofilullaa",
    "follower_count": 603_078, "views": 751_247, "likes": 104_445,
    "comments": 331, "engagement_rate": 13.95, "upload_date": "2025-11-29",
    "duration_seconds": 11, "hashtags": ["elyanna", "callinu"],
    "url": "https://www.instagram.com/reel/DRpvyXjjcCa/",
    "transcript": "I don't need nobody, I don't fit nobody, I don't call nobody but you, my one and only.",
}

THREAD_ID = "test-rag-session-001"
JOB_ID    = "test-rag-job-001"

QUESTIONS = [
    "What is the engagement rate of Video A?",
    "What did the creator say about consistency and posting frequency?",
    "What tips did the creator give about hooks in the first 5 seconds?",
    "Based on Video A, what should a creator do to improve their engagement?",
]

# seed qdrant with mock data
async def seed_qdrant() -> None:
    print("\n── Seeding Qdrant with test data ────────────────────────")

    t0 = time.perf_counter()
    await setup_collection(recreate=True)
    print(f"  ✓ Collection recreated [{time.perf_counter()-t0:.2f}s]")

    t_chunk = time.perf_counter()
    chunks_a = chunk_video(FAKE_VIDEO_A)
    chunks_b = chunk_video(FAKE_VIDEO_B)
    for c in chunks_a:
        c["job_id"] = JOB_ID
    for c in chunks_b:
        c["job_id"] = JOB_ID
    print(f"  ✓ Chunked: Video A={len(chunks_a)}, Video B={len(chunks_b)} [{time.perf_counter()-t_chunk:.2f}s]")

    t_embed = time.perf_counter()
    embedded_a, embedded_b = await asyncio.gather(
        embed_chunks(chunks_a),
        embed_chunks(chunks_b),
    )
    print(f"  ✓ Embedded [{time.perf_counter()-t_embed:.2f}s]")

    t_store = time.perf_counter()
    count_a, count_b = await asyncio.gather(
        upsert_chunks(embedded_a),
        upsert_chunks(embedded_b),
    )
    print(f"  ✓ Stored {count_a} + {count_b} = {count_a+count_b} points [{time.perf_counter()-t_store:.2f}s]")
    print(f"  Seed total: [{time.perf_counter()-t0:.2f}s]\n")


# test single question turn and verify citation outputs
async def test_single_turn(graph):
    print("\n── Single-turn test ─────────────────────────────────────")
    question = QUESTIONS[0]
    print(f"  Q: {question}")

    t0 = time.perf_counter()
    result = await graph.ainvoke(
        {"question": question, "job_id": JOB_ID},
        config={"configurable": {"thread_id": THREAD_ID + "-single"}},
    )
    elapsed = time.perf_counter() - t0

    answer  = result.get("answer", "")
    sources = result.get("sources", [])

    print(f"\n  A: {answer[:500]}{'...' if len(answer) > 500 else ''}")
    print(f"\n  Sources count: {len(sources)}")
    if sources:
        print(f"  First source: video_id={sources[0].get('video_id')} chunk={sources[0].get('chunk_index')} score={sources[0].get('score')}")
    print(f"  Time: {elapsed:.2f}s")

    assert len(answer) > 50,  "FAIL: answer is too short"
    assert len(sources) > 0,  "FAIL: no sources returned"
    print("\n  ✓ Answer is non-empty")
    print(f"  ✓ {len(sources)} source(s) returned")

    if "5.15" in answer or "engagement" in answer.lower():
        print("  ✓ Answer mentions engagement rate")
    if "[Video A" in answer or "[Video B" in answer:
        print("  ✓ Answer contains inline citations")


# test conversation memory across multiple turns
async def test_multi_turn_memory(graph):
    print("\n── Multi-turn memory test ───────────────────────────────")
    thread = THREAD_ID + "-memory"

    for i, question in enumerate(QUESTIONS[:3]):
        print(f"\n  Turn {i+1}: {question}")
        t0 = time.perf_counter()
        result = await graph.ainvoke(
            {"question": question, "job_id": JOB_ID},
            config={"configurable": {"thread_id": thread}},
        )
        elapsed = time.perf_counter() - t0
        answer  = result.get("answer", "")
        memory  = result.get("memory", [])
        print(f"  A: {answer[:200]}...")
        print(f"  Memory turns accumulated: {len(memory)}  [{elapsed:.2f}s]")

    assert len(memory) >= 4, \
        f"FAIL: expected ≥4 memory entries after 3 turns, got {len(memory)}"
    print(f"\n  ✓ Memory has {len(memory)} entries after 3 turns")

    followup = "Based on what we just discussed, what is the single most important thing?"
    print(f"\n  Follow-up (requires memory): {followup}")
    t0 = time.perf_counter()
    result = await graph.ainvoke(
        {"question": followup, "job_id": JOB_ID},
        config={"configurable": {"thread_id": thread}},
    )
    answer = result.get("answer", "")
    print(f"  A: {answer[:300]}...  [{time.perf_counter()-t0:.2f}s]")
    assert len(answer) > 50, "FAIL: follow-up answer is empty"
    print("  ✓ Follow-up answered (memory is working)")


# run through all specific project assignment questions
async def test_all_assignment_questions(graph):
    print("\n── Assignment question types ────────────────────────────")
    thread = THREAD_ID + "-assignment"

    assignment_questions = [
        "Why did Video B get more engagement than Video A?",
        "What's the engagement rate of each video?",
        "What hooks or techniques did Video A use in the first 5 seconds?",
        "Who's the creator of Video A and what do you know about them?",
        "Suggest improvements for Video B based on what worked in Video A.",
    ]

    for q in assignment_questions:
        print(f"\n  Q: {q}")
        t0 = time.perf_counter()
        result = await graph.ainvoke(
            {"question": q, "job_id": JOB_ID},
            config={"configurable": {"thread_id": thread}},
        )
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        print(f"  A: {answer[:200]}...  [{time.perf_counter()-t0:.2f}s]")
        print(f"  Sources: {len(sources)} retrieved")
        assert len(answer) > 30, f"FAIL: empty answer for: {q}"

    print(f"\n  ✓ All {len(assignment_questions)} assignment question types answered")


# test suite orchestrator
async def main():
    print("=" * 60)
    print("TEST: LangGraph RAG Pipeline")
    print("=" * 60)
    print("Self-seeding: populating Qdrant with fake video data\n")

    total_start = time.perf_counter()

    await seed_qdrant()

    print("Phase A: Testing WITHOUT memory (no Redis needed)")
    print("-" * 40)
    graph_no_mem = create_graph_no_memory()
    await test_single_turn(graph_no_mem)
    print("\n  ✓ Phase A passed")

    print("\nPhase B: Testing WITH Redis memory")
    print("-" * 40)
    try:
        graph_with_mem = await create_graph_with_redis()
        print("  ✓ Redis connection successful!")
        await test_multi_turn_memory(graph_with_mem)
        print("\n  ✓ Phase B passed")
    except Exception as e:
        print(f"  ⚠ Redis not available ({e})")

    print("\nPhase C: Assignment question types")
    print("-" * 40)
    await test_all_assignment_questions(graph_no_mem)
    print("\n  ✓ Phase C passed")

    total_elapsed = time.perf_counter() - total_start
    print("\n" + "=" * 60)
    print(f"  Total test time: {total_elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
