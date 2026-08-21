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

  const [tab, setTab] = useState("pendentes");
  const [pendingIdeaId, setPendingIdeaId] = useState(null);
  const [actionIdeaId, setActionIdeaId] = useState(null);
  const [actionType, setActionType] = useState(null); // "aprovar" | "rejeitar"
  const [actionProjectId, setActionProjectId] = useState("");
  const [actionReason, setActionReason] = useState("");
  const [actionError, setActionError] = useState("");

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

  function openAction(idea, type) {
    setActionIdeaId(idea.id);
    setActionType(type);
    setActionProjectId(idea.project ? String(idea.project.id) : "");
    setActionReason("");
    setActionError("");
  }

  function cancelAction() {
    setActionIdeaId(null);
    setActionType(null);
    setActionError("");
  }

  async function confirmAction(idea) {
    setActionError("");
    const payload = { status: actionType === "aprovar" ? "aprovada" : "rejeitada" };
    if (actionType === "aprovar" && !idea.project) {
      if (!actionProjectId) {
        setActionError("Selecione um projeto.");
        return;
      }
      payload.project_id = Number(actionProjectId);
    }
    if (actionType === "rejeitar") {
      if (!actionReason.trim()) {
        setActionError("Informe o motivo da rejeição.");
        return;
      }
      payload.rejection_reason = actionReason.trim();
    }

    setPendingIdeaId(idea.id);
    try {
      await updateProjectIdeaStatus(idea.id, payload);
      queryClient.invalidateQueries({ queryKey: ["project-ideas"] });
      cancelAction();
    } catch (err) {
      setActionError(err.message || "Não foi possível atualizar o status da ideia.");
    } finally {
      setPendingIdeaId(null);
    }
  }

  const pendentes = ideas?.filter((idea) => idea.status === "pendente") ?? [];
  const historico = ideas?.filter((idea) => idea.status !== "pendente") ?? [];
  const visibleIdeas = tab === "pendentes" ? pendentes : historico;

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

      <div className="tabs">
        <button
          type="button"
          className={`tab-button ${tab === "pendentes" ? "active" : ""}`}
          onClick={() => setTab("pendentes")}
        >
          Pendentes
        </button>
        <button
          type="button"
          className={`tab-button ${tab === "historico" ? "active" : ""}`}
          onClick={() => setTab("historico")}
        >
          Histórico
        </button>
      </div>

      {isLoading && <p>Carregando ideias...</p>}
      {isError && <p className="error">Não foi possível carregar as ideias.</p>}
      {ideas && visibleIdeas.length === 0 && <p>Nenhuma ideia encontrada.</p>}

      {ideas && visibleIdeas.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Descrição</th>
              {isAdmin && <th>Autor</th>}
              <th>Status</th>
              {tab === "historico" && <th>Detalhes</th>}
              {isAdmin && tab === "pendentes" && <th>Ações</th>}
            </tr>
          </thead>
          <tbody>
            {visibleIdeas.map((idea) => (
              <tr key={idea.id}>
                <td>{idea.title}</td>
                <td>{idea.description}</td>
                {isAdmin && <td>{idea.author ? idea.author.name : "—"}</td>}
                <td>
                  <span className={`badge badge-idea-${idea.status}`}>{STATUS_LABELS[idea.status]}</span>
                </td>
                {tab === "historico" && (
                  <td>
                    {idea.status === "aprovada" && idea.project && <span>Projeto: {idea.project.name}</span>}
                    {idea.status === "rejeitada" && idea.rejection_reason && <span>{idea.rejection_reason}</span>}
                  </td>
                )}
                {isAdmin && tab === "pendentes" && (
                  <td>
                    {actionIdeaId !== idea.id && (
                      <>
                        <button type="button" onClick={() => openAction(idea, "aprovar")} disabled={pendingIdeaId === idea.id}>
                          Aprovar
                        </button>{" "}
                        <button type="button" onClick={() => openAction(idea, "rejeitar")} disabled={pendingIdeaId === idea.id}>
                          Rejeitar
                        </button>
                      </>
                    )}
                    {actionIdeaId === idea.id && actionType === "aprovar" && (
                      <div className="form">
                        {!idea.project && (
                          <select value={actionProjectId} onChange={(e) => setActionProjectId(e.target.value)}>
                            <option value="" disabled>
                              Selecione um projeto
                            </option>
                            {projects?.map((project) => (
                              <option key={project.id} value={project.id}>
                                {project.name}
                              </option>
                            ))}
                          </select>
                        )}
                        {actionError && <p className="error">{actionError}</p>}
                        <button type="button" onClick={() => confirmAction(idea)} disabled={pendingIdeaId === idea.id}>
                          Confirmar aprovação
                        </button>{" "}
                        <button type="button" onClick={cancelAction}>
                          Cancelar
                        </button>
                      </div>
                    )}
                    {actionIdeaId === idea.id && actionType === "rejeitar" && (
                      <div className="form">
                        <textarea
                          value={actionReason}
                          onChange={(e) => setActionReason(e.target.value)}
                          rows={2}
                          placeholder="Motivo da rejeição"
                        />
                        {actionError && <p className="error">{actionError}</p>}
                        <button type="button" onClick={() => confirmAction(idea)} disabled={pendingIdeaId === idea.id}>
                          Confirmar rejeição
                        </button>{" "}
                        <button type="button" onClick={cancelAction}>
                          Cancelar
                        </button>
                      </div>
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
