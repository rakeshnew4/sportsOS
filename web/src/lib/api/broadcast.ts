import { apiFetch } from "./client";

export type BroadcastTarget = "all_players" | "all_admins" | "sport" | "court" | "team";

export interface BroadcastPayload {
  target: BroadcastTarget;
  title: string;
  body: string;
  sport?: string;
  court_id?: string;
  team_id?: string;
  tenant_id?: string;
  city?: string;
}

export function sendBroadcast(payload: BroadcastPayload) {
  return apiFetch<{ recipient_count: number }>(`/admin/broadcast`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
