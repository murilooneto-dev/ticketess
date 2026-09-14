import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchReports() {
  const response = await fetch(`${API_BASE_URL}/reports`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function generateReport(periodStart, periodEnd) {
  const response = await fetch(`${API_BASE_URL}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      period_start: periodStart || null,
      period_end: periodEnd || null,
    }),
  });
  return handleApiResponse(response);
}

export function reportDownloadUrl(reportId) {
  return `${API_BASE_URL}/reports/${reportId}/download`;
}
