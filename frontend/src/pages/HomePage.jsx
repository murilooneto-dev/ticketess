import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import NewProjectForm from "../components/NewProjectForm.jsx";
import ProjectCard from "../components/ProjectCard.jsx";
import { fetchProjects } from "../services/projects.js";
import { fetchTickets } from "../services/tickets.js";
import { PRIORITY_LABELS, STATUS_LABELS as TICKET_STATUS_LABELS } from "../utils/ticketLabels.js";

export default function HomePage() {
  const [showNewProject, setShowNewProject] = useState(false);
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");

  const { data: projects, isLoading: loadingProjects, isError: projectsError } = useQuery({
    queryKey: ["projects"],
    queryFn: () => fetchProjects(),
  });

  const { data: tickets, isLoading: loadingTickets, isError: ticketsError } = useQuery({
    queryKey: ["tickets", status, priority],
    queryFn: () => fetchTickets({ status: status || undefined, priority: priority || undefined }),
  });

  const ticketsByProject = useMemo(() => {
    const map = {};
    for (const ticket of tickets || []) {
      if (!map[ticket.project_id]) map[ticket.project_id] = [];
      map[ticket.project_id].push(ticket);
    }
    return map;
  }, [tickets]);

  return (
    <main className="page">
      <div className="page-header">
        <h1>Projetos</h1>
        <div className="page-actions">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos os status</option>
            {Object.entries(TICKET_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="">Todas as prioridades</option>
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => setShowNewProject((v) => !v)}>
            {showNewProject ? "Cancelar" : "Novo projeto"}
          </button>
          <Link className="button-link" to="/tickets/new">
            Nova solicitação
          </Link>
          <Link className="button-link" to="/reports">
            Relatório
          </Link>
        </div>
      </div>

      {showNewProject && <NewProjectForm onDone={() => setShowNewProject(false)} />}

      {(loadingProjects || loadingTickets) && <p>Carregando...</p>}
      {(projectsError || ticketsError) && <p className="error">Não foi possível carregar os dados.</p>}
      {projects && projects.length === 0 && <p>Nenhum projeto encontrado.</p>}

      <div className="project-list">
        {projects?.map((project) => (
          <ProjectCard key={project.id} project={project} tickets={ticketsByProject[project.id] || []} />
        ))}
      </div>
    </main>
  );
}
