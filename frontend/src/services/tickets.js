import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchTickets({ projectId, status, priority, finalized = false } = {}) {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  if (finalized) params.set("finalized", "true");

  const response = await fetch(`${API_BASE_URL}/tickets?${params.toString()}`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchTicket(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function createTicket(data) {
  const response = await fetch(`${API_BASE_URL}/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function updateTicket(ticketId, data) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleApiResponse(response);
}

export async function finalizeTicket(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/finalize`, {
    method: "POST",
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchComments(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/comments`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function addComment(ticketId, message) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ message }),
  });
  return handleApiResponse(response);
}

export async function fetchHistory(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/history`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchAttachments(ticketId) {
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/attachments`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function uploadAttachment(ticketId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/attachments`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  return handleApiResponse(response);
}

export function attachmentDownloadUrl(ticketId, attachmentId) {
  return `${API_BASE_URL}/tickets/${ticketId}/attachments/${attachmentId}/download`;
}
