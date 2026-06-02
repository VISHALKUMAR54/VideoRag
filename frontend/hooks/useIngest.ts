"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { postIngest, getStatus, getMetadata, getTimings } from "@/lib/api";
import type { VideoMetadata, StatusResponse, TimingsResponse } from "@/lib/types";

const POLL_MS = 2000;

export function useIngest() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusA, setStatusA] = useState({ pct: 0, stage: "idle" });
  const [statusB, setStatusB] = useState({ pct: 0, stage: "idle" });
  const [videoReady, setVideoReady] = useState<string[]>([]);
  const [metadataA, setMetadataA] = useState<VideoMetadata | null>(null);
  const [metadataB, setMetadataB] = useState<VideoMetadata | null>(null);
  const [timings, setTimings] = useState<TimingsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = () => {
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const fetchMetadataAndTimings = useCallback(async (id: string) => {
    try {
      const [meta, tim] = await Promise.all([getMetadata(id), getTimings(id)]);
      setMetadataA(meta.metadata_a);
      setMetadataB(meta.metadata_b);
      setTimings(tim);
    } catch {
      // metadata not fatal — video cards still show partial info
    }
  }, []);

  const startPoll = useCallback((id: string) => {
    pollRef.current = setInterval(async () => {
      try {
        const s: StatusResponse = await getStatus(id);
        const pct = s.pct;
        const stage = s.stage;

        // Split progress: 0-50 is Video A (YT), 50-100 is Video B (IG)
        if (pct <= 50) {
          setStatusA({ pct: Math.min(pct * 2, 100), stage });
          setStatusB({ pct: 0, stage: "waiting" });
        } else {
          setStatusA({ pct: 100, stage: "ready" });
          setStatusB({ pct: (pct - 50) * 2, stage });
        }

        setVideoReady(s.video_ready);

        if (s.error) {
          setError(s.error);
          stopPoll();
          setIsIngesting(false);
        }

        if (s.pct === 100) {
          setStatusA({ pct: 100, stage: "ready" });
          setStatusB({ pct: 100, stage: "ready" });
          stopPoll();
          setIsIngesting(false);
          await fetchMetadataAndTimings(id);
        }
      } catch (e) {
        setError(String(e));
        stopPoll();
        setIsIngesting(false);
      }
    }, POLL_MS);
  }, [fetchMetadataAndTimings]);

  const ingest = useCallback(async (ytUrl: string, igUrl: string) => {
    stopPoll();
    setError(null);
    setIsIngesting(true);
    setMetadataA(null);
    setMetadataB(null);
    setTimings(null);
    setVideoReady([]);
    setStatusA({ pct: 0, stage: "queued" });
    setStatusB({ pct: 0, stage: "queued" });
    try {
      const res = await postIngest(ytUrl, igUrl);
      setJobId(res.job_id);
      startPoll(res.job_id);
    } catch (e) {
      setError(String(e));
      setIsIngesting(false);
    }
  }, [startPoll]);

  useEffect(() => () => stopPoll(), []);

  return { jobId, statusA, statusB, videoReady, metadataA, metadataB, timings, error, isIngesting, ingest };
}
