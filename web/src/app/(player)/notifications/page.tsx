"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Settings2 } from "lucide-react";
import {
  getNotificationPreferences,
  listNotifications,
  markNotificationClicked,
  markNotificationRead,
  updateNotificationPreferences,
} from "@/lib/api/notifications";
import { getInvitePreferences, respondToInvite, updateInvitePreferences } from "@/lib/api/invites";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { Switch } from "@/components/ui/Switch";
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
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-bold">Notifications</h1>
        <button
          onClick={() => setUnreadOnly((v) => !v)}
          className={`shrink-0 rounded-full px-4 py-2 text-xs font-semibold transition-colors ${
            unreadOnly
              ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
              : "bg-surface-muted text-ink-muted hover:text-foreground"
          }`}
        >
          Unread only
        </button>
      </div>

      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      )}
      {notifications && notifications.length === 0 && (
        <EmptyState icon={Bell} title="No notifications" description="You're all caught up." />
      )}

      <div className="space-y-2">
        {notifications?.map((n) => {
          const inviteId = n.type === "match_invite" ? (n.data?.invite_id as string | undefined) : undefined;
          const respondedInvite = inviteId && respondedInviteIds.includes(inviteId);
          const isUnread = !n.read_at;
          return (
            <button
              key={n.notification_id}
              onClick={() => handleOpen(n)}
              className={`w-full text-left rounded-2xl border px-4 py-3 transition-colors ${
                isUnread ? "border-indigo-200 bg-indigo-50/60" : "border-border bg-surface"
              }`}
            >
              <div className="flex items-start gap-2.5">
                {isUnread && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-from" />}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{n.title}</p>
                  <p className="text-sm text-ink-muted">{n.body}</p>
                  <p className="text-xs text-ink-muted/70 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                  {inviteId && !respondedInvite && (
                    <div className="flex gap-2 mt-2.5" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="gradient"
                        pill
                        onClick={() => respondMutation.mutate({ inviteId, accept: true })}
                        disabled={respondMutation.isPending}
                        className="text-xs px-4 py-1.5"
                      >
                        Accept
                      </Button>
                      <Button
                        variant="secondary"
                        pill
                        onClick={() => respondMutation.mutate({ inviteId, accept: false })}
                        disabled={respondMutation.isPending}
                        className="text-xs px-4 py-1.5"
                      >
                        Decline
                      </Button>
                    </div>
                  )}
                  {inviteId && respondedInvite && (
                    <p className="text-xs font-medium text-emerald-600 mt-2">You&apos;re in!</p>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {preferences && (
        <Card className="space-y-3">
          <p className="text-sm font-semibold flex items-center gap-1.5">
            <Settings2 size={15} strokeWidth={2.25} /> Preferences
          </p>
          {PREFERENCE_LABELS.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm">{label}</span>
              <Switch checked={Boolean(preferences[key])} onChange={() => togglePreference(key)} label={label} />
            </div>
          ))}
        </Card>
      )}

      {invitePrefs && (
        <Card className="space-y-3">
          <p className="text-sm font-semibold">Invite settings</p>
          <div className="flex items-center justify-between">
            <span className="text-sm">Let players I haven&apos;t played with invite me</span>
            <Switch
              checked={invitePrefs.open_to_invites}
              onChange={() => invitePrefsMutation.mutate({ open_to_invites: !invitePrefs.open_to_invites })}
              label="Open to invites"
            />
          </div>
          {invitePrefs.open_to_invites && (
            <div className="flex items-center justify-between">
              <span className="text-sm">Radius (km)</span>
              <input
                type="number"
                min={1}
                max={100}
                defaultValue={invitePrefs.radius_km}
                onBlur={(e) => {
                  const value = Number(e.target.value);
                  if (value > 0) invitePrefsMutation.mutate({ radius_km: value });
                }}
                className="w-20 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-right focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
