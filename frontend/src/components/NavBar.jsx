import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import Logo from "./Logo.jsx";
import NotificationBell from "./NotificationBell.jsx";

const ROLE_LABELS = {
  admin: "Administrador",
  gestor: "Gestor",
  operador: "Operador",
};

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <Logo size="md" variant="wide" />
      </Link>
      <div className="navbar-links">
        {user.role !== "operador" && <Link to="/projects">Projetos</Link>}
        <Link to="/tickets">Solicitações</Link>
        {user.role !== "operador" && <Link to="/project-ideas">Ideias</Link>}
        {user.role !== "operador" && <Link to="/reports">Relatórios</Link>}
        {user.role === "admin" && <Link to="/users">Usuários</Link>}
        <NotificationBell />
        <span className="navbar-user">
          {user.name} ({ROLE_LABELS[user.role] || user.role})
        </span>
        <button type="button" onClick={handleLogout}>
          Sair
        </button>
      </div>
    </nav>
  );
}
