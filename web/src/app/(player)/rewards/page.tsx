"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createReferralCode,
  getLeaderboard,
  getMyCaptainStats,
  getMyReferralEarnings,
  getMyRewardHistory,
  LeaderboardKind,
} from "@/lib/api/rewards";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

const LEADERBOARDS: { kind: LeaderboardKind; label: string }[] = [
  { kind: "credits-monthly", label: "Credits" },
  { kind: "matches-hosted", label: "Matches hosted" },
  { kind: "new-players-referred", label: "Referrals" },
];

export default function RewardsPage() {
  const queryClient = useQueryClient();
  const [leaderboardKind, setLeaderboardKind] = useState<LeaderboardKind>("credits-monthly");
  const [error, setError] = useState<string | null>(null);

  const { data: captainStats } = useQuery({
    queryKey: queryKeys.myCaptainStats(),
    queryFn: getMyCaptainStats,
    retry: false,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: queryKeys.myRewardHistory(),
    queryFn: getMyRewardHistory,
  });

  const { data: referralEarnings } = useQuery({
    queryKey: queryKeys.myReferralEarnings(),
    queryFn: getMyReferralEarnings,
  });

  const { data: leaderboard } = useQuery({
    queryKey: queryKeys.leaderboard(leaderboardKind),
    queryFn: () => getLeaderboard(leaderboardKind),
  });

  const referralMutation = useMutation({
    mutationFn: createReferralCode,
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create referral code"),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Rewards</h1>
        <p className="text-neutral-500 text-sm">Captain credits, referrals, and leaderboards.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {captainStats && (
        <div className="rounded-2xl bg-emerald-600 text-white p-5 grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs opacity-80">Credits this month</p>
            <p className="text-xl font-bold">{captainStats.credits_this_month}</p>
          </div>
          <div>
            <p className="text-xs opacity-80">Matches hosted</p>
            <p className="text-xl font-bold">{captainStats.matches_hosted}</p>
          </div>
          <div>
            <p className="text-xs opacity-80">Total credits earned</p>
            <p className="text-xl font-bold">{captainStats.total_credits_earned}</p>
          </div>
          <div>
            <p className="text-xs opacity-80">Acceptance rate</p>
            <p className="text-xl font-bold">{captainStats.acceptance_rate}%</p>
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
        <p className="text-sm font-semibold text-neutral-700">Referrals</p>
        {referralEarnings && (
          <p className="text-sm text-neutral-600">
            {referralEarnings.total_referrals} referrals · ₹{referralEarnings.total_credits_earned} earned
          </p>
        )}
        {referralMutation.data ? (
          <div className="text-sm">
            <p className="font-mono text-neutral-900">{referralMutation.data.referral_code}</p>
            <p className="text-xs text-neutral-500 break-all">{referralMutation.data.share_link}</p>
          </div>
        ) : (
          <Button
            variant="secondary"
            onClick={() => referralMutation.mutate()}
            disabled={referralMutation.isPending}
          >
            {referralMutation.isPending ? "Generating…" : "Get my referral code"}
          </Button>
        )}
      </div>

      <div>
        <div className="flex gap-1 rounded-xl bg-neutral-100 p-1 mb-2">
          {LEADERBOARDS.map((lb) => (
            <button
              key={lb.kind}
              onClick={() => setLeaderboardKind(lb.kind)}
              className={`flex-1 rounded-lg py-1.5 text-xs font-medium ${
                leaderboardKind === lb.kind ? "bg-white shadow-sm text-neutral-900" : "text-neutral-500"
              }`}
            >
              {lb.label}
            </button>
          ))}
        </div>
        <div className="space-y-2">
          {leaderboard?.map((entry) => (
            <div
              key={entry.player_uid}
              className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-2"
            >
              <span className="text-sm text-neutral-700">
                #{entry.rank} {entry.player_name}
              </span>
              <span className="text-sm font-semibold text-neutral-900">
                {leaderboardKind === "credits-monthly" && `${entry.credits_earned_month} cr`}
                {leaderboardKind === "matches-hosted" && `${entry.matches_hosted_month} matches`}
                {leaderboardKind === "new-players-referred" && `${entry.new_players_brought} players`}
              </span>
            </div>
          ))}
          {leaderboard && leaderboard.length === 0 && (
            <p className="text-sm text-neutral-500">No data yet.</p>
          )}
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold text-neutral-700 mb-2">Reward history</p>
        {historyLoading && <p className="text-sm text-neutral-500">Loading…</p>}
        <div className="space-y-2">
          {history?.map((r) => (
            <div
              key={r.reward_id}
              className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-neutral-900">{r.reason}</p>
                <p className="text-xs text-neutral-400">{new Date(r.issued_at).toLocaleString()}</p>
              </div>
              <p className="text-sm font-semibold text-emerald-600">+{r.credits_amount} cr</p>
            </div>
          ))}
          {history && history.length === 0 && (
            <p className="text-sm text-neutral-500">No rewards yet — host a match to start earning.</p>
          )}
        </div>
      </div>
    </div>
  );
}
