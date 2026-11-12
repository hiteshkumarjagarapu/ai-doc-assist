import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { getErrorMessage } from "../api/api";
import DocumentList from "../components/DocumentList";
import FileUpload from "../components/FileUpload";
import { useAuth } from "../hooks/useAuth";

/** Document upload + list, with a shortcut to start a new chat. */
export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");

  const loadDocuments = useCallback(async () => {
    try {
      const { data } = await api.get("/docs/list");
      setDocuments(data);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load documents"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.filename}"?`)) return;
    setDeletingId(doc.id);
    setError("");
    try {
      await api.delete(`/docs/${doc.id}`);
      setDocuments((docs) => docs.filter((d) => d.id !== doc.id));
    } catch (err) {
      setError(getErrorMessage(err, "Failed to delete document"));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Your documents</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Signed in as {user?.name}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate("/chat")}
            disabled={!documents.length}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            New Chat
          </button>
          <button
            onClick={logout}
            className="rounded-lg bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
          >
            Log out
          </button>
        </div>
      </header>

      <FileUpload onUploaded={loadDocuments} />

      {error && (
        <div role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          {error}
        </div>
      )}

      <section className="mt-8">
        <DocumentList documents={documents} loading={loading} deletingId={deletingId} onDelete={handleDelete} />
      </section>
    </div>
  );
}
