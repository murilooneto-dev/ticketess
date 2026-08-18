const API_BASE_URL = "/api";

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/system/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}
