"use client";
import { useState, useRef, useCallback } from "react";
import { chatStream } from "@/lib/api";
import type { Message } from "@/lib/types";

export function useChat(jobId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const threadId = useRef(
    typeof crypto !== "undefined" ? crypto.randomUUID() : Math.random().toString(36)
  );

  const sendMessage = useCallback(async (question: string) => {
    if (!jobId || isStreaming) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question };
    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = { id: assistantId, role: "assistant", content: "", streaming: true };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    try {
      const res = await chatStream(question, threadId.current, jobId);
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") break;
          if (data.startsWith("[ERROR]")) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: "⚠ " + data.slice(8), streaming: false } : m
              )
            );
            break;
          }
          // SSE escapes newlines as \\n
          const token = data.replace(/\\n/g, "\n");
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m
            )
          );
        }
      }
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: `⚠ Error: ${e}`, streaming: false } : m
        )
      );
    } finally {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m))
      );
      setIsStreaming(false);
    }
  }, [jobId, isStreaming]);

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, isStreaming, sendMessage, clearMessages, threadId: threadId.current };
}
