import { apiFetch } from "./client";
import type { NotificationPreferences, NotificationResponse } from "@/lib/types";

export function listNotifications(params?: { unreadOnly?: boolean; limit?: number }) {
  const qs = new URLSearchParams();
  if (params?.unreadOnly) qs.set("unread_only", "true");
  if (params?.limit) qs.set("limit", String(params.limit));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<NotificationResponse[]>(`/notifications/me${suffix}`);
}

export function markNotificationRead(notificationId: string) {
  return apiFetch<{ success: boolean }>(`/notifications/me/${notificationId}/read`, { method: "POST" });
}

export function markNotificationClicked(notificationId: string) {
  return apiFetch<{ success: boolean }>(`/notifications/me/${notificationId}/clicked`, { method: "POST" });
}

export function getNotificationPreferences() {
  return apiFetch<NotificationPreferences>(`/notifications/me/preferences`);
}

// Backend stub — accepts and echoes success but doesn't persist preferences yet.
export function updateNotificationPreferences(payload: NotificationPreferences) {
  return apiFetch<{ success: boolean; message: string }>(`/notifications/me/preferences`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
