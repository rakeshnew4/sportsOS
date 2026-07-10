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
import { getInvitePreferences, respondToInvite, updateInvitePreferences } from "@/lib/api/invites";
import { queryKeys } from "@/lib/queryKeys";
import type { InvitePreferences, NotificationPreferences, NotificationResponse } from "@/lib/types";

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
  const [respondedInviteIds, setRespondedInviteIds] = useState<string[]>([]);

  const { data: notifications, isLoading } = useQuery({
    queryKey: queryKeys.notifications(unreadOnly),
    queryFn: () => listNotifications({ unreadOnly }),
  });

  const { data: preferences } = useQuery({
    queryKey: queryKeys.notificationPreferences(),
    queryFn: getNotificationPreferences,
  });

  const { data: invitePrefs } = useQuery({
    queryKey: queryKeys.invitePreferences(),
    queryFn: getInvitePreferences,
  });

  const readMutation = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const prefsMutation = useMutation({
    mutationFn: (payload: NotificationPreferences) => updateNotificationPreferences(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.notificationPreferences() }),
  });

  const invitePrefsMutation = useMutation({
    mutationFn: (payload: Partial<InvitePreferences>) => updateInvitePreferences(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.invitePreferences() }),
  });

  const respondMutation = useMutation({
    mutationFn: ({ inviteId, accept }: { inviteId: string; accept: boolean }) => respondToInvite(inviteId, accept),
    onSuccess: (_data, { inviteId }) => {
      setRespondedInviteIds((prev) => [...prev, inviteId]);
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
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
        {notifications?.map((n) => {
          const inviteId = n.type === "match_invite" ? (n.data?.invite_id as string | undefined) : undefined;
          const respondedInvite = inviteId && respondedInviteIds.includes(inviteId);
          return (
            <div
              key={n.notification_id}
              onClick={() => handleOpen(n)}
              className={`w-full text-left rounded-xl border px-4 py-3 ${
                n.read_at ? "border-neutral-200 bg-white" : "border-emerald-200 bg-emerald-50"
              }`}
            >
              <p className="text-sm font-medium text-neutral-900">{n.title}</p>
              <p className="text-sm text-neutral-500">{n.body}</p>
              <p className="text-xs text-neutral-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
              {inviteId && !respondedInvite && (
                <div className="flex gap-2 mt-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => respondMutation.mutate({ inviteId, accept: true })}
                    disabled={respondMutation.isPending}
                    className="rounded-full bg-emerald-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => respondMutation.mutate({ inviteId, accept: false })}
                    disabled={respondMutation.isPending}
                    className="rounded-full border border-neutral-300 px-3 py-1 text-xs font-medium text-neutral-600 disabled:opacity-50"
                  >
                    Decline
                  </button>
                </div>
              )}
              {inviteId && respondedInvite && (
                <p className="text-xs text-emerald-600 mt-2">You're in!</p>
              )}
            </div>
          );
        })}
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

      {invitePrefs && (
        <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
          <p className="text-sm font-semibold text-neutral-700">Invite settings</p>
          <label className="flex items-center justify-between text-sm text-neutral-600">
            Let players I haven't played with invite me
            <input
              type="checkbox"
              checked={invitePrefs.open_to_invites}
              onChange={() => invitePrefsMutation.mutate({ open_to_invites: !invitePrefs.open_to_invites })}
            />
          </label>
          {invitePrefs.open_to_invites && (
            <label className="flex items-center justify-between text-sm text-neutral-600">
              Radius (km)
              <input
                type="number"
                min={1}
                max={100}
                defaultValue={invitePrefs.radius_km}
                onBlur={(e) => {
                  const value = Number(e.target.value);
                  if (value > 0) invitePrefsMutation.mutate({ radius_km: value });
                }}
                className="w-20 rounded-lg border border-neutral-300 px-2 py-1 text-right"
              />
            </label>
          )}
        </div>
      )}
    </div>
  );
}
