import asyncio
import time
import uuid

from fastapi import APIRouter, BackgroundTasks

from models import IngestRequest, IngestResponse
from services.chunker import chunk_video
from services.embedder import embed_chunks
from services.ingestion import run_ingestion_pipeline
from services.vector_store import setup_collection, upsert_chunks
from state import mark_video_ready, set_job_state, update_job_state

router = APIRouter(tags=["ingestion"])


# update job progress state
async def _on_progress(job_id: str, pct: int, stage: str) -> None:
    await update_job_state(job_id, pct=pct, stage=stage)


# complete ingestion pipeline in the background
async def _full_pipeline(yt_url: str, ig_url: str, job_id: str) -> None:
    try:
        _t_pipeline_start = time.perf_counter()

        await update_job_state(job_id, pct=5, stage="Starting ingestion")
        _t_ingest_start = time.perf_counter()

        yt_data, ig_data = await run_ingestion_pipeline(
            yt_url, ig_url, job_id,
            on_progress=_on_progress,
        )
        _t_ingest_ms = (time.perf_counter() - _t_ingest_start) * 1000

        await mark_video_ready(job_id, "A")
        await update_job_state(job_id, pct=50, stage="Transcripts ready — chunking...")

        chunks_a = chunk_video(yt_data)
        chunks_b = chunk_video(ig_data)
        for c in chunks_a:
            c["job_id"] = job_id
        for c in chunks_b:
            c["job_id"] = job_id
        print(f"  [Ingest] job={job_id} | Video A: {len(chunks_a)} chunks, Video B: {len(chunks_b)} chunks")

        await update_job_state(job_id, pct=65, stage="Embedding chunks...")
        _t_embed_start = time.perf_counter()
        embedded_a, embedded_b = await asyncio.gather(
            embed_chunks(chunks_a),
            embed_chunks(chunks_b),
        )
        _t_embed_ms = (time.perf_counter() - _t_embed_start) * 1000

        await update_job_state(job_id, pct=80, stage="Storing in vector DB...")
        await setup_collection(recreate=False)
        _t_upsert_start = time.perf_counter()
        count_a, count_b = await asyncio.gather(
            upsert_chunks(embedded_a),
            upsert_chunks(embedded_b),
        )
        _t_upsert_ms = (time.perf_counter() - _t_upsert_start) * 1000
        print(f"  [Ingest] job={job_id} | Stored {count_a} + {count_b} = {count_a+count_b} points")

        _meta_keys = {
            "video_id", "platform", "title", "creator", "views", "likes",
            "comments", "engagement_rate", "upload_date", "duration_seconds",
            "hashtags", "follower_count", "url", "thumbnail_url",
        }
        metadata_a = {k: v for k, v in yt_data.items() if k in _meta_keys} if yt_url.strip() else None
        metadata_b = {k: v for k, v in ig_data.items() if k in _meta_keys} if ig_url.strip() else None
        if metadata_a:
            metadata_a.setdefault("platform", "youtube")

        timings = {
            "ingest_total_ms":   _t_ingest_ms,
            "embedding_ms":      _t_embed_ms,
            "qdrant_upsert_ms":  _t_upsert_ms,
            "pipeline_total_ms": (time.perf_counter() - _t_pipeline_start) * 1000,
        }

        await mark_video_ready(job_id, "B")
        await update_job_state(
            job_id,
            pct=100,
            stage="Ready",
            video_ready=["A", "B"],
            error=None,
            metadata_a=metadata_a,
            metadata_b=metadata_b,
            timings=timings,
        )
        print(f"  [Ingest] job={job_id} ✓ Pipeline complete")

    except Exception as exc:
        print(f"  [Ingest] job={job_id} ✗ Pipeline FAILED: {exc}")
        await update_job_state(
            job_id,
            pct=0,
            stage="failed",
            error=str(exc),
        )


# start the ingestion pipeline in the background
@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, background_tasks: BackgroundTasks) -> IngestResponse:
    job_id = str(uuid.uuid4())

    await set_job_state(job_id, {
        "pct":         0,
        "stage":       "queued",
        "video_ready": [],
        "error":       None,
    })

    background_tasks.add_task(_full_pipeline, req.yt_url, req.ig_url, job_id)
    print(f"[Ingest] job={job_id} queued | YT={req.yt_url[:50]} | IG={req.ig_url[:50]}")

    return IngestResponse(job_id=job_id, status="queued")
