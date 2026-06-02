"use client";

import { useState, useEffect, useRef } from "react";

interface IngestModalProps {
  onSubmit: (ytUrl: string, igUrl: string) => void;
}

export function IngestModal({ onSubmit }: IngestModalProps) {
  const [ytUrl, setYtUrl] = useState("");
  const [igUrl, setIgUrl] = useState("");
  const ytRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    ytRef.current?.focus();
  }, []);

  const canAnalyse = ytUrl.trim().length > 0 || igUrl.trim().length > 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canAnalyse) return;
    onSubmit(ytUrl.trim(), igUrl.trim());
  };

  return (
    <div className="modal-overlay">
      <div className="modal-backdrop" aria-hidden />
      <div className="modal-card" role="dialog" aria-modal="true" aria-label="Add video URLs">
        {/* Glow orbs inside modal */}
        <div className="modal-orb modal-orb-a" aria-hidden />
        <div className="modal-orb modal-orb-b" aria-hidden />

        <div className="modal-header">
          <span className="modal-logo"><span className="logo-icon">◈</span> VideoRAG</span>
          <h2 className="modal-title">Analyse Your Videos</h2>
          <p className="modal-sub">Add at least one video URL to begin. Both videos unlock full comparison mode.</p>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {/* YouTube */}
          <div className="modal-field">
            <label htmlFor="modal-yt" className="modal-label">
              <span className="modal-label-icon" style={{ color: "#22d3ee" }}>▶</span>
              YouTube URL
              <span className="modal-label-optional">optional if Instagram added</span>
            </label>
            <input
              ref={ytRef}
              id="modal-yt"
              type="url"
              className="modal-input modal-input-a"
              placeholder="https://youtube.com/watch?v=..."
              value={ytUrl}
              onChange={(e) => setYtUrl(e.target.value)}
              autoComplete="off"
            />
          </div>

          {/* Divider */}
          <div className="modal-divider">
            <span className="modal-divider-line" />
            <span className="modal-divider-text">and / or</span>
            <span className="modal-divider-line" />
          </div>

          {/* Instagram */}
          <div className="modal-field">
            <label htmlFor="modal-ig" className="modal-label">
              <span className="modal-label-icon" style={{ color: "#f472b6" }}>◉</span>
              Instagram Reel URL
              <span className="modal-label-optional">optional if YouTube added</span>
            </label>
            <input
              id="modal-ig"
              type="url"
              className="modal-input modal-input-b"
              placeholder="https://instagram.com/reel/..."
              value={igUrl}
              onChange={(e) => setIgUrl(e.target.value)}
              autoComplete="off"
            />
          </div>

          {!canAnalyse && (
            <p className="modal-hint">⚡ Add at least one URL to enable analysis</p>
          )}

          <button
            id="modal-analyse-btn"
            type="submit"
            className="btn-primary btn-lg modal-submit"
            disabled={!canAnalyse}
          >
            {canAnalyse ? "Start Analysis →" : "Add a URL above"}
          </button>
        </form>

        <p className="modal-footer-note">
          Transcripts are fetched server-side · No login required · Data expires in 2h
        </p>
      </div>
    </div>
  );
}
