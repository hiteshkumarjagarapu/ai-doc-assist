/** Renders text preserving line breaks, with a blinking cursor while streaming. */
export default function StreamingText({ text, streaming }) {
  return (
    <span className="whitespace-pre-wrap break-words">
      {text}
      {streaming && (
        <span aria-hidden="true" className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-current align-middle" />
      )}
    </span>
  );
}
