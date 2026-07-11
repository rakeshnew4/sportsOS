import { apiFetch } from "./client";
import type { PlayerProfile, SkillLevel } from "@/lib/types";

export function getMyProfile() {
  return apiFetch<PlayerProfile>(`/players/me/profile`);
}

export function getPlayerProfile(uid: string) {
  return apiFetch<PlayerProfile>(`/players/${uid}/profile`);
}

export function updateMySkills(skillLevels: Record<string, SkillLevel>) {
  return apiFetch<PlayerProfile>(`/players/me/skills`, {
    method: "PUT",
    body: JSON.stringify({ skill_levels: skillLevels }),
  });
}
