import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchProjects } from "../services/projects.js";
import { createProjectIdea, fetchProjectIdeas, updateProjectIdeaStatus } from "../services/projectIdeas.js";

const STATUS_LABELS = {
  pendente: "Pendente",
  aprovada: "Aprovada",
  rejeitada: "Rejeitada",
};

export default function ProjectIdeasPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [pendingIdeaId, setPendingIdeaId] = useState(null);

  const { data: ideas, isLoading, isError } = useQuery({
    queryKey: ["project-ideas"],
    queryFn: fetchProjectIdeas,
  });

  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: () => fetchProjects() });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createProjectIdea({ title, description, project_id: Number(projectId) });
      setTitle("");
      setDescription("");
      setProjectId("");
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
    } catch (err) {
      setError(err.message || "Não foi possível enviar a ideia.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatusChange(ideaId, nextStatus) {
    setError("");
    setPendingIdeaId(ideaId);
    try {
      await updateProjectIdeaStatus(ideaId, nextStatus);
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
    } catch (err) {
      setError(err.message || "Não foi possível atualizar o status da ideia.");
    } finally {
      setPendingIdeaId(null);
    }
  }

  return (
    <main className="page">
      <h1>Ideias de projeto</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label htmlFor="idea_title">Título</label>
        <input id="idea_title" value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus />

        <label htmlFor="idea_project">Projeto</label>
        <select id="idea_project" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
          <option value="" disabled>
            Selecione um projeto
          </option>
          {projects?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>

        <label htmlFor="idea_description">Descrição</label>
        <textarea
          id="idea_description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting || !projectId}>
          {submitting ? "Enviando..." : "Enviar ideia"}
        </button>
      </form>

      <div className="page-header">
        <h2>{isAdmin ? "Todas as ideias" : "Minhas ideias"}</h2>
      </div>

      {isLoading && <p>Carregando ideias...</p>}
      {isError && <p className="error">Não foi possível carregar as ideias.</p>}
      {ideas && ideas.length === 0 && <p>Nenhuma ideia enviada ainda.</p>}

      {ideas && ideas.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Descrição</th>
              {isAdmin && <th>Autor</th>}
              <th>Status</th>
              {isAdmin && <th>Ações</th>}
            </tr>
          </thead>
          <tbody>
            {ideas.map((idea) => (
              <tr key={idea.id}>
                <td>{idea.title}</td>
                <td>{idea.description}</td>
                {isAdmin && <td>{idea.author ? idea.author.name : "—"}</td>}
                <td>
                  <span className={`badge badge-idea-${idea.status}`}>{STATUS_LABELS[idea.status]}</span>
                </td>
                {isAdmin && (
                  <td>
                    {idea.status === "pendente" && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleStatusChange(idea.id, "aprovada")}
                          disabled={pendingIdeaId === idea.id}
                        >
                          Aprovar
                        </button>{" "}
                        <button
                          type="button"
                          onClick={() => handleStatusChange(idea.id, "rejeitada")}
                          disabled={pendingIdeaId === idea.id}
                        >
                          Rejeitar
                        </button>
                      </>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
