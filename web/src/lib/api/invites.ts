import { apiFetch } from "./client";
import type { InviteCandidate, InvitePreferences, MatchInviteResponse } from "@/lib/types";

export function getInviteCandidates(tenantId: string, bookingId: string) {
  return apiFetch<InviteCandidate[]>(`/venues/${tenantId}/bookings/${bookingId}/invite-candidates`);
}

export function sendInvites(
  tenantId: string,
  bookingId: string,
  invites: { to_uid: string; tier: string }[]
) {
  return apiFetch<MatchInviteResponse[]>(`/venues/${tenantId}/bookings/${bookingId}/invites`, {
    method: "POST",
    body: JSON.stringify({ invites }),
  });
}

export function getMyInvites() {
  return apiFetch<MatchInviteResponse[]>(`/invites/me`);
}

export function respondToInvite(inviteId: string, accept: boolean) {
  return apiFetch<{ success: boolean; status: string; booking_id?: string }>(
    `/invites/${inviteId}/respond`,
    { method: "POST", body: JSON.stringify({ accept }) }
  );
}

export function getInvitePreferences() {
  return apiFetch<InvitePreferences>(`/players/me/invite-preferences`);
}

export function updateInvitePreferences(payload: Partial<InvitePreferences>) {
  return apiFetch<InvitePreferences>(`/players/me/invite-preferences`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
