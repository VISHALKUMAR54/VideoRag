from fastapi import APIRouter, HTTPException
from models import MetadataResponse, VideoMetadata
from state import get_job_state

router = APIRouter(tags=["metadata"])


# helper to map raw state dict to VideoMetadata model
def _to_model(raw: dict | None) -> VideoMetadata | None:
    if not raw:
        return None
    return VideoMetadata(
        video_id=raw.get("video_id", ""),
        platform=raw.get("platform", "youtube"),
        title=raw.get("title", ""),
        creator=raw.get("creator", ""),
        views=int(raw.get("views", 0)),
        likes=int(raw.get("likes", 0)),
        comments=int(raw.get("comments", 0)),
        engagement_rate=float(raw.get("engagement_rate", 0.0)),
        upload_date=raw.get("upload_date"),
        duration_seconds=int(raw.get("duration_seconds", 0)),
        hashtags=raw.get("hashtags", []),
        follower_count=raw.get("follower_count"),
        url=raw.get("url", ""),
        thumbnail_url=raw.get("thumbnail_url") or None,
    )


# retrieve metadata for both ingested videos
@router.get("/metadata/{job_id}", response_model=MetadataResponse)
async def get_metadata(job_id: str) -> MetadataResponse:
    state = await get_job_state(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return MetadataResponse(
        metadata_a=_to_model(state.get("metadata_a")),
        metadata_b=_to_model(state.get("metadata_b")),
    )
