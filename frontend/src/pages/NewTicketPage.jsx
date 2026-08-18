import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchProjects } from "../services/projects.js";
import { createTicket } from "../services/tickets.js";
import { TYPE_OPTIONS, PRIORITY_OPTIONS } from "../utils/ticketLabels.js";

export default function NewTicketPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [searchParams] = useSearchParams();
  const defaultProjectId = searchParams.get("project_id") || "";

  const [projectId, setProjectId] = useState(defaultProjectId);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("outro");
  const [priority, setPriority] = useState("media");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: () => fetchProjects() });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        project_id: Number(projectId),
        title,
        description: description || null,
      };
      if (isAdmin) {
        payload.type = type;
        payload.priority = priority;
      }
      const ticket = await createTicket(payload);
      navigate(`/tickets/${ticket.id}`, { replace: true });
    } catch (err) {
      setError(err.message || "Não foi possível abrir a solicitação.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <h1>Nova solicitação</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label htmlFor="project">Projeto</label>
        <select id="project" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
          <option value="" disabled>
            Selecione um projeto
          </option>
          {projects?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>

        <label htmlFor="title">Título</label>
        <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus />

        <label htmlFor="description">Descrição</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={5}
          placeholder="Descreva o que você precisa..."
        />

        {isAdmin && (
          <>
            <label htmlFor="type">Tipo</label>
            <select id="type" value={type} onChange={(e) => setType(e.target.value)}>
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <label htmlFor="priority">Prioridade</label>
            <select id="priority" value={priority} onChange={(e) => setPriority(e.target.value)}>
              {PRIORITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </>
        )}

        {!isAdmin && (
          <p className="meta">O tipo e a prioridade da solicitação serão definidos pelo administrador.</p>
        )}

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting || !projectId}>
          {submitting ? "Enviando..." : "Abrir solicitação"}
        </button>
      </form>
    </main>
  );
}
