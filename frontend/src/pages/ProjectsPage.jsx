import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchProjects } from "../services/projects.js";
import { STATUS_LABELS } from "../utils/projectStatus.js";

export default function ProjectsPage() {
  const { data: projects, isLoading, isError } = useQuery({
    queryKey: ["projects"],
    queryFn: () => fetchProjects(),
  });

  return (
    <main className="page">
      <div className="page-header">
        <h1>Projetos</h1>
        <div className="page-actions">
          <Link className="button-link" to="/projects/new">
            Novo projeto
          </Link>
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
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
