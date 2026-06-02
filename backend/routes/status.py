from fastapi import APIRouter, HTTPException
from models import StatusResponse
from state import get_job_state

router = APIRouter(tags=["status"])


# check ingestion progress for a specific job
@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    state = await get_job_state(job_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found. It may have expired (TTL=2h) or never existed."
        )
    return StatusResponse(
        pct=state.get("pct", 0),
        stage=state.get("stage", "unknown"),
        video_ready=state.get("video_ready", []),
        error=state.get("error"),
    )
