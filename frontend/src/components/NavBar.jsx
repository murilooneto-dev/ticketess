import { Link } from "react-router-dom";

import Logo from "./Logo.jsx";

export default function NavBar() {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <Logo size="md" variant="wide" />
      </Link>
      <div className="navbar-links">
        <Link to="/projects">Projetos</Link>
        <Link to="/tickets">Solicitações</Link>
        <Link to="/project-ideas">Ideias</Link>
        <Link to="/reports">Relatórios</Link>
      </div>
    </nav>
  );
}
