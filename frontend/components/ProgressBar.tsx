"use client";

interface ProgressBarProps {
  pct: number;
  stage: string;
}

const stageColor: Record<string, string> = {
  idle: "var(--surface-2)",
  queued: "#475569",
  "Starting ingestion": "#3b82f6",
  "Fetching YouTube transcript + Instagram metadata...": "#3b82f6",
  "All media fetched and transcribed.": "#3b82f6",
  "Transcripts ready — chunking...": "#8b5cf6",
  "Embedding chunks...": "#f59e0b",
  "Storing in vector DB...": "#f59e0b",
  ready: "#4ade80",
  failed: "#f43f5e",
  waiting: "#1e293b",
};

function getColor(stage: string): string {
  return stageColor[stage] ?? "#3b82f6";
}

export function ProgressBar({ pct, stage }: ProgressBarProps) {
  const color = getColor(stage);
  return (
    <div className="progress-wrap">
      <div
        className="progress-bar"
        style={{ width: `${pct}%`, background: color }}
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      />
      <span className="progress-label">{stage !== "idle" ? `${pct}% · ${stage}` : ""}</span>
    </div>
  );
}
