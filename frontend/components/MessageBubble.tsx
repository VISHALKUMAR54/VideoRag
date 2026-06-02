"use client";

import { Message } from "@/lib/types";

const CITATION_A = /\[Video A,?\s*chunk\s*(\d+)\]/gi;
const CITATION_B = /\[Video B,?\s*chunk\s*(\d+)\]/gi;

function parseCitations(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let last = 0;
  const combined: { index: number; match: RegExpExecArray; video: "A" | "B" }[] = [];
  let m: RegExpExecArray | null;

  const rA = new RegExp(CITATION_A.source, "gi");
  const rB = new RegExp(CITATION_B.source, "gi");

  while ((m = rA.exec(text)) !== null) combined.push({ index: m.index, match: m, video: "A" });
  while ((m = rB.exec(text)) !== null) combined.push({ index: m.index, match: m, video: "B" });
  combined.sort((a, b) => a.index - b.index);

  for (const { index, match, video } of combined) {
    if (index > last) parts.push(text.slice(last, index));
    parts.push(
      <span
        key={`${video}-${match[1]}-${index}`}
        className={video === "A" ? "cite-badge cite-a" : "cite-badge cite-b"}
      >
        Video {video}, chunk {match[1]}
      </span>
    );
    last = index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const lines = message.content.split("\n");

  return (
    <div className={`bubble-wrap ${isUser ? "bubble-user" : "bubble-ai"}`}>
      <div className={`bubble ${isUser ? "bubble-user-inner" : "bubble-ai-inner"}`}>
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="bubble-content">
            {lines.map((line, i) => (
              <p key={i}>{parseCitations(line)}</p>
            ))}
            {message.streaming && <span className="cursor-blink">▋</span>}
          </div>
        )}
      </div>
    </div>
  );
}
