import { extractErrorMessage, handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchProjects() {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function createProject(data) {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function updateProject(projectId, data) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function deleteProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    let detail = null;
    try {
      detail = (await response.json()).detail;
    } catch {
      // corpo sem JSON, mantém mensagem padrão
    }
    throw new Error(extractErrorMessage(detail, `Erro ${response.status}`));
  }
}

export async function fetchProjectUpdates(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/updates`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function addProjectUpdate(projectId, message) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/updates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ message }),
  });
  return handleApiResponse(response);
}
