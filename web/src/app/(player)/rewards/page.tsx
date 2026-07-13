"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Gift, Sparkles, Trophy } from "lucide-react";
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
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { ApiError } from "@/lib/api/client";

const LEADERBOARDS: { kind: LeaderboardKind; label: string }[] = [
  { kind: "credits-monthly", label: "Credits" },
  { kind: "matches-hosted", label: "Matches hosted" },
  { kind: "new-players-referred", label: "Referrals" },
];

export default function RewardsPage() {
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

  const { data: leaderboard, isLoading: leaderboardLoading } = useQuery({
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
        <p className="text-ink-muted text-sm">Captain credits, referrals, and leaderboards.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {captainStats && (
        <div className="rounded-3xl bg-gradient-to-br from-brand-from to-brand-to p-5 text-white shadow-lg shadow-indigo-600/20">
          <div className="flex items-center gap-2 opacity-80 mb-3">
            <Trophy size={15} strokeWidth={2.25} />
            <p className="text-sm">Captain stats</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
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
        </div>
      )}

      <Card className="space-y-2.5">
        <p className="text-sm font-semibold flex items-center gap-1.5">
          <Gift size={15} strokeWidth={2.25} /> Referrals
        </p>
        {referralEarnings && (
          <p className="text-sm text-ink-muted">
            {referralEarnings.total_referrals} referrals · ₹{referralEarnings.total_credits_earned} earned
          </p>
        )}
        {referralMutation.data ? (
          <div className="rounded-xl bg-surface-muted px-3 py-2.5 space-y-0.5">
            <p className="font-mono text-sm font-semibold">{referralMutation.data.referral_code}</p>
            <p className="text-xs text-ink-muted break-all">{referralMutation.data.share_link}</p>
          </div>
        ) : (
          <Button
            variant="gradient"
            pill
            onClick={() => referralMutation.mutate()}
            disabled={referralMutation.isPending}
            className="text-sm px-5"
          >
            {referralMutation.isPending ? "Generating…" : "Get my referral code"}
          </Button>
        )}
      </Card>

      <div>
        <div className="flex gap-1 rounded-2xl bg-surface-muted p-1 mb-3">
          {LEADERBOARDS.map((lb) => (
            <button
              key={lb.kind}
              onClick={() => setLeaderboardKind(lb.kind)}
              className={`flex-1 rounded-xl py-2.5 text-xs font-semibold transition-colors ${
                leaderboardKind === lb.kind
                  ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                  : "text-ink-muted"
              }`}
            >
              {lb.label}
            </button>
          ))}
        </div>
        {leaderboardLoading && <FootballSpinner />}
        <div className="space-y-2">
          {leaderboard?.map((entry) => (
            <Card key={entry.player_uid}>
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-bold text-indigo-600">
                  #{entry.rank}
                </span>
                <span className="text-sm flex-1 truncate">{entry.player_name}</span>
                <span className="text-sm font-semibold shrink-0">
                  {leaderboardKind === "credits-monthly" && `${entry.credits_earned_month} cr`}
                  {leaderboardKind === "matches-hosted" && `${entry.matches_hosted_month} matches`}
                  {leaderboardKind === "new-players-referred" && `${entry.new_players_brought} players`}
                </span>
              </div>
            </Card>
          ))}
          {leaderboard && leaderboard.length === 0 && (
            <EmptyState icon={Trophy} title="No leaderboard data yet" />
          )}
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold mb-2">Reward history</p>
        {historyLoading && <FootballSpinner />}
        <div className="space-y-2">
          {history?.map((r) => (
            <Card key={r.reward_id}>
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-600">
                  <Sparkles size={16} strokeWidth={2.25} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{r.reason}</p>
                  <p className="text-xs text-ink-muted">{new Date(r.issued_at).toLocaleString()}</p>
                </div>
                <p className="text-sm font-semibold text-emerald-600 shrink-0">+{r.credits_amount} cr</p>
              </div>
            </Card>
          ))}
          {history && history.length === 0 && (
            <EmptyState icon={Sparkles} title="No rewards yet" description="Host a match to start earning." />
          )}
        </div>
      </div>
    </div>
  );
}
