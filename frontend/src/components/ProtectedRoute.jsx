import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

/** Redirects to /login when the user is not authenticated. */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}
