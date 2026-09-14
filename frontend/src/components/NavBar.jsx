import { Link } from "react-router-dom";

import Logo from "./Logo.jsx";

export default function NavBar() {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <Logo size="md" variant="wide" />
      </Link>
    </nav>
  );
}
