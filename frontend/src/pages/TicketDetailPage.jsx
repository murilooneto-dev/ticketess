import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchTicketGithubActivity } from "../services/github.js";
import {
  addComment,
  attachmentDownloadUrl,
  fetchAttachments,
  fetchComments,
  fetchHistory,
  fetchTicket,
  updateTicket,
  uploadAttachment,
} from "../services/tickets.js";
import {
  FIELD_LABELS,
  PRIORITY_LABELS,
  PRIORITY_OPTIONS,
  STATUS_LABELS,
  STATUS_OPTIONS,
  TYPE_LABELS,
  TYPE_OPTIONS,
  historyValueLabel,
} from "../utils/ticketLabels.js";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isAdmin = user?.role === "admin";
  const fileInputRef = useRef(null);

  const [comment, setComment] = useState("");
  const [commentError, setCommentError] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);

  const { data: ticket, isLoading } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => fetchTicket(ticketId),
  });

  const { data: comments } = useQuery({
    queryKey: ["ticket-comments", ticketId],
    queryFn: () => fetchComments(ticketId),
  });

  const { data: attachments } = useQuery({
    queryKey: ["ticket-attachments", ticketId],
    queryFn: () => fetchAttachments(ticketId),
  });

  const { data: history } = useQuery({
    queryKey: ["ticket-history", ticketId],
    queryFn: () => fetchHistory(ticketId),
  });

  const { data: githubActivity } = useQuery({
    queryKey: ["ticket-github", ticketId],
    queryFn: () => fetchTicketGithubActivity(ticketId),
  });

  function invalidateTicket() {
    queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
    queryClient.invalidateQueries({ queryKey: ["ticket-history", ticketId] });
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
  }

  async function handleFieldChange(field, value) {
    await updateTicket(ticketId, { [field]: value });
    invalidateTicket();
  }

  async function handleAddComment(event) {
    event.preventDefault();
    setCommentError("");
    setSubmittingComment(true);
    try {
      await addComment(ticketId, comment);
      setComment("");
      queryClient.invalidateQueries({ queryKey: ["ticket-comments", ticketId] });
    } catch (err) {
      setCommentError(err.message || "Não foi possível enviar o comentário.");
    } finally {
      setSubmittingComment(false);
    }
  }

  async function handleFileUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError("");
    setUploading(true);
    try {
      await uploadAttachment(ticketId, file);
      queryClient.invalidateQueries({ queryKey: ["ticket-attachments", ticketId] });
    } catch (err) {
      setUploadError(err.message || "Não foi possível enviar o arquivo.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  if (isLoading) {
    return (
      <main className="page">
        <p>Carregando solicitação...</p>
      </main>
    );
  }

  if (!ticket) {
    return (
      <main className="page">
        <p>Solicitação não encontrada.</p>
      </main>
    );
  }

  return (
    <main className="page">
      <Link to="/tickets" className="back-link">
        ← Voltar para solicitações
      </Link>

      <div className="page-header">
        <h1>{ticket.title}</h1>
      </div>

      <div className="ticket-fields">
        <div>
          <span className="meta">Tipo</span>
          {isAdmin ? (
            <select value={ticket.type} onChange={(e) => handleFieldChange("type", e.target.value)}>
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <p>{TYPE_LABELS[ticket.type]}</p>
          )}
        </div>

        <div>
          <span className="meta">Prioridade</span>
          {isAdmin ? (
            <select value={ticket.priority} onChange={(e) => handleFieldChange("priority", e.target.value)}>
              {PRIORITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <span className={`badge badge-priority-${ticket.priority}`}>{PRIORITY_LABELS[ticket.priority]}</span>
          )}
        </div>

        <div>
          <span className="meta">Status</span>
          {isAdmin ? (
            <select value={ticket.status} onChange={(e) => handleFieldChange("status", e.target.value)}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <span className={`badge badge-status-${ticket.status}`}>{STATUS_LABELS[ticket.status]}</span>
          )}
        </div>
      </div>

      <p>{ticket.description || "Sem descrição."}</p>
      <p className="meta">Aberto por {ticket.author ? ticket.author.name : "—"}</p>

      <h2>Anexos</h2>
      <ul className="attachment-list">
        {attachments?.length === 0 && <p>Nenhum anexo enviado.</p>}
        {attachments?.map((attachment) => (
          <li key={attachment.id}>
            <a href={attachmentDownloadUrl(ticketId, attachment.id)} target="_blank" rel="noreferrer">
              {attachment.original_filename}
            </a>
            <span className="meta">
              {" "}
              ({formatBytes(attachment.size_bytes)}, enviado por {attachment.uploader ? attachment.uploader.name : "—"})
            </span>
          </li>
        ))}
      </ul>
      <input ref={fileInputRef} type="file" onChange={handleFileUpload} disabled={uploading} />
      {uploadError && <p className="error">{uploadError}</p>}

      <h2>Comentários</h2>
      <ul className="update-list">
        {comments?.length === 0 && <p>Nenhum comentário ainda.</p>}
        {comments?.map((c) => (
          <li key={c.id}>
            <p>{c.message}</p>
            <span className="meta">
              {c.author ? c.author.name : "—"} em {new Date(c.created_at).toLocaleString("pt-BR")}
            </span>
          </li>
        ))}
      </ul>

      <form className="form" onSubmit={handleAddComment}>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Escreva um comentário..."
          rows={3}
          required
        />
        {commentError && <p className="error">{commentError}</p>}
        <button type="submit" disabled={submittingComment}>
          {submittingComment ? "Enviando..." : "Comentar"}
        </button>
      </form>

      {githubActivity && (githubActivity.commits.length > 0 || githubActivity.pull_requests.length > 0) && (
        <>
          <h2>Atividade no GitHub</h2>
          <ul className="update-list">
            {githubActivity.pull_requests.map((pr) => (
              <li key={`pr-${pr.id}`}>
                <p>
                  <a href={pr.url} target="_blank" rel="noreferrer">
                    Pull request #{pr.number}: {pr.title}
                  </a>
                </p>
                <span className="meta">
                  {pr.state} — {pr.author_login || "—"} em {new Date(pr.opened_at).toLocaleString("pt-BR")}
                </span>
              </li>
            ))}
            {githubActivity.commits.map((commit) => (
              <li key={`commit-${commit.id}`}>
                <p>
                  <a href={commit.url} target="_blank" rel="noreferrer">
                    Commit {commit.sha.slice(0, 7)}
                  </a>{" "}
                  {commit.message.split("\n")[0]}
                </p>
                <span className="meta">
                  {commit.author_name || "—"} em {new Date(commit.committed_at).toLocaleString("pt-BR")}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>Histórico</h2>
      <ul className="update-list">
        {history?.length === 0 && <p>Nenhuma alteração registrada ainda.</p>}
        {history?.map((entry) => (
          <li key={entry.id}>
            <p>
              {FIELD_LABELS[entry.field] || entry.field}: {historyValueLabel(entry.field, entry.old_value)} →{" "}
              {historyValueLabel(entry.field, entry.new_value)}
            </p>
            <span className="meta">
              {entry.author ? entry.author.name : "—"} em {new Date(entry.created_at).toLocaleString("pt-BR")}
            </span>
          </li>
        ))}
      </ul>
    </main>
  );
}
