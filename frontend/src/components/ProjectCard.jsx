import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { addProjectUpdate, deleteProject, fetchProjectUpdates, updateProject } from "../services/projects.js";
import { fetchTickets } from "../services/tickets.js";
import { STATUS_LABELS as PROJECT_STATUS_LABELS, STATUS_OPTIONS as PROJECT_STATUS_OPTIONS } from "../utils/projectStatus.js";
import { PRIORITY_LABELS, STATUS_LABELS as TICKET_STATUS_LABELS, TYPE_LABELS } from "../utils/ticketLabels.js";

export default function ProjectCard({ project, tickets }) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const [name, setName] = useState(project.name);
  const [nameError, setNameError] = useState("");
  const [savingName, setSavingName] = useState(false);

  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);

  const [message, setMessage] = useState("");
  const [updateError, setUpdateError] = useState("");
  const [submittingUpdate, setSubmittingUpdate] = useState(false);

  const [githubRepo, setGithubRepo] = useState(project.github_repo || "");
  const [repoError, setRepoError] = useState("");
  const [savingRepo, setSavingRepo] = useState(false);
  const [githubToken, setGithubToken] = useState("");
  const [tokenError, setTokenError] = useState("");
  const [savingToken, setSavingToken] = useState(false);
  const [clearingToken, setClearingToken] = useState(false);

  const { data: updates } = useQuery({
    queryKey: ["project-updates", project.id],
    queryFn: () => fetchProjectUpdates(project.id),
    enabled: expanded,
  });

  const { data: historyTickets } = useQuery({
    queryKey: ["tickets", "history", project.id],
    queryFn: () => fetchTickets({ projectId: project.id, finalized: true }),
    enabled: expanded && showHistory,
  });

  function invalidateProjects() {
    queryClient.invalidateQueries({ queryKey: ["projects"] });
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
  }

  async function handleSaveName(event) {
    event.preventDefault();
    setNameError("");
    setSavingName(true);
    try {
      await updateProject(project.id, { name });
      invalidateProjects();
    } catch (err) {
      setNameError(err.message || "Não foi possível renomear o projeto.");
    } finally {
      setSavingName(false);
    }
  }

  async function handleStatusChange(event) {
    await updateProject(project.id, { status: event.target.value });
    invalidateProjects();
  }

  async function handleDeleteProject() {
    if (!window.confirm(`Excluir o projeto "${project.name}"? Essa ação não pode ser desfeita.`)) {
      return;
    }
    setDeleteError("");
    setDeleting(true);
    try {
      await deleteProject(project.id);
      invalidateProjects();
    } catch (err) {
      setDeleteError(err.message || "Não foi possível excluir o projeto.");
      setDeleting(false);
    }
  }

  async function handleAddUpdate(event) {
    event.preventDefault();
    setUpdateError("");
    setSubmittingUpdate(true);
    try {
      await addProjectUpdate(project.id, message);
      setMessage("");
      queryClient.invalidateQueries({ queryKey: ["project-updates", project.id] });
    } catch (err) {
      setUpdateError(err.message || "Não foi possível registrar o andamento.");
    } finally {
      setSubmittingUpdate(false);
    }
  }

  async function handleSaveRepo(event) {
    event.preventDefault();
    setRepoError("");
    setSavingRepo(true);
    try {
      await updateProject(project.id, { github_repo: githubRepo || null });
      invalidateProjects();
    } catch (err) {
      setRepoError(err.message || "Não foi possível salvar o repositório.");
    } finally {
      setSavingRepo(false);
    }
  }

  async function handleSaveToken(event) {
    event.preventDefault();
    if (!githubToken) return;
    setTokenError("");
    setSavingToken(true);
    try {
      await updateProject(project.id, { github_token: githubToken });
      setGithubToken("");
      invalidateProjects();
    } catch (err) {
      setTokenError(err.message || "Não foi possível salvar o token.");
    } finally {
      setSavingToken(false);
    }
  }

  async function handleClearToken() {
    setTokenError("");
    setClearingToken(true);
    try {
      await updateProject(project.id, { clear_github_token: true });
      invalidateProjects();
    } catch (err) {
      setTokenError(err.message || "Não foi possível remover o token.");
    } finally {
      setClearingToken(false);
    }
  }

  const visibleTickets = showHistory ? historyTickets : tickets;

  return (
    <div className="project-card">
      <button type="button" className="project-card-header" onClick={() => setExpanded((v) => !v)}>
        <span className="project-card-title">
          <span className={`project-card-chevron ${expanded ? "expanded" : ""}`}>▶</span>
          {project.name}
          <span className={`badge badge-${project.status}`}>{PROJECT_STATUS_LABELS[project.status]}</span>
        </span>
        <span className="project-card-count">{tickets.length} solicitações</span>
      </button>

      {expanded && (
        <div className="project-card-body">
          <div className="project-card-section">
            <div className="page-header">
              <form className="project-name-form" onSubmit={handleSaveName}>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  aria-label="Nome do projeto"
                  required
                />
                <button type="submit" disabled={savingName || name === project.name}>
                  {savingName ? "Salvando..." : "Salvar nome"}
                </button>
              </form>
              <select value={project.status} onChange={handleStatusChange}>
                {PROJECT_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            {nameError && <p className="error">{nameError}</p>}
            <p>{project.description || "Sem descrição."}</p>
            <div className="page-actions">
              <button type="button" onClick={handleDeleteProject} disabled={deleting} className="danger-button">
                {deleting ? "Excluindo..." : "Excluir projeto"}
              </button>
            </div>
            {deleteError && <p className="error">{deleteError}</p>}
          </div>

          <div className="project-card-section">
            <h3>Andamento</h3>
            <form className="form" onSubmit={handleAddUpdate}>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Descreva o andamento..."
                rows={3}
                required
              />
              {updateError && <p className="error">{updateError}</p>}
              <button type="submit" disabled={submittingUpdate}>
                {submittingUpdate ? "Enviando..." : "Registrar andamento"}
              </button>
            </form>
            <ul className="update-list">
              {updates?.length === 0 && <p>Nenhuma atualização registrada ainda.</p>}
              {updates?.map((update) => (
                <li key={update.id}>
                  <p>{update.message}</p>
                  <span className="meta">{new Date(update.created_at).toLocaleString("pt-BR")}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="project-card-section">
            <h3>GitHub</h3>
            <form className="form github-repo-form" onSubmit={handleSaveRepo}>
              <label htmlFor={`github_repo_${project.id}`}>Repositório (owner/repo)</label>
              <input
                id={`github_repo_${project.id}`}
                value={githubRepo}
                onChange={(e) => setGithubRepo(e.target.value)}
                placeholder="owner/repo"
              />
              {repoError && <p className="error">{repoError}</p>}
              <button type="submit" disabled={savingRepo}>
                {savingRepo ? "Salvando..." : "Salvar repositório"}
              </button>
            </form>

            <form className="form github-token-form" onSubmit={handleSaveToken}>
              <label htmlFor={`github_token_${project.id}`}>
                Token de acesso específico deste repositório —{" "}
                {project.has_github_token ? "configurado" : "não configurado (usando o token padrão do sistema)"}
              </label>
              <input
                id={`github_token_${project.id}`}
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="Deixe em branco para não alterar"
                autoComplete="off"
              />
              {tokenError && <p className="error">{tokenError}</p>}
              <div className="page-actions">
                <button type="submit" disabled={savingToken || !githubToken}>
                  {savingToken ? "Salvando..." : "Salvar token"}
                </button>
                {project.has_github_token && (
                  <button type="button" onClick={handleClearToken} disabled={clearingToken}>
                    {clearingToken ? "Removendo..." : "Remover token específico"}
                  </button>
                )}
              </div>
            </form>

            {!project.github_repo && <p className="meta">Nenhum repositório configurado.</p>}
          </div>

          <div className="project-card-section">
            <div className="page-header">
              <h3>Solicitações</h3>
              <div className="page-actions">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={showHistory}
                    onChange={(e) => setShowHistory(e.target.checked)}
                  />
                  Ver histórico
                </label>
                <Link className="button-link" to={`/tickets/new?project_id=${project.id}`}>
                  + Nova solicitação
                </Link>
              </div>
            </div>

            {visibleTickets && visibleTickets.length === 0 && <p className="meta">Nenhuma solicitação encontrada.</p>}
            {visibleTickets && visibleTickets.length > 0 && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Título</th>
                    <th>Tipo</th>
                    <th>Prioridade</th>
                    <th>Status</th>
                    <th>Quem pediu</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleTickets.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>
                        <Link to={`/tickets/${ticket.id}`}>{ticket.title}</Link>
                      </td>
                      <td>{TYPE_LABELS[ticket.type]}</td>
                      <td>
                        <span className={`badge badge-priority-${ticket.priority}`}>
                          {PRIORITY_LABELS[ticket.priority]}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-status-${ticket.status}`}>
                          {TICKET_STATUS_LABELS[ticket.status]}
                        </span>
                      </td>
                      <td>{ticket.requester_name || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
