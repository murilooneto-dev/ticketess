import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { createProject } from "../services/projects.js";

export default function NewProjectForm({ onDone }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createProject({
        name,
        description: description || null,
        github_repo: githubRepo || null,
        github_token: githubToken || null,
      });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      onDone();
    } catch (err) {
      setError(err.message || "Não foi possível criar o projeto.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label htmlFor="new_project_name">Nome</label>
      <input id="new_project_name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />

      <label htmlFor="new_project_description">Descrição</label>
      <textarea
        id="new_project_description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={3}
      />

      <label htmlFor="new_project_github_repo">Repositório GitHub (opcional)</label>
      <input
        id="new_project_github_repo"
        value={githubRepo}
        onChange={(e) => setGithubRepo(e.target.value)}
        placeholder="owner/repo"
      />

      <label htmlFor="new_project_github_token">Token de acesso do repositório (opcional)</label>
      <input
        id="new_project_github_token"
        type="password"
        value={githubToken}
        onChange={(e) => setGithubToken(e.target.value)}
        placeholder="Deixe em branco para usar o token padrão do sistema"
        autoComplete="off"
      />

      {error && <p className="error">{error}</p>}

      <button type="submit" disabled={submitting}>
        {submitting ? "Salvando..." : "Criar projeto"}
      </button>
    </form>
  );
}
