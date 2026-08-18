import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchProjectCommits, fetchProjectPullRequests, syncProjectGithub } from "../services/github.js";
import {
  addProjectUpdate,
  deleteProject,
  fetchProject,
  fetchProjectUpdates,
  updateProject,
} from "../services/projects.js";
import { STATUS_LABELS, STATUS_OPTIONS } from "../utils/projectStatus.js";

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [nameError, setNameError] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);

  const [githubRepo, setGithubRepo] = useState("");
  const [repoError, setRepoError] = useState("");
  const [savingRepo, setSavingRepo] = useState(false);
  const [syncError, setSyncError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  const [githubToken, setGithubToken] = useState("");
  const [tokenError, setTokenError] = useState("");
  const [savingToken, setSavingToken] = useState(false);
  const [clearingToken, setClearingToken] = useState(false);

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
  });

  useEffect(() => {
    if (project) {
      setGithubRepo(project.github_repo || "");
      setName(project.name);
    }
  }, [project]);

  const { data: updates } = useQuery({
    queryKey: ["project-updates", projectId],
    queryFn: () => fetchProjectUpdates(projectId),
  });

  const { data: commits } = useQuery({
    queryKey: ["project-commits", projectId],
    queryFn: () => fetchProjectCommits(projectId),
    enabled: Boolean(project?.github_repo),
  });

  const { data: pullRequests } = useQuery({
    queryKey: ["project-pull-requests", projectId],
    queryFn: () => fetchProjectPullRequests(projectId),
    enabled: Boolean(project?.github_repo),
  });

  async function handleAddUpdate(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await addProjectUpdate(projectId, message);
      setMessage("");
      queryClient.invalidateQueries({ queryKey: ["project-updates", projectId] });
    } catch (err) {
      setError(err.message || "Não foi possível registrar o andamento.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSaveName(event) {
    event.preventDefault();
    setNameError("");
    setSavingName(true);
    try {
      await updateProject(projectId, { name });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    } catch (err) {
      setNameError(err.message || "Não foi possível renomear o projeto.");
    } finally {
      setSavingName(false);
    }
  }

  async function handleDeleteProject() {
    if (!window.confirm(`Excluir o projeto "${project.name}"? Essa ação não pode ser desfeita.`)) {
      return;
    }
    setDeleteError("");
    setDeleting(true);
    try {
      await deleteProject(projectId);
      navigate("/projects", { replace: true });
    } catch (err) {
      setDeleteError(err.message || "Não foi possível excluir o projeto.");
      setDeleting(false);
    }
  }

  async function handleStatusChange(event) {
    const status = event.target.value;
    await updateProject(projectId, { status });
    queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  }

  async function handleSaveRepo(event) {
    event.preventDefault();
    setRepoError("");
    setSavingRepo(true);
    try {
      await updateProject(projectId, { github_repo: githubRepo || null });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
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
      await updateProject(projectId, { github_token: githubToken });
      setGithubToken("");
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
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
      await updateProject(projectId, { clear_github_token: true });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    } catch (err) {
      setTokenError(err.message || "Não foi possível remover o token.");
    } finally {
      setClearingToken(false);
    }
  }

  async function handleSync() {
    setSyncError("");
    setSyncing(true);
    try {
      const result = await syncProjectGithub(projectId);
      setSyncResult(result);
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project-commits", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project-pull-requests", projectId] });
    } catch (err) {
      setSyncError(err.message || "Não foi possível sincronizar com o GitHub.");
    } finally {
      setSyncing(false);
    }
  }

  if (isLoading) {
    return (
      <main className="page">
        <p>Carregando projeto...</p>
      </main>
    );
  }

  if (!project) {
    return (
      <main className="page">
        <p>Projeto não encontrado.</p>
      </main>
    );
  }

  return (
    <main className="page">
      <Link to="/projects" className="back-link">
        ← Voltar para projetos
      </Link>

      <div className="page-header">
        {isAdmin ? (
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
        ) : (
          <h1>{project.name}</h1>
        )}
        {isAdmin ? (
          <select value={project.status} onChange={handleStatusChange}>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : (
          <span className={`badge badge-${project.status}`}>{STATUS_LABELS[project.status]}</span>
        )}
      </div>
      {nameError && <p className="error">{nameError}</p>}

      <p>{project.description || "Sem descrição."}</p>
      <p className="meta">Gestor responsável: {project.manager ? project.manager.name : "—"}</p>

      {isAdmin && (
        <div className="page-actions">
          <button type="button" onClick={handleDeleteProject} disabled={deleting} className="danger-button">
            {deleting ? "Excluindo..." : "Excluir projeto"}
          </button>
        </div>
      )}
      {deleteError && <p className="error">{deleteError}</p>}

      <h2>Andamento</h2>

      {isAdmin && (
        <form className="form" onSubmit={handleAddUpdate}>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Descreva o andamento..."
            rows={3}
            required
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Enviando..." : "Registrar andamento"}
          </button>
        </form>
      )}

      <ul className="update-list">
        {updates?.length === 0 && <p>Nenhuma atualização registrada ainda.</p>}
        {updates?.map((update) => (
          <li key={update.id}>
            <p>{update.message}</p>
            <span className="meta">
              {update.author ? update.author.name : "—"} em {new Date(update.created_at).toLocaleString("pt-BR")}
            </span>
          </li>
        ))}
      </ul>

      <h2>GitHub</h2>

      {isAdmin && (
        <form className="form github-repo-form" onSubmit={handleSaveRepo}>
          <label htmlFor="github_repo">Repositório (owner/repo)</label>
          <input
            id="github_repo"
            value={githubRepo}
            onChange={(e) => setGithubRepo(e.target.value)}
            placeholder="owner/repo"
          />
          {repoError && <p className="error">{repoError}</p>}
          <button type="submit" disabled={savingRepo}>
            {savingRepo ? "Salvando..." : "Salvar repositório"}
          </button>
        </form>
      )}

      {isAdmin && (
        <form className="form github-token-form" onSubmit={handleSaveToken}>
          <label htmlFor="github_token">
            Token de acesso específico deste repositório —{" "}
            {project.has_github_token ? "configurado" : "não configurado (usando o token padrão do sistema)"}
          </label>
          <input
            id="github_token"
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
      )}

      {!project.github_repo && <p className="meta">Nenhum repositório configurado.</p>}

      {project.github_repo && (
        <>
          <p className="meta">
            Repositório: {project.github_repo}
            {project.github_synced_at && (
              <> — última sincronização em {new Date(project.github_synced_at).toLocaleString("pt-BR")}</>
            )}
          </p>

          {isAdmin && (
            <button type="button" onClick={handleSync} disabled={syncing}>
              {syncing ? "Sincronizando..." : "Sincronizar agora"}
            </button>
          )}
          {syncError && <p className="error">{syncError}</p>}
          {syncResult && (
            <p className="meta">
              {syncResult.commits_synced} commit(s) e {syncResult.pull_requests_synced} pull request(s)
              sincronizados.
            </p>
          )}

          <h3>Pull requests</h3>
          <ul className="update-list">
            {pullRequests?.length === 0 && <p>Nenhum pull request sincronizado ainda.</p>}
            {pullRequests?.map((pr) => (
              <li key={pr.id}>
                <p>
                  <a href={pr.url} target="_blank" rel="noreferrer">
                    #{pr.number} {pr.title}
                  </a>{" "}
                  <span className={`badge badge-status-${pr.state === "merged" ? "concluido" : pr.state === "closed" ? "cancelado" : "aberto"}`}>
                    {pr.state}
                  </span>
                </p>
                <span className="meta">
                  {pr.author_login || "—"} em {new Date(pr.opened_at).toLocaleString("pt-BR")}
                  {pr.ticket_id && (
                    <>
                      {" "}
                      —{" "}
                      <Link to={`/tickets/${pr.ticket_id}`}>vinculado ao ticket #{pr.ticket_id}</Link>
                    </>
                  )}
                </span>
              </li>
            ))}
          </ul>

          <h3>Commits</h3>
          <ul className="update-list">
            {commits?.length === 0 && <p>Nenhum commit sincronizado ainda.</p>}
            {commits?.map((commit) => (
              <li key={commit.id}>
                <p>
                  <a href={commit.url} target="_blank" rel="noreferrer">
                    {commit.sha.slice(0, 7)}
                  </a>{" "}
                  {commit.message.split("\n")[0]}
                </p>
                <span className="meta">
                  {commit.author_name || "—"} em {new Date(commit.committed_at).toLocaleString("pt-BR")}
                  {commit.ticket_id && (
                    <>
                      {" "}
                      — <Link to={`/tickets/${commit.ticket_id}`}>vinculado ao ticket #{commit.ticket_id}</Link>
                    </>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  );
}
