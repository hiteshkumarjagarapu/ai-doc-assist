import { useRef, useState } from "react";
import api, { getErrorMessage } from "../api/api";

const ALLOWED = [".pdf", ".docx", ".pptx"];
const MAX_MB = 10;

/** Drag & drop (or click) upload area. Calls onUploaded() after each successful upload. */
export default function FileUpload({ onUploaded }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const validate = (file) => {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED.includes(ext)) return `${file.name}: only PDF, DOCX and PPTX files are allowed`;
    if (file.size > MAX_MB * 1024 * 1024) return `${file.name}: exceeds ${MAX_MB}MB limit`;
    return null;
  };

  const uploadFiles = async (fileList) => {
    const files = Array.from(fileList);
    if (!files.length) return;
    setError("");
    setUploading(true);
    const errors = [];
    for (const file of files) {
      const problem = validate(file);
      if (problem) {
        errors.push(problem);
        continue;
      }
      const formData = new FormData();
      formData.append("file", file);
      try {
        await api.post("/docs/upload", formData);
        onUploaded?.();
      } catch (err) {
        errors.push(`${file.name}: ${getErrorMessage(err, "Upload failed")}`);
      }
    }
    setError(errors.join(" | "));
    setUploading(false);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !uploading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !uploading && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!uploading) uploadFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
          dragging
            ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20"
            : "border-gray-300 hover:border-indigo-400 dark:border-gray-600"
        } ${uploading ? "opacity-60" : ""}`}
      >
        <p className="font-medium">
          {uploading ? "Uploading and indexing..." : "Drag & drop documents here, or click to browse"}
        </p>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">PDF, DOCX or PPTX, up to {MAX_MB}MB</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ALLOWED.join(",")}
          className="hidden"
          onChange={(e) => uploadFiles(e.target.files)}
        />
      </div>
      {error && (
        <div role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
