import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchProjects } from "../services/projects.js";
import { STATUS_LABELS } from "../utils/projectStatus.js";

export default function ProjectsPage() {
  const { user } = useAuth();
  const [onlyMine, setOnlyMine] = useState(false);

  const { data: projects, isLoading, isError } = useQuery({
    queryKey: ["projects", onlyMine],
    queryFn: () => fetchProjects(onlyMine),
  });

  return (
    <main className="page">
      <div className="page-header">
        <h1>Projetos</h1>
        <div className="page-actions">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={onlyMine}
              onChange={(e) => setOnlyMine(e.target.checked)}
            />
            Ver apenas meus projetos
          </label>
          {user?.role === "admin" && (
            <Link className="button-link" to="/projects/new">
              Novo projeto
            </Link>
          )}
        </div>
      </div>

      {isLoading && <p>Carregando projetos...</p>}
      {isError && <p className="error">Não foi possível carregar os projetos.</p>}

      {projects && projects.length === 0 && <p>Nenhum projeto encontrado.</p>}

      {projects && projects.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Status</th>
              <th>Gestor responsável</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr key={project.id}>
                <td>
                  <Link to={`/projects/${project.id}`}>{project.name}</Link>
                </td>
                <td>
                  <span className={`badge badge-${project.status}`}>{STATUS_LABELS[project.status]}</span>
                </td>
                <td>{project.manager ? project.manager.name : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
