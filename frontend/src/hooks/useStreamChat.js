import { useCallback, useEffect, useRef, useState } from "react";
import api, { API_URL } from "../api/api";

/**
 * Parse one SSE event block into its text. Multiple `data:` lines are rejoined with "\n"
 * (the server splits tokens containing newlines into several data lines).
 */
function parseEvent(block) {
  const lines = block.split("\n").filter((l) => l.startsWith("data:"));
  if (!lines.length) return null;
  return lines.map((l) => (l.startsWith("data: ") ? l.slice(6) : l.slice(5))).join("\n");
}

/** Chat state + streaming send. Tokens are appended to the last AI message as they arrive. */
export function useStreamChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const appendToLast = useCallback((text) => {
    setMessages((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = { ...last, content: last.content + text };
      return copy;
    });
  }, []);

  /** Load a session's saved messages. */
  const loadHistory = useCallback(async (sessionId) => {
    abortRef.current?.abort();
    setError("");
    setIsStreaming(false);
    try {
      const { data } = await api.get(`/chat/history/${sessionId}`);
      setMessages(data.messages.map((m) => ({ role: m.role, content: m.content })));
    } catch {
      setMessages([]);
      setError("Could not load this conversation");
    }
  }, []);

  /** Reset to an empty conversation. */
  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setError("");
    setIsStreaming(false);
  }, []);

  /**
   * Send a question. Resolves with the session id (from the X-Session-Id header).
   * onSession(id) fires as soon as headers arrive so the caller can update the URL.
   */
  const sendMessage = useCallback(
    async (query, sessionId, onSession) => {
      setError("");
      setMessages((prev) => [...prev, { role: "user", content: query }, { role: "ai", content: "" }]);
      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await fetch(`${API_URL}/chat`, {
          method: "POST",
          signal: controller.signal,
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ query, session_id: sessionId || null }),
        });

        if (response.status === 401) {
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          window.location.assign("/login");
          return null;
        }
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(typeof body.detail === "string" ? body.detail : "Request failed");
        }

        const newSessionId = response.headers.get("X-Session-Id");
        if (newSessionId) onSession?.(newSessionId);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let done = false;

        while (!done) {
          const { value, done: streamDone } = await reader.read();
          if (streamDone) break;
          buffer += decoder.decode(value, { stream: true });

          let sep;
          while ((sep = buffer.indexOf("\n\n")) !== -1) {
            const block = buffer.slice(0, sep);
            buffer = buffer.slice(sep + 2);
            const text = parseEvent(block);
            if (text === null) continue;
            if (text === "[DONE]") {
              done = true;
              break;
            }
            if (text.startsWith("[ERROR]")) {
              setError(text.slice(7).trim() || "Failed to generate an answer");
              done = true;
              break;
            }
            appendToLast(text);
          }
        }
        return newSessionId;
      } catch (err) {
        if (err.name !== "AbortError") setError(err.message || "Something went wrong");
        return null;
      } finally {
        setIsStreaming(false);
      }
    },
    [appendToLast]
  );

  return { messages, isStreaming, error, sendMessage, loadHistory, reset };
}
