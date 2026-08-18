import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function syncProjectGithub(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/github/sync`, {
    method: "POST",
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchProjectCommits(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/github/commits`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchProjectPullRequests(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/github/pull-requests`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchTicketGithubActivity(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/github`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}
