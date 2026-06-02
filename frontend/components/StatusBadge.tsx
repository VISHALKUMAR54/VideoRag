"use client";

type Status = "idle" | "queued" | "fetching" | "embedding" | "ready" | "failed" | "waiting";

function resolveStatus(stage: string, pct: number): Status {
  if (stage === "idle") return "idle";
  if (stage === "ready") return "ready";
  if (stage === "failed") return "failed";
  if (stage === "queued") return "queued";
  if (stage === "waiting") return "waiting";
  if (pct >= 80) return "embedding";
  if (pct >= 5) return "fetching";
  return "queued";
}

const CONFIG: Record<Status, { label: string; dot: string; bg: string; text: string }> = {
  idle:      { label: "Idle",       dot: "#475569", bg: "rgba(71,85,105,0.12)",  text: "#94a3b8" },
  queued:    { label: "Queued",     dot: "#64748b", bg: "rgba(100,116,139,0.12)",text: "#94a3b8" },
  fetching:  { label: "Fetching",   dot: "#3b82f6", bg: "rgba(59,130,246,0.12)", text: "#93c5fd" },
  embedding: { label: "Embedding",  dot: "#f59e0b", bg: "rgba(245,158,11,0.12)", text: "#fcd34d" },
  ready:     { label: "Ready ✓",    dot: "#4ade80", bg: "rgba(74,222,128,0.12)", text: "#86efac" },
  failed:    { label: "Failed",     dot: "#f43f5e", bg: "rgba(244,63,94,0.12)",  text: "#fda4af" },
  waiting:   { label: "Waiting…",   dot: "#475569", bg: "rgba(71,85,105,0.08)",  text: "#64748b" },
};

interface StatusBadgeProps {
  stage: string;
  pct: number;
}

export function StatusBadge({ stage, pct }: StatusBadgeProps) {
  const status = resolveStatus(stage, pct);
  const cfg = CONFIG[status];
  return (
    <span
      className="status-badge"
      style={{ background: cfg.bg, color: cfg.text }}
    >
      <span className="status-dot" style={{ background: cfg.dot }} />
      {cfg.label}
    </span>
  );
}
