export interface VideoMetadata {
  video_id: string;
  platform: string;
  title: string;
  creator: string;
  views: number;
  likes: number;
  comments: number;
  engagement_rate: number;
  upload_date: string | null;
  duration_seconds: number;
  hashtags: string[];
  follower_count: number | null;
  url: string;
  thumbnail_url?: string | null;  // Instagram CDN cover frame (may be absent)
}

export interface IngestResponse {
  job_id: string;
  status: string;
}

export interface StatusResponse {
  pct: number;
  stage: string;
  video_ready: string[];
  error: string | null;
}

export interface MetadataResponse {
  metadata_a: VideoMetadata | null;
  metadata_b: VideoMetadata | null;
}

export interface TimingsResponse {
  timings: Record<string, number>;
  video_duration_a_s: number | null;
  video_duration_b_s: number | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  sources?: SourceChunk[];
}

export interface SourceChunk {
  video_id: string;
  chunk_index: number;
  score: number;
  text: string;
}
