import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { getErrorMessage } from "../api/api";
import { useAuth } from "../hooks/useAuth";

const inputClass =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-gray-600 dark:bg-gray-700 dark:focus:ring-indigo-900";

/** Login / Register form with a toggle between the two modes. */
export default function Login() {
  const { isAuthenticated, login, register } = useAuth();
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isRegister) await register(form.name, form.email, form.password);
      else await login(form.email, form.password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, isRegister ? "Registration failed" : "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-8 shadow-lg dark:bg-gray-800"
      >
        <div className="text-center">
          <h1 className="text-2xl font-bold">AI Document Assistant</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {isRegister ? "Create your account" : "Sign in to continue"}
          </p>
        </div>

        {error && (
          <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
            {error}
          </div>
        )}

        {isRegister && (
          <input className={inputClass} placeholder="Name" value={form.name} onChange={update("name")} required />
        )}
        <input
          className={inputClass}
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={update("email")}
          required
        />
        <input
          className={inputClass}
          type="password"
          placeholder="Password"
          minLength={isRegister ? 8 : undefined}
          value={form.password}
          onChange={update("password")}
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-60"
        >
          {loading ? "Please wait..." : isRegister ? "Create account" : "Sign in"}
        </button>

        <p className="text-center text-sm text-gray-500 dark:text-gray-400">
          {isRegister ? "Already have an account?" : "No account yet?"}{" "}
          <button
            type="button"
            className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            onClick={() => {
              setIsRegister(!isRegister);
              setError("");
            }}
          >
            {isRegister ? "Sign in" : "Register"}
          </button>
        </p>
      </form>
    </div>
  );
}
