import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchProjectIdeas() {
  const response = await fetch(`${API_BASE_URL}/project-ideas`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function createProjectIdea(data) {
  const response = await fetch(`${API_BASE_URL}/project-ideas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function updateProjectIdeaStatus(ideaId, payload) {
  const response = await fetch(`${API_BASE_URL}/project-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleApiResponse(response);
}
