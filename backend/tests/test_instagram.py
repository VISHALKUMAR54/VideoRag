import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ingestion import ingest_instagram

IG_URL = "https://www.instagram.com/reel/DXQ3Yf6DXcO/"


# test instagram ingestion logic
async def main():
    if "REPLACE_ME" in IG_URL:
        print("⚠  Edit IG_URL at the top of this file before running.")
        sys.exit(1)

    print("=" * 60)
    print("TEST: Instagram Ingestion")
    print("=" * 60)
    print(f"URL: {IG_URL}\n")

    start = time.perf_counter()
    data  = await ingest_instagram(IG_URL, video_id="B")
    elapsed = time.perf_counter() - start

    print("\n── Metadata ─────────────────────────────────────────────")
    print(f"  Creator:         {data['creator']}")
    print(f"  Followers:       {data['follower_count']:,}" if data['follower_count'] else "  Followers:       N/A")
    print(f"  Views:           {data['views']:,}")
    print(f"  Likes:           {data['likes']:,}")
    print(f"  Comments:        {data['comments']:,}")
    print(f"  Engagement rate: {data['engagement_rate']}%")
    print(f"  Upload date:     {data['upload_date']}")
    print(f"  Duration:        {data['duration_seconds']}s")
    print(f"  Hashtags:        {data['hashtags'][:5]}")

    print("\n── Transcript (Whisper) ─────────────────────────────────")
    print(f"  Length:  {len(data['transcript'])} chars")
    print(f"  Preview: \"{data['transcript'][:200]}...\"")

    print("\n── Performance ──────────────────────────────────────────")
    print(f"  Total time:   {elapsed:.2f}s")
    dur = data['duration_seconds'] or 60
    print(f"  Whisper cost: ~${dur/60 * 0.006:.4f} (${0.006}/min × {dur}s)")

    print("\n── Verification ─────────────────────────────────────────")
    assert len(data['transcript']) > 50, \
        "FAIL: transcript too short — Whisper may have failed or reel has no speech"
    print("  ✓ Transcript length > 50 chars")

    assert data['video_id'] == "B", "FAIL: video_id should be 'B'"
    print("  ✓ video_id = 'B'")

    assert data['platform'] == "instagram", "FAIL: platform should be 'instagram'"
    print("  ✓ platform = 'instagram'")

    print("\n✓ PASSED — Instagram ingestion works correctly")


if __name__ == "__main__":
    asyncio.run(main())
