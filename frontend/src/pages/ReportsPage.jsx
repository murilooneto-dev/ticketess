import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext.jsx";
import { generateReports, fetchReports, reportDownloadUrl } from "../services/reports.js";

const TYPE_LABELS = {
  technical: "Técnico",
  management: "Acompanhamento",
};

export default function ReportsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();

  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [error, setError] = useState("");
  const [generating, setGenerating] = useState(false);

  const { data: reports, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  async function handleGenerate(event) {
    event.preventDefault();
    setError("");
    setGenerating(true);
    try {
      await generateReports(periodStart, periodEnd);
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    } catch (err) {
      setError(err.message || "Não foi possível gerar os relatórios.");
    } finally {
      setGenerating(false);
    }
  }

  const technicalReports = reports?.filter((r) => r.type === "technical") || [];
  const managementReports = reports?.filter((r) => r.type === "management") || [];

  return (
    <main className="page">
      <h1>Relatórios</h1>

      {isAdmin && (
        <form className="form" onSubmit={handleGenerate}>
          <label htmlFor="period_start">Início do período (opcional)</label>
          <input
            id="period_start"
            type="date"
            value={periodStart}
            onChange={(e) => setPeriodStart(e.target.value)}
          />

          <label htmlFor="period_end">Fim do período (opcional)</label>
          <input id="period_end" type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />

          <p className="meta">Se não informado, gera para os últimos 7 dias.</p>

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={generating}>
            {generating ? "Gerando..." : "Gerar relatórios"}
          </button>
        </form>
      )}

      {isLoading && <p>Carregando relatórios...</p>}

      {isAdmin && (
        <>
          <h2>Relatório técnico</h2>
          {technicalReports.length === 0 && <p className="meta">Nenhum relatório técnico gerado ainda.</p>}
          <ul className="update-list">
            {technicalReports.map((report) => (
              <li key={report.id}>
                <p>
                  <a href={reportDownloadUrl(report.id)} target="_blank" rel="noreferrer">
                    {report.period_start} a {report.period_end}
                  </a>
                </p>
                <span className="meta">
                  {TYPE_LABELS[report.type]} — gerado em {new Date(report.created_at).toLocaleString("pt-BR")}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>Relatório de acompanhamento</h2>
      {managementReports.length === 0 && <p className="meta">Nenhum relatório de acompanhamento gerado ainda.</p>}
      <ul className="update-list">
        {managementReports.map((report) => (
          <li key={report.id}>
            <p>
              <a href={reportDownloadUrl(report.id)} target="_blank" rel="noreferrer">
                {report.period_start} a {report.period_end}
              </a>
            </p>
            <span className="meta">
              {TYPE_LABELS[report.type]} — gerado em {new Date(report.created_at).toLocaleString("pt-BR")}
            </span>
          </li>
        ))}
      </ul>
    </main>
  );
}
