import { apiFetch } from "./client";
import type { CaptainLeaderboardEntry, CaptainStatsResponse, ReferralTracking, RewardRecord } from "@/lib/types";

export function getMyRewardHistory() {
  return apiFetch<RewardRecord[]>(`/rewards/me/history`);
}

export function getMyCaptainStats() {
  return apiFetch<CaptainStatsResponse>(`/rewards/me/captain`);
}

export type LeaderboardKind = "credits-monthly" | "matches-hosted" | "new-players-referred";

export function getLeaderboard(kind: LeaderboardKind, limit = 10) {
  return apiFetch<CaptainLeaderboardEntry[]>(`/rewards/leaderboard/${kind}?limit=${limit}`);
}

export function getMyReferrals() {
  return apiFetch<ReferralTracking[]>(`/rewards/me/referrals`);
}

export function getMyReferralEarnings() {
  return apiFetch<{
    total_referrals: number;
    total_credits_earned: number;
    avg_ltv_per_referral: number;
    referrals_this_month: number;
    top_referrer_rank: number | null;
  }>(`/rewards/me/referral-earnings`);
}

export function createReferralCode() {
  return apiFetch<{ referral_code: string; share_link: string; description: string }>(
    `/rewards/me/referrals/create-code`,
    { method: "POST" }
  );
}
