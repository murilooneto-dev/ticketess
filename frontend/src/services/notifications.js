import { handleApiResponse } from "../utils/apiError.js";

const API_BASE_URL = "/api";

export async function fetchNotifications() {
  const response = await fetch(`${API_BASE_URL}/notifications`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function fetchUnreadCount() {
  const response = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function markNotificationRead(notificationId) {
  const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
    method: "POST",
    credentials: "include",
  });
  return handleApiResponse(response);
}

export async function markAllNotificationsRead() {
  const response = await fetch(`${API_BASE_URL}/notifications/read-all`, {
    method: "POST",
    credentials: "include",
  });
  return handleApiResponse(response);
}
