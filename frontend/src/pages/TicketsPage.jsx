import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { fetchTickets } from "../services/tickets.js";
import { PRIORITY_LABELS, STATUS_LABELS, TYPE_LABELS } from "../utils/ticketLabels.js";

export default function TicketsPage() {
  const { user } = useAuth();
  const isOperador = user?.role === "operador";
  const [onlyMine, setOnlyMine] = useState(false);
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");

  const { data: tickets, isLoading, isError } = useQuery({
    queryKey: ["tickets", onlyMine, status, priority],
    queryFn: () => fetchTickets({ mine: onlyMine, status: status || undefined, priority: priority || undefined }),
  });

  return (
    <main className="page">
      <div className="page-header">
        <h1>Solicitações</h1>
        <div className="page-actions">
          {!isOperador && (
            <label className="checkbox-label">
              <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} />
              Ver apenas minhas solicitações
            </label>
          )}
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos os status</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
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
          <Link className="button-link" to="/tickets/new">
            Nova solicitação
          </Link>
        </div>
      </div>

      {isLoading && <p>Carregando solicitações...</p>}
      {isError && <p className="error">Não foi possível carregar as solicitações.</p>}
      {tickets && tickets.length === 0 && <p>Nenhuma solicitação encontrada.</p>}

      {tickets && tickets.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Tipo</th>
              <th>Prioridade</th>
              <th>Status</th>
              <th>Autor</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.id}>
                <td>
                  <Link to={`/tickets/${ticket.id}`}>{ticket.title}</Link>
                </td>
                <td>{TYPE_LABELS[ticket.type]}</td>
                <td>
                  <span className={`badge badge-priority-${ticket.priority}`}>{PRIORITY_LABELS[ticket.priority]}</span>
                </td>
                <td>
                  <span className={`badge badge-status-${ticket.status}`}>{STATUS_LABELS[ticket.status]}</span>
                </td>
                <td>{ticket.author ? ticket.author.name : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
