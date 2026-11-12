/** Lists uploaded documents with a delete button. */
export default function DocumentList({ documents, loading, deletingId, onDelete }) {
  if (loading) return <p className="text-sm text-gray-500">Loading documents...</p>;
  if (!documents.length)
    return <p className="text-sm text-gray-500 dark:text-gray-400">No documents yet. Upload one to get started.</p>;

  return (
    <ul className="divide-y divide-gray-200 overflow-hidden rounded-xl bg-white shadow-sm dark:divide-gray-700 dark:bg-gray-800">
      {documents.map((doc) => (
        <li key={doc.id} className="flex items-center justify-between gap-3 px-4 py-3">
          <div className="min-w-0">
            <p className="truncate font-medium">{doc.filename}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {doc.chunk_count} chunks · {new Date(doc.created_at + "Z").toLocaleString()}
            </p>
          </div>
          <button
            onClick={() => onDelete(doc)}
            disabled={deletingId === doc.id}
            className="shrink-0 rounded-lg px-3 py-1 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-900/20"
          >
            {deletingId === doc.id ? "Deleting..." : "Delete"}
          </button>
        </li>
      ))}
    </ul>
  );
}
