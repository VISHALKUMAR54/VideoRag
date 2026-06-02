from fastapi import APIRouter, HTTPException
from models import TimingsResponse
from state import get_job_state

router = APIRouter(tags=["timings"])


# retrieve execution durations and video lengths for a job
@router.get("/timings/{job_id}", response_model=TimingsResponse)
async def get_timings(job_id: str) -> TimingsResponse:
    state = await get_job_state(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return TimingsResponse(
        timings=state.get("timings", {}),
        video_duration_a_s=state.get("metadata_a", {}).get("duration_seconds") if state.get("metadata_a") else None,
        video_duration_b_s=state.get("metadata_b", {}).get("duration_seconds") if state.get("metadata_b") else None,
    )
