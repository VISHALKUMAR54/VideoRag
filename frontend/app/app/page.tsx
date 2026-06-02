"use client";

import { useState } from "react";
import { VideoCard } from "@/components/VideoCard";
import { ChatPanel } from "@/components/ChatPanel";
import { IngestModal } from "@/components/IngestModal";
import { useIngest } from "@/hooks/useIngest";
import { useChat } from "@/hooks/useChat";
import { useWebSocket } from "@/hooks/useWebSocket";
import Link from "next/link";

export default function AppPage() {
  const [chatCollapsed, setChatCollapsed] = useState(false);
  const [modalOpen, setModalOpen] = useState(true);

  const { jobId, statusA, statusB, videoReady, metadataA, metadataB, error, isIngesting, ingest } =
    useIngest();
  const { videoReady: wsReady } = useWebSocket(jobId);
  const { messages, isStreaming, sendMessage } = useChat(jobId);

  const combinedReady = [...new Set([...videoReady, ...wsReady])];
  const isAReady = combinedReady.includes("A");
  const isBReady = combinedReady.includes("B");
  const bothReady = isAReady && isBReady;

  const handleModalSubmit = (ytUrl: string, igUrl: string) => {
    setModalOpen(false);
    ingest(ytUrl, igUrl);
  };

  // Dynamic card title: prefer video title over placeholder
  const titleA = metadataA?.title ?? (statusA.stage !== "idle" ? "YouTube Video" : "Video A");
  const titleB = metadataB?.title ?? (statusB.stage !== "idle" ? "Instagram Reel" : "Video B");

  return (
    <div className="app-root">
      {/* URL entry modal */}
      {modalOpen && <IngestModal onSubmit={handleModalSubmit} />}

      {/* Top bar */}
      <header className="app-topbar">
        <Link href="/" className="topbar-logo">
          <span className="logo-icon">◈</span> VideoRAG
        </Link>

        <div className="topbar-status">
          {!isIngesting && !bothReady && !error && (
            <span className="topbar-hint">Ingest videos to start chatting</span>
          )}
          {(isIngesting || bothReady) && (
            <span className={`status-pill ${bothReady ? "status-pill-ready" : "status-pill-loading"}`}>
              {bothReady
                ? "✓ Both Videos Ready"
                : `Ingesting… ${Math.max(statusA.pct, statusB.pct)}%`}
            </span>
          )}
          {error && <span className="error-pill">⚠ {error}</span>}
        </div>

        <button
          className="btn-ghost"
          onClick={() => setModalOpen(true)}
          title="Analyse new videos"
        >
          + New Analysis
        </button>
      </header>

      {/* 3-column grid */}
      <main
        className="app-grid"
        style={{ "--chat-collapsed": chatCollapsed ? "3rem" : "2fr" } as React.CSSProperties}
      >
        <section className="col-video col-a">
          <VideoCard
            label="A"
            cardTitle={titleA}
            platform="youtube"
            status={statusA}
            isReady={isAReady}
            metadata={metadataA}
            disabled={isIngesting}
          />
        </section>

        <section className="col-video col-b">
          <VideoCard
            label="B"
            cardTitle={titleB}
            platform="instagram"
            status={statusB}
            isReady={isBReady}
            metadata={metadataB}
            disabled={isIngesting}
          />
        </section>

        <section className="col-chat">
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            isReady={bothReady}
            onSend={sendMessage}
            isCollapsed={chatCollapsed}
            onToggleCollapse={() => setChatCollapsed((v) => !v)}
          />
        </section>
      </main>
    </div>
  );
}
