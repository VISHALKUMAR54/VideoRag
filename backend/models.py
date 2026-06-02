from pydantic import BaseModel
from typing import Optional, List, Dict

class IngestRequest(BaseModel):
    yt_url: str
    ig_url: str

class IngestResponse(BaseModel):
    job_id: str
    status: str  # always "queued"

class StatusResponse(BaseModel):
    pct:         int
    stage:       str
    video_ready: List[str]
    error:       Optional[str]

class ChatRequest(BaseModel):
    question:  str
    thread_id: str  # conversation id — generated server-side, stored client-side
    job_id:    str  # links chat to an ingestion job

class ChatResponse(BaseModel):
    answer:  str
    sources: List[str]

class VideoMetadata(BaseModel):
    video_id:         str
    platform:         str
    title:            str
    creator:          str
    views:            int
    likes:            int
    comments:         int
    engagement_rate:  float
    upload_date:      Optional[str]
    duration_seconds: int
    hashtags:         List[str]
    follower_count:   Optional[int]
    url:              str
    thumbnail_url:    Optional[str] = None

class MetadataResponse(BaseModel):
    metadata_a: Optional[VideoMetadata]
    metadata_b: Optional[VideoMetadata]

class TimingsResponse(BaseModel):
    timings:              Dict[str, float]
    video_duration_a_s:   Optional[int]
    video_duration_b_s:   Optional[int]