import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchUsers() {
  const response = await fetch(`${API_BASE_URL}/users`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function createUserAccount(data) {
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function updateUserAccount(userId, data) {
  const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}
