"use client";

import type { VideoMetadata } from "@/lib/types";
import { ProgressBar } from "./ProgressBar";
import { StatusBadge } from "./StatusBadge";

interface VideoCardProps {
  label: "A" | "B";
  cardTitle: string;
  platform: "youtube" | "instagram";
  status: { pct: number; stage: string };
  isReady: boolean;
  metadata: VideoMetadata | null;
  disabled?: boolean;
}

function ytThumbnail(url: string): string | null {
  const m = url.match(/(?:v=|\/shorts\/|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return m ? `https://img.youtube.com/vi/${m[1]}/maxresdefault.jpg` : null;
}

function InstagramPlaceholder({ creator, title }: { creator: string; title: string }) {
  const initials = creator.replace("@", "").slice(0, 2).toUpperCase() || "IG";
  return (
    <div className="ig-placeholder">
      <span className="ig-initials">{initials}</span>
      <span className="ig-title">{title.slice(0, 40)}{title.length > 40 ? "…" : ""}</span>
    </div>
  );
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function VideoCard({ label, cardTitle, platform, status, isReady, metadata, disabled }: VideoCardProps) {
  // YouTube: derive thumbnail from video ID in the URL (public CDN, no CORS issues)
  // Instagram: route through our backend proxy to bypass the CDN's CORP header
  //   Direct CDN URLs from Instagram return Cross-Origin-Resource-Policy: same-origin,
  //   which blocks browsers from loading them cross-origin. The proxy re-serves them
  //   from localhost:8000 with Cross-Origin-Resource-Policy: cross-origin.
  const thumb = metadata
    ? platform === "youtube"
      ? ytThumbnail(metadata.url)
      : metadata.thumbnail_url
        ? `${API_BASE}/thumbnail?url=${encodeURIComponent(metadata.thumbnail_url)}`
        : null
    : null;
  const accentVar = label === "A" ? "var(--accent-a)" : "var(--accent-b)";

  return (
    <div
      className={`video-card ${isReady ? "video-card-ready" : ""}`}
      style={{ "--card-accent": accentVar } as React.CSSProperties}
    >
      <div className="card-header">
        <span className="card-label" style={{ color: accentVar, maxWidth: "70%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {cardTitle}
        </span>
        <span className="platform-badge">
          {platform === "youtube" ? "▶ YouTube" : "◉ Instagram"}
        </span>
        <StatusBadge stage={status.stage} pct={status.pct} />
      </div>

      {/* Thumbnail */}
      <div className="thumb-wrap">
        {thumb ? (
          <img src={thumb} alt={metadata?.title ?? "thumbnail"} className="thumb-img" loading="lazy" />
        ) : metadata ? (
          <InstagramPlaceholder creator={metadata.creator} title={metadata.title} />
        ) : (
          <div className="thumb-empty">
            <span style={{ color: accentVar, fontSize: "2.5rem", opacity: 0.35 }}>
              {platform === "youtube" ? "▶" : "◉"}
            </span>
          </div>
        )}
      </div>

      {/* Metadata */}
      {metadata && (
        <div className="meta-section">
          <h3 className="meta-title">{metadata.title}</h3>
          <p className="meta-creator">{metadata.creator}</p>
          <div className="meta-stats">
            <div className="stat">
              <span className="stat-icon">👁</span>
              <span className="stat-value">{fmt(metadata.views)}</span>
              <span className="stat-label">views</span>
            </div>
            <div className="stat">
              <span className="stat-icon">❤️</span>
              <span className="stat-value">{fmt(metadata.likes)}</span>
              <span className="stat-label">likes</span>
            </div>
            <div className="stat">
              <span className="stat-icon">💬</span>
              <span className="stat-value">{fmt(metadata.comments)}</span>
              <span className="stat-label">comments</span>
            </div>
            <div className="stat stat-eng">
              <span className="stat-icon">📈</span>
              <span className="stat-value" style={{ color: accentVar }}>{metadata.engagement_rate}%</span>
              <span className="stat-label">engagement</span>
            </div>
          </div>
          {metadata.hashtags?.length > 0 && (
            <div className="hashtags">
              {metadata.hashtags.slice(0, 5).map((tag) => (
                <span key={tag} className="hashtag">#{tag}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Progress — only while ingesting, hidden once ready */}
      {status.stage !== "idle" && !isReady && (
        <div className="card-footer">
          <ProgressBar pct={status.pct} stage={status.stage} />
        </div>
      )}
    </div>
  );
}
