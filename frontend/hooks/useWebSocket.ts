"use client";
import { useState, useEffect, useRef, useCallback } from "react";

const BASE_WS = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const RECONNECT_DELAY_MS = 1000;

export function useWebSocket(jobId: string | null) {
  const [videoReady, setVideoReady] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback((id: string) => {
    if (wsRef.current) wsRef.current.close();
    const ws = new WebSocket(`${BASE_WS}/ws/${id}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.event === "video_ready" && data.video_id) {
          setVideoReady((prev) =>
            prev.includes(data.video_id) ? prev : [...prev, data.video_id]
          );
        }
      } catch {}
    };

    ws.onclose = () => {
      if (mountedRef.current) {
        setTimeout(() => { if (mountedRef.current && id) connect(id); }, RECONNECT_DELAY_MS);
      }
    };
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (jobId) connect(jobId);
    return () => {
      mountedRef.current = false;
      wsRef.current?.close();
    };
  }, [jobId, connect]);

  return { videoReady };
}
