"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "@/lib/types";

const SUGGESTED: string[] = [
  "Compare the hooks in the first 5 seconds",
  "What's the engagement rate of each video?",
  "Suggest improvements for Video B",
  "Why did one video outperform the other?",
];

interface ChatPanelProps {
  messages: Message[];
  isStreaming: boolean;
  isReady: boolean;
  onSend: (q: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function ChatPanel({ messages, isStreaming, isReady, onSend, isCollapsed, onToggleCollapse }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const q = input.trim();
    if (!q || isStreaming || !isReady) return;
    setInput("");
    onSend(q);
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const lastAiMsg = [...messages].reverse().find((m) => m.role === "assistant" && !m.streaming);
  const showSuggested = !isStreaming && messages.length === 0;

  /* ── Collapsed sidebar strip ── */
  if (isCollapsed) {
    return (
      <div className="chat-panel chat-collapsed">
        <button
          id="chat-collapse-toggle"
          className="chat-expand-btn"
          onClick={onToggleCollapse}
          aria-label="Expand chat"
          title="Expand chat"
        >
          {/* Sidebar-open icon */}
          <svg width="1.15em" height="1.15em" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="2" width="16" height="16" rx="3" />
            <line x1="7" y1="2" x2="7" y2="18" />
            <polyline points="11,7 14,10 11,13" />
          </svg>
          <span className="expand-label">Chat</span>
        </button>
      </div>
    );
  }

  return (
    <div className="chat-panel chat-expanded">
      {/* Header with collapse toggle pinned to top-right */}
      <div className="chat-header">
        <span className="chat-title">Chat</span>
        {!isReady && (
          <span className="chat-hint">Ingest both videos to start chatting</span>
        )}
        <button
          id="chat-collapse-toggle"
          className="chat-collapse-btn"
          onClick={onToggleCollapse}
          aria-label="Collapse chat"
          title="Collapse chat"
        >
          {/* Sidebar-close icon */}
          <svg width="1.15em" height="1.15em" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="2" width="16" height="16" rx="3" />
            <line x1="7" y1="2" x2="7" y2="18" />
            <polyline points="10,7 7,10 10,13" />
          </svg>
        </button>
      </div>

      {/* Message list */}
      <div className="message-list" role="log" aria-live="polite">
        {messages.length === 0 && showSuggested && (
          <div className="suggestions-intro">
            <p className="suggest-label">Try asking:</p>
            <div className="suggest-pills">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  className="suggest-pill"
                  onClick={() => isReady && onSend(s)}
                  disabled={!isReady}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Suggested follow-ups after last AI reply */}
        {lastAiMsg && !isStreaming && (
          <div className="followup-pills">
            {SUGGESTED.slice(0, 2).map((s) => (
              <button
                key={s}
                className="suggest-pill followup-pill"
                onClick={() => onSend(s)}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="chat-input-bar">
        <textarea
          ref={inputRef}
          id="chat-input"
          className="chat-textarea"
          placeholder={isReady ? "Ask anything about the videos…" : "Waiting for ingestion to complete…"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={!isReady || isStreaming}
          rows={2}
          aria-label="Chat input"
        />
        <button
          id="chat-send-btn"
          className={`send-btn ${isStreaming ? "send-streaming" : ""}`}
          onClick={handleSend}
          disabled={!isReady || isStreaming || !input.trim()}
          aria-label="Send message"
        >
          {isStreaming ? (
            <span className="spinner" />
          ) : (
            <svg width="1.2em" height="1.2em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
