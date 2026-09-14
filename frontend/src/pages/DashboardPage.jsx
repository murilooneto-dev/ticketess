import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import StatBarList from "../components/StatBarList.jsx";
import { fetchDashboardSummary } from "../services/dashboard.js";
import { STATUS_LABELS as PROJECT_STATUS_LABELS } from "../utils/projectStatus.js";
import {
  PRIORITY_LABELS,
  STATUS_LABELS as TICKET_STATUS_LABELS,
  TYPE_LABELS,
} from "../utils/ticketLabels.js";

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: fetchDashboardSummary,
  });

  return (
    <main className="page">
      <h1>Dashboard</h1>

      {isLoading && <p>Carregando dashboard...</p>}
      {isError && <p className="error">Não foi possível carregar o dashboard.</p>}

      {data && (
        <>
          <div className="stat-cards">
            <div className="stat-card">
              <span className="stat-card-value">{data.total_projects}</span>
              <span className="stat-card-label">Projetos</span>
            </div>
            <div className="stat-card">
              <span className="stat-card-value">{data.total_tickets}</span>
              <span className="stat-card-label">Solicitações</span>
            </div>
            <div className="stat-card">
              <span className="stat-card-value">{data.open_tickets}</span>
              <span className="stat-card-label">Solicitações em aberto</span>
            </div>
          </div>

          <div className="dashboard-grid">
            <section>
              <h2>Solicitações por status</h2>
              <StatBarList data={data.tickets_by_status} labels={TICKET_STATUS_LABELS} colorPrefix="badge-status" />
            </section>

            <section>
              <h2>Solicitações por prioridade</h2>
              <StatBarList
                data={data.tickets_by_priority}
                labels={PRIORITY_LABELS}
                colorPrefix="badge-priority"
              />
            </section>

            <section>
              <h2>Projetos por status</h2>
              <StatBarList data={data.projects_by_status} labels={PROJECT_STATUS_LABELS} colorPrefix="badge" />
            </section>
          </div>

          <div className="dashboard-grid">
            <section>
              <h2>Solicitações recentes</h2>
              {data.recent_tickets.length === 0 && <p className="meta">Nenhuma solicitação ainda.</p>}
              <ul className="update-list">
                {data.recent_tickets.map((ticket) => (
                  <li key={ticket.id}>
                    <p>
                      <Link to={`/tickets/${ticket.id}`}>{ticket.title}</Link>
                    </p>
                    <span className="meta">
                      {TYPE_LABELS[ticket.type]} em {new Date(ticket.created_at).toLocaleString("pt-BR")}
                    </span>
                  </li>
                ))}
              </ul>
            </section>

            {(data.recent_commits.length > 0 || data.recent_pull_requests.length > 0) && (
              <section>
                <h2>Atividade recente no GitHub</h2>
                <ul className="update-list">
                  {data.recent_pull_requests.map((pr) => (
                    <li key={`pr-${pr.id}`}>
                      <p>
                        <a href={pr.url} target="_blank" rel="noreferrer">
                          PR #{pr.number}: {pr.title}
                        </a>
                      </p>
                      <span className="meta">
                        {pr.state} — {new Date(pr.opened_at).toLocaleString("pt-BR")}
                      </span>
                    </li>
                  ))}
                  {data.recent_commits.map((commit) => (
                    <li key={`commit-${commit.id}`}>
                      <p>
                        <a href={commit.url} target="_blank" rel="noreferrer">
                          {commit.sha.slice(0, 7)}
                        </a>{" "}
                        {commit.message.split("\n")[0]}
                      </p>
                      <span className="meta">{new Date(commit.committed_at).toLocaleString("pt-BR")}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </>
      )}
    </main>
  );
}
