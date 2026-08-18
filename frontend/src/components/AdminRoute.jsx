import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <p className="loading-screen">Carregando...</p>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "admin") {
    return <Navigate to="/projects" replace />;
  }

  return children;
}
