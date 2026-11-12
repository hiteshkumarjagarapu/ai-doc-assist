import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/api";
import ChatWindow from "../components/ChatWindow";
import Sidebar from "../components/Sidebar";
import { useStreamChat } from "../hooks/useStreamChat";
import { useTheme } from "../hooks/useTheme";

/** Chat interface: sidebar of sessions + messages + input, with streaming answers. */
export default function Chat() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { dark, toggle } = useTheme();
  const { messages, isStreaming, error, sendMessage, loadHistory, reset } = useStreamChat();
  const [sessions, setSessions] = useState([]);
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // Session id we just created while streaming; don't reload history for it (would wipe the stream).
  const ownSessionRef = useRef(null);

  const refreshSessions = useCallback(async () => {
    try {
      const { data } = await api.get("/chat/sessions");
      setSessions(data);
    } catch {
      /* sidebar is non-critical */
    }
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    if (!sessionId) {
      ownSessionRef.current = null;
      reset();
    } else if (ownSessionRef.current === sessionId) {
      ownSessionRef.current = null;
    } else {
      loadHistory(sessionId);
    }
  }, [sessionId, loadHistory, reset]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || isStreaming) return;
    setInput("");
    await sendMessage(query, sessionId, (newId) => {
      if (newId !== sessionId) {
        ownSessionRef.current = newId;
        navigate(`/chat/${newId}`, { replace: true });
      }
    });
    refreshSessions();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) handleSubmit(e);
  };

  return (
    <div className="flex h-screen">
      <Sidebar sessions={sessions} activeId={sessionId} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
            className="rounded-lg px-2 py-1 hover:bg-gray-200 dark:hover:bg-gray-700 md:hidden"
          >
            ☰
          </button>
          <h1 className="font-semibold">AI Document Assistant</h1>
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="rounded-lg px-2 py-1 hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            {dark ? "☀️" : "🌙"}
          </button>
        </header>

        <ChatWindow messages={messages} isStreaming={isStreaming} />

        {error && (
          <div role="alert" className="mx-4 mb-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-200 p-3 dark:border-gray-700">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your documents..."
            maxLength={2000}
            className="max-h-32 flex-1 resize-none rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 dark:border-gray-600 dark:bg-gray-800"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
