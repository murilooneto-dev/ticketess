import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { generateReport, fetchReports, reportDownloadUrl } from "../services/reports.js";

export default function ReportsPage() {
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
      await generateReport(periodStart, periodEnd);
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    } catch (err) {
      setError(err.message || "Não foi possível gerar o relatório.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="page">
      <Link to="/" className="back-link">
        ← Voltar
      </Link>

      <h1>Relatórios</h1>

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
          {generating ? "Gerando..." : "Gerar relatório"}
        </button>
      </form>

      {isLoading && <p>Carregando relatórios...</p>}
      {reports?.length === 0 && <p className="meta">Nenhum relatório gerado ainda.</p>}

      <ul className="update-list">
        {reports?.map((report) => (
          <li key={report.id}>
            <p>
              <a href={reportDownloadUrl(report.id)} target="_blank" rel="noreferrer">
                {report.period_start} a {report.period_end}
              </a>
            </p>
            <span className="meta">gerado em {new Date(report.created_at).toLocaleString("pt-BR")}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
