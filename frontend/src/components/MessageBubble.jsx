import ReactMarkdown from "react-markdown";
import StreamingText from "./StreamingText";

// Element styles for markdown (no typography plugin needed). Raw HTML is not rendered.
const components = {
  p: (props) => <p className="my-2 first:mt-0 last:mb-0" {...props} />,
  ul: (props) => <ul className="my-2 list-disc pl-5" {...props} />,
  ol: (props) => <ol className="my-2 list-decimal pl-5" {...props} />,
  li: (props) => <li className="my-0.5" {...props} />,
  strong: (props) => <strong className="font-semibold" {...props} />,
  a: (props) => (
    <a className="text-indigo-600 underline dark:text-indigo-400" target="_blank" rel="noopener noreferrer" {...props} />
  ),
  h1: (props) => <h3 className="my-2 text-base font-bold" {...props} />,
  h2: (props) => <h3 className="my-2 text-base font-bold" {...props} />,
  h3: (props) => <h3 className="my-2 font-semibold" {...props} />,
  code: (props) => (
    <code className="rounded bg-gray-100 px-1 py-0.5 font-mono text-xs dark:bg-gray-700" {...props} />
  ),
  pre: (props) => (
    <pre className="my-2 overflow-x-auto rounded-lg bg-gray-100 p-3 text-xs dark:bg-gray-900" {...props} />
  ),
  blockquote: (props) => (
    <blockquote className="my-2 border-l-4 border-gray-300 pl-3 dark:border-gray-600" {...props} />
  ),
};

/** A single user or AI message. AI messages are rendered as markdown. */
export default function MessageBubble({ role, content, streaming }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed sm:max-w-[75%] ${
          isUser
            ? "bg-indigo-600 text-white"
            : "bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-gray-100"
        }`}
      >
        {isUser || !content ? (
          <StreamingText text={content} streaming={streaming} />
        ) : (
          <div
            className={`break-words ${
              streaming ? "[&>*:last-child]:after:ml-0.5 [&>*:last-child]:after:animate-pulse [&>*:last-child]:after:content-['▍']" : ""
            }`}
          >
            <ReactMarkdown components={components}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
