"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getNotificationPreferences,
  listNotifications,
  markNotificationClicked,
  markNotificationRead,
  updateNotificationPreferences,
} from "@/lib/api/notifications";
import { queryKeys } from "@/lib/queryKeys";
import type { NotificationPreferences, NotificationResponse } from "@/lib/types";

const PREFERENCE_LABELS: { key: keyof NotificationPreferences; label: string }[] = [
  { key: "match_needs_players", label: "Match needs players" },
  { key: "team_challenge", label: "Team challenges" },
  { key: "match_reminder", label: "Match reminders" },
  { key: "reward_earned", label: "Rewards earned" },
  { key: "promoted_from_waitlist", label: "Promoted from waitlist" },
];

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const { data: notifications, isLoading } = useQuery({
    queryKey: queryKeys.notifications(unreadOnly),
    queryFn: () => listNotifications({ unreadOnly }),
  });

  const { data: preferences } = useQuery({
    queryKey: queryKeys.notificationPreferences(),
    queryFn: getNotificationPreferences,
  });

  const readMutation = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const prefsMutation = useMutation({
    mutationFn: (payload: NotificationPreferences) => updateNotificationPreferences(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.notificationPreferences() }),
  });

  function handleOpen(n: NotificationResponse) {
    markNotificationClicked(n.notification_id);
    if (!n.read_at) readMutation.mutate(n.notification_id);
  }

  function togglePreference(key: keyof NotificationPreferences) {
    if (!preferences) return;
    prefsMutation.mutate({ ...preferences, [key]: !preferences[key] });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Notifications</h1>
        <label className="flex items-center gap-2 text-sm text-neutral-600">
          <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
          Unread only
        </label>
      </div>

      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
      {notifications && notifications.length === 0 && (
        <p className="text-sm text-neutral-500">No notifications.</p>
      )}

      <div className="space-y-2">
        {notifications?.map((n) => (
          <button
            key={n.notification_id}
            onClick={() => handleOpen(n)}
            className={`w-full text-left rounded-xl border px-4 py-3 ${
              n.read_at ? "border-neutral-200 bg-white" : "border-emerald-200 bg-emerald-50"
            }`}
          >
            <p className="text-sm font-medium text-neutral-900">{n.title}</p>
            <p className="text-sm text-neutral-500">{n.body}</p>
            <p className="text-xs text-neutral-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
          </button>
        ))}
      </div>

      {preferences && (
        <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
          <p className="text-sm font-semibold text-neutral-700">Preferences</p>
          {PREFERENCE_LABELS.map(({ key, label }) => (
            <label key={key} className="flex items-center justify-between text-sm text-neutral-600">
              {label}
              <input
                type="checkbox"
                checked={Boolean(preferences[key])}
                onChange={() => togglePreference(key)}
              />
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
