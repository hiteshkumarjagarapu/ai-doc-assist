import { Link, useNavigate } from "react-router-dom";

/** Chat history list with New Chat and a link back to the dashboard. */
export default function Sidebar({ sessions, activeId, open, onClose }) {
  const navigate = useNavigate();
  return (
    <>
      {open && <div className="fixed inset-0 z-10 bg-black/40 md:hidden" onClick={onClose} />}
      <aside
        className={`fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-gray-200 bg-white transition-transform dark:border-gray-700 dark:bg-gray-800 md:static md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-3">
          <button
            onClick={() => {
              navigate("/chat");
              onClose();
            }}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            + New chat
          </button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-2">
          {sessions.length === 0 && <p className="px-2 text-sm text-gray-500">No conversations yet</p>}
          {sessions.map((s) => (
            <Link
              key={s.id}
              to={`/chat/${s.id}`}
              onClick={onClose}
              className={`block truncate rounded-lg px-3 py-2 text-sm ${
                s.id === activeId
                  ? "bg-indigo-50 font-medium text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300"
                  : "hover:bg-gray-100 dark:hover:bg-gray-700"
              }`}
            >
              {s.title}
            </Link>
          ))}
        </nav>
        <div className="border-t border-gray-200 p-3 dark:border-gray-700">
          <Link to="/dashboard" className="text-sm text-indigo-600 hover:underline dark:text-indigo-400">
            ← Documents
          </Link>
        </div>
      </aside>
    </>
  );
}
