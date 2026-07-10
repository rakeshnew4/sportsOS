import { apiFetch } from "./client";
import type {
  TeamCreateRequest,
  TeamInviteRequest,
  TeamMember,
  TeamOpponentRequest,
  TeamOpponentResponse,
  TeamResponse,
} from "@/lib/types";

export function listTeams(sport?: string) {
  const suffix = sport ? `?sport=${sport}` : "";
  return apiFetch<TeamResponse[]>(`/teams${suffix}`);
}

export function listMyTeams() {
  return apiFetch<TeamResponse[]>(`/teams/me`);
}

export function suggestTeamNames(sport: string, playerName: string) {
  const qs = new URLSearchParams({ sport, player_name: playerName });
  return apiFetch<{ suggestions: string[] }>(`/teams/suggest-names?${qs.toString()}`);
}

export function discoverOpponentChallenges(params?: { sport?: string; date?: string }) {
  const qs = new URLSearchParams();
  if (params?.sport) qs.set("sport", params.sport);
  if (params?.date) qs.set("date", params.date);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<TeamOpponentResponse[]>(`/teams/available${suffix}`);
}

export function getTeam(teamId: string) {
  return apiFetch<TeamResponse>(`/teams/${teamId}`);
}

export function createTeam(payload: TeamCreateRequest) {
  return apiFetch<TeamResponse>(`/teams`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTeamMembers(teamId: string) {
  return apiFetch<TeamMember[]>(`/teams/${teamId}/members`);
}

export function inviteTeamMember(teamId: string, payload: TeamInviteRequest) {
  return apiFetch<TeamMember>(`/teams/${teamId}/members`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeTeamMember(teamId: string, playerUid: string) {
  return apiFetch<{ success: boolean; message: string }>(`/teams/${teamId}/members/${playerUid}`, {
    method: "DELETE",
  });
}

export function createOpponentChallenge(teamId: string, payload: TeamOpponentRequest) {
  return apiFetch<TeamOpponentResponse>(`/teams/${teamId}/challenges`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTeamChallenges(teamId: string) {
  return apiFetch<TeamOpponentResponse[]>(`/teams/${teamId}/challenges`);
}

export function acceptOpponentChallenge(teamId: string, challengeId: string) {
  return apiFetch<{ success: boolean; message: string; booking_id?: string; match_date?: string }>(
    `/teams/${teamId}/challenges/${challengeId}/accept`,
    { method: "POST" }
  );
}

export function rejectOpponentChallenge(teamId: string, challengeId: string) {
  return apiFetch<{ success: boolean; message: string }>(
    `/teams/${teamId}/challenges/${challengeId}/reject`,
    { method: "POST" }
  );
}

export function getTeamStats(teamId: string) {
  return apiFetch<Record<string, unknown>>(`/teams/${teamId}/stats`);
}

export function getTeamHistory(teamId: string, limit = 10) {
  return apiFetch<{ team_id: string; team_name: string; total_matches: number; recent_matches: unknown[] }>(
    `/teams/${teamId}/history?limit=${limit}`
  );
}
