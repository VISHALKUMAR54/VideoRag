import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ingestion import ingest_youtube

YT_URL = "https://www.youtube.com/watch?v=V04ojClenZU"


# test youtube video ingestion logic
async def main():
    print("=" * 60)
    print("TEST: YouTube Ingestion")
    print("=" * 60)
    print(f"URL: {YT_URL}\n")

    data = await ingest_youtube(YT_URL, video_id="A")

    print("\n── Metadata ─────────────────────────────────────────────")
    print(f"  Title:           {data['title']}")
    print(f"  Creator:         {data['creator']}")
    print(f"  Views:           {data['views']:,}")
    print(f"  Likes:           {data['likes']:,}")
    print(f"  Comments:        {data['comments']:,}")
    print(f"  Engagement rate: {data['engagement_rate']}%")
    print(f"  Upload date:     {data['upload_date']}")
    print(f"  Duration:        {data['duration_seconds']}s")
    print(f"  Hashtags:        {data['hashtags'][:5]}")

    print("\n── Transcript ───────────────────────────────────────────")
    print(f"  Length:  {len(data['transcript'])} chars")
    print(f"  Preview: \"{data['transcript'][:200]}...\"")

    print("\n── Verification ─────────────────────────────────────────")
    if data['views'] > 0:
        expected_er = round((data['likes'] + data['comments']) / data['views'] * 100, 2)
        assert abs(expected_er - data['engagement_rate']) < 0.01, \
            f"FAIL: engagement_rate={data['engagement_rate']} but manual calc={expected_er}"
        print(f"  ✓ Engagement rate math correct: ({data['likes']} + {data['comments']}) / {data['views']} × 100 = {expected_er}%")
    else:
        print("  ⚠ Views = 0, skipping engagement rate check")

    assert len(data['transcript']) > 100, "FAIL: transcript is too short"
    print(f"  ✓ Transcript length > 100 chars")

    assert data['video_id'] == "A", "FAIL: video_id should be 'A'"
    print(f"  ✓ video_id = 'A'")

    print("\n✓ PASSED — YouTube ingestion works correctly")


if __name__ == "__main__":
    asyncio.run(main())
