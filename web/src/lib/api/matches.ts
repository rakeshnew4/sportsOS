import { apiFetch } from "./client";
import type { BookingResponse, MatchRequestResponse, MatchResponse, ParticipantResponse } from "@/lib/types";

export function listOpenMatches(params?: { sport?: string; date?: string }) {
  const qs = new URLSearchParams();
  if (params?.sport) qs.set("sport", params.sport);
  if (params?.date) qs.set("date", params.date);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<MatchResponse[]>(`/matches${suffix}`);
}

export function joinMatch(tenantId: string, bookingId: string) {
  return apiFetch<BookingResponse>(`/venues/${tenantId}/bookings/${bookingId}/join`, {
    method: "POST",
  });
}

export function listParticipants(tenantId: string, bookingId: string) {
  return apiFetch<ParticipantResponse[]>(`/venues/${tenantId}/bookings/${bookingId}/participants`);
}

export interface CreateMatchRequestPayload {
  court_id: string;
  date: string;
  start_time: string;
  end_time: string;
}

export function createMatchRequest(tenantId: string, payload: CreateMatchRequestPayload) {
  return apiFetch<MatchRequestResponse>(`/venues/${tenantId}/match-requests`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listMatchRequests(tenantId: string, params: { courtId: string; date: string }) {
  const qs = new URLSearchParams({ court_id: params.courtId, date: params.date });
  return apiFetch<MatchRequestResponse[]>(`/venues/${tenantId}/match-requests?${qs.toString()}`);
}

export function cancelMatchRequest(tenantId: string, requestId: string) {
  return apiFetch<MatchRequestResponse>(`/venues/${tenantId}/match-requests/${requestId}`, {
    method: "DELETE",
  });
}

export function listMyMatchRequests() {
  return apiFetch<MatchRequestResponse[]>(`/players/me/match-requests`);
}
