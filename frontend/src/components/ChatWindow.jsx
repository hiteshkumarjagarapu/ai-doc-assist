import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

/** Scrollable message list that auto-scrolls to the bottom as messages stream in. */
export default function ChatWindow({ messages, isStreaming }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (!messages.length)
    return (
      <div className="flex flex-1 items-center justify-center px-4 text-center text-gray-500 dark:text-gray-400">
        Ask a question about your documents to get started.
      </div>
    );

  return (
    <div className="flex-1 space-y-4 overflow-y-auto px-4 py-6">
      {messages.map((m, i) => (
        <MessageBubble
          key={i}
          role={m.role}
          content={m.content}
          streaming={isStreaming && i === messages.length - 1 && m.role === "ai"}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
