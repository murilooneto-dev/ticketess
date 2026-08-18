import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { createProject, fetchManagers } from "../services/projects.js";

export default function NewProjectPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [managerId, setManagerId] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data: managers } = useQuery({ queryKey: ["managers"], queryFn: fetchManagers });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const project = await createProject({
        name,
        description: description || null,
        manager_id: managerId ? Number(managerId) : null,
        github_repo: githubRepo || null,
        github_token: githubToken || null,
      });
      navigate(`/projects/${project.id}`, { replace: true });
    } catch (err) {
      setError(err.message || "Não foi possível criar o projeto.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <h1>Novo projeto</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label htmlFor="name">Nome</label>
        <input id="name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />

        <label htmlFor="description">Descrição</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
        />

        <label htmlFor="manager">Gestor responsável</label>
        <select id="manager" value={managerId} onChange={(e) => setManagerId(e.target.value)}>
          <option value="">Sem gestor definido</option>
          {managers?.map((manager) => (
            <option key={manager.id} value={manager.id}>
              {manager.name}
            </option>
          ))}
        </select>

        <label htmlFor="github_repo">Repositório GitHub (opcional)</label>
        <input
          id="github_repo"
          value={githubRepo}
          onChange={(e) => setGithubRepo(e.target.value)}
          placeholder="owner/repo"
        />

        <label htmlFor="github_token">Token de acesso do repositório (opcional)</label>
        <input
          id="github_token"
          type="password"
          value={githubToken}
          onChange={(e) => setGithubToken(e.target.value)}
          placeholder="Deixe em branco para usar o token padrão do sistema"
          autoComplete="off"
        />
        <p className="meta">
          Só preencha se este repositório exigir um token diferente do token global configurado no
          servidor (ex.: repositório privado de outra organização).
        </p>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Salvando..." : "Criar projeto"}
        </button>
      </form>
    </main>
  );
}
