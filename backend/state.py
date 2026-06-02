import json
import redis.asyncio as aioredis
from config import REDIS_URL

# job state expires after 2 hours
JOB_TTL_SECONDS = 7200

_redis: aioredis.Redis | None = None

def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

def _key(job_id: str) -> str:
    return f"job:{job_id}"

async def set_job_state(job_id: str, state: dict) -> None:
    r = get_redis()
    await r.setex(_key(job_id), JOB_TTL_SECONDS, json.dumps(state))

async def get_job_state(job_id: str) -> dict | None:
    r = get_redis()
    raw = await r.get(_key(job_id))
    return json.loads(raw) if raw else None

# partial update — merges kwargs into existing state
async def update_job_state(job_id: str, **kwargs) -> None:
    current = await get_job_state(job_id) or {}
    current.update(kwargs)
    await set_job_state(job_id, current)

# marks a video as ready and pushes a websocket event via redis pub/sub
async def mark_video_ready(job_id: str, video_id: str) -> None:
    current = await get_job_state(job_id) or {}
    ready = current.get("video_ready", [])
    if video_id not in ready:
        ready.append(video_id)
    current["video_ready"] = ready
    await set_job_state(job_id, current)
    r = get_redis()
    await r.publish(f"ws:{job_id}", json.dumps({"event": "video_ready", "video_id": video_id}))