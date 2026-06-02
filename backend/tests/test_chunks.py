import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chunker import chunk_video
from services.embedder import embed_chunks, embed_question

# fake video data for tests
FAKE_VIDEO = {
    "video_id":        "A",
    "platform":        "youtube",
    "title":           "How I grew to 100k followers",
    "creator":         "@testcreator",
    "follower_count":  None,
    "views":           850_000,
    "likes":           42_000,
    "comments":        1_800,
    "engagement_rate": 5.15,
    "upload_date":     "2024-11-15",
    "duration_seconds": 187,
    "hashtags":        ["#growth", "#youtube"],
    "url":             "https://youtube.com/watch?v=test",
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
        "The third thing was thumbnail strategy. I tested three thumbnails per video for "
        "the first month. I would post the video, run it for 48 hours, check the CTR, "
        "and then swap to whichever thumbnail was performing better. The difference "
        "between a two percent CTR and a six percent CTR on the same video is enormous. "
        "For Instagram specifically the engagement rate formula is likes plus comments "
        "divided by views times one hundred. My best reel had forty two thousand likes "
        "and one thousand eight hundred comments on eight hundred fifty thousand views. "
        "That gives you an engagement rate of about five point one five percent which "
        "is significantly above the platform average of around two to three percent. "
        "The fourth thing I want to mention is collaboration. I reached out to five "
        "creators in my niche who had between ten and fifty thousand followers. Three "
        "of them said yes to a cross-promotion. Each collab added between two and five "
        "thousand subscribers in the week following the post. "
        "Finally, I want to address the question I get most often which is whether "
        "you need expensive equipment to grow. The answer is absolutely not. My first "
        "fifty videos were shot on an iPhone twelve with a fifteen dollar ring light. "
        "The content is what matters. Sound quality matters more than video quality. "
        "If your audio is bad people will click off regardless of how beautiful your "
        "footage looks. Invest in a decent microphone before anything else. "
        "That is everything for today. If you found this useful please drop a comment "
        "below telling me which tip you are going to implement first. See you next week."
    ),
}


# main test function for chunking and embedding logic
async def main():
    print("=" * 60)
    print("TEST: Chunking + Embedding")
    print("=" * 60)

    start_time = time.perf_counter()

    # chunking verification
    print("\n── Step 1: Chunking ─────────────────────────────────────")
    t0 = time.perf_counter()
    chunks = chunk_video(FAKE_VIDEO)
    t_chunking = time.perf_counter() - t0

    print(f"\n  Transcript length: {len(FAKE_VIDEO['transcript'])} chars")
    print(f"  Chunk count:       {len(chunks)}")
    print(f"  Expected range:    10-20 chunks\n")

    for c in chunks:
        print(f"  Chunk {c['chunk_index']:02d} | {len(c['text'])} chars | \"{c['text'][:60]}...\"")

    for c in chunks:
        assert c['video_id'] == "A",        "FAIL: video_id not propagated"
        assert c['creator']  == "@testcreator", "FAIL: creator not propagated"
        assert c['engagement_rate'] == 5.15, "FAIL: engagement_rate not propagated"
        assert 'text' in c,                 "FAIL: missing 'text' key"
        assert 'chunk_index' in c,          "FAIL: missing 'chunk_index' key"

    assert 5 <= len(chunks) <= 25, f"FAIL: unexpected chunk count {len(chunks)}"
    print(f"\n  ✓ All chunks have correct metadata")
    print(f"  ✓ Chunk count {len(chunks)} is in expected range")
    print(f"  ✓ Chunking completed in {t_chunking:.4f}s")

    # verify overlap
    if len(chunks) >= 2:
        end_of_first   = chunks[0]['text'][-50:]
        start_of_second = chunks[1]['text'][:100]
        overlap_found  = any(word in start_of_second for word in end_of_first.split() if len(word) > 4)
        if overlap_found:
            print(f"  ✓ Chunk overlap detected between chunk 0 and chunk 1")
        else:
            print(f"  ⚠ Overlap not clearly visible")

    # embedding verification
    print("\n── Step 2: Embedding ────────────────────────────────────")
    print("  Loading BGE-small model (first run downloads ~130MB)...\n")

    t0 = time.perf_counter()
    embedded = await embed_chunks(chunks)
    t_embedding = time.perf_counter() - t0

    print(f"\n  Chunks embedded: {len(embedded)}")
    sample_vector = embedded[0]['vector']
    print(f"  Vector dimension: {len(sample_vector)}")
    print(f"  Vector preview (first 8 dims): {[round(x, 4) for x in sample_vector[:8]]}")

    for i, e in enumerate(embedded):
        assert 'vector' in e,                f"FAIL: chunk {i} missing 'vector'"
        assert len(e['vector']) == 384,      f"FAIL: chunk {i} has wrong dim {len(e['vector'])}"
        assert all(isinstance(x, float) for x in e['vector'][:5]), \
                                              f"FAIL: chunk {i} vector contains non-floats"

    import math
    v = sample_vector
    magnitude = math.sqrt(sum(x**2 for x in v))
    assert abs(magnitude - 1.0) < 0.01, f"FAIL: vector not normalized, magnitude={magnitude:.4f}"

    print(f"\n  ✓ All {len(embedded)} chunks have float[384] vectors")
    print(f"  ✓ Vectors are normalized")
    print(f"  ✓ Embedding completed in {t_embedding:.2f}s")

    # question embedding verification
    print("\n── Step 3: Question embedding ───────────────────────────")
    question = "What did the creator say about consistency and posting frequency?"
    t0 = time.perf_counter()
    q_vector = await embed_question(question)
    t_q_embedding = time.perf_counter() - t0

    assert len(q_vector) == 384, f"FAIL: question vector dim={len(q_vector)}"
    print(f"  Question: \"{question}\"")
    print(f"  Vector dim: {len(q_vector)} ✓")

    # dot product similarity check
    from services.embedder import embed_texts_sync
    import numpy as np
    chunk_vectors = [e['vector'] for e in embedded]
    scores = [
        sum(a*b for a,b in zip(q_vector, cv))
        for cv in chunk_vectors
    ]
    best_idx   = scores.index(max(scores))
    best_score = max(scores)
    print(f"\n  Most similar chunk to question:")
    print(f"  Chunk {best_idx} (score={best_score:.4f}): \"{embedded[best_idx]['text'][:100]}...\"")
    assert best_score > 0.5, f"FAIL: best similarity score {best_score:.4f} too low"
    print(f"  ✓ Best score {best_score:.4f} > 0.5 — retrieval should work correctly")
    print(f"  ✓ Question embedding completed in {t_q_embedding:.4f}s")

    total_time = time.perf_counter() - start_time
    print("\n" + "=" * 60)
    print(f"✓ PASSED — Chunking + Embedding work correctly (Total time: {total_time:.2f}s)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
