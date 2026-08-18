import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from "../services/notifications.js";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: unread } = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: fetchUnreadCount,
    refetchInterval: 30000,
  });

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: fetchNotifications,
    enabled: open,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  async function handleNotificationClick(notification) {
    if (!notification.is_read) {
      await markNotificationRead(notification.id);
      invalidate();
    }
    setOpen(false);
    if (notification.link) {
      navigate(notification.link);
    }
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead();
    invalidate();
  }

  const count = unread?.unread_count || 0;

  return (
    <div className="notification-bell">
      <button type="button" className="bell-button" onClick={() => setOpen((v) => !v)}>
        🔔{count > 0 && <span className="bell-badge">{count}</span>}
      </button>

      {open && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <span>Notificações</span>
            {count > 0 && (
              <button type="button" className="link-button" onClick={handleMarkAllRead}>
                Marcar todas como lidas
              </button>
            )}
          </div>
          {notifications?.length === 0 && <p className="meta">Nenhuma notificação.</p>}
          <ul>
            {notifications?.map((notification) => (
              <li
                key={notification.id}
                className={notification.is_read ? "read" : "unread"}
                onClick={() => handleNotificationClick(notification)}
              >
                <p className="notification-title">{notification.title}</p>
                <p className="notification-message">{notification.message}</p>
                <span className="meta">{new Date(notification.created_at).toLocaleString("pt-BR")}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
