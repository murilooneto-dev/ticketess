import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchDashboardSummary() {
  const response = await fetch(`${API_BASE_URL}/dashboard/summary`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}
