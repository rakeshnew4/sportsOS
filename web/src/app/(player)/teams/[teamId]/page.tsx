"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Star, Swords, UserPlus, Users2 } from "lucide-react";
import {
  acceptOpponentChallenge,
  createOpponentChallenge,
  getTeam,
  inviteTeamMember,
  listTeamChallenges,
  rejectOpponentChallenge,
  removeTeamMember,
} from "@/lib/api/teams";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

const CHALLENGE_BADGE_VARIANT: Record<string, "confirmed" | "pending" | "cancelled" | "neutral"> = {
  pending: "pending",
  accepted: "confirmed",
  rejected: "cancelled",
  expired: "neutral",
};

export default function TeamDetailPage({ params }: { params: Promise<{ teamId: string }> }) {
  const { teamId } = use(params);
  const session = useSession();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [inviteUid, setInviteUid] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [challengeDate, setChallengeDate] = useState("");
  const [challengeTime, setChallengeTime] = useState("");
  const [numPlayers, setNumPlayers] = useState("10");

  const { data: team, isLoading } = useQuery({
    queryKey: queryKeys.team(teamId),
    queryFn: () => getTeam(teamId),
  });

  const { data: challenges } = useQuery({
    queryKey: queryKeys.teamChallenges(teamId),
    queryFn: () => listTeamChallenges(teamId),
  });

  const isCaptain = team?.captain_uid === session.uid;

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: queryKeys.team(teamId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.teamChallenges(teamId) });
  }

  const inviteMutation = useMutation({
    mutationFn: () => inviteTeamMember(teamId, { player_uid: inviteUid, player_name: inviteName }),
    onSuccess: () => {
      setError(null);
      setInviteUid("");
      setInviteName("");
      invalidate();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not invite player"),
  });

  const removeMutation = useMutation({
    mutationFn: (uid: string) => removeTeamMember(teamId, uid),
    onSuccess: () => invalidate(),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not remove player"),
  });

  const createChallengeMutation = useMutation({
    mutationFn: () =>
      createOpponentChallenge(teamId, {
        sport: team!.sport,
        date: challengeDate,
        time: challengeTime,
        number_of_players: Number(numPlayers),
      }),
    onSuccess: () => {
      setError(null);
      setChallengeDate("");
      setChallengeTime("");
      invalidate();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create challenge"),
  });

  const acceptMutation = useMutation({
    mutationFn: (challengeId: string) => acceptOpponentChallenge(teamId, challengeId),
    onSuccess: () => invalidate(),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not accept challenge"),
  });

  const rejectMutation = useMutation({
    mutationFn: (challengeId: string) => rejectOpponentChallenge(teamId, challengeId),
    onSuccess: () => invalidate(),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not reject challenge"),
  });

  if (isLoading) return <SkeletonCard />;
  if (!team) return <EmptyState icon={Users2} title="Team not found" />;

  const theme = getSportTheme(team.sport);
  const Icon = theme.icon;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${theme.light}`}>
          <Icon size={22} strokeWidth={2.25} />
        </span>
        <div className="min-w-0">
          <h1 className="text-xl font-bold truncate">{team.team_name}</h1>
          <p className="text-ink-muted text-sm flex items-center gap-2 flex-wrap">
            <span>{sportLabel(team.sport)}</span>
            <span>·</span>
            <span>
              {team.wins}W-{team.losses}L
            </span>
            <span className="inline-flex items-center gap-1 text-amber-600 font-semibold">
              <Star size={12} strokeWidth={2.5} fill="currentColor" />
              {team.rating}
            </span>
          </p>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Card className="space-y-3">
        <p className="text-sm font-semibold">Members ({team.total_members})</p>
        <div className="space-y-2">
          {team.members.map((m) => (
            <div key={m.uid} className="flex items-center justify-between">
              <Link href={`/players/${m.uid}`} className="flex items-center gap-2.5 min-w-0 hover:opacity-80">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-muted text-xs font-bold text-ink-muted">
                  {(m.display_name || m.uid).charAt(0).toUpperCase()}
                </span>
                <span className="text-sm truncate">
                  {m.display_name || m.uid}
                  {m.uid === team.captain_uid && (
                    <span className="ml-1.5 text-xs font-semibold text-indigo-600">(captain)</span>
                  )}
                </span>
              </Link>
              {(isCaptain || m.uid === session.uid) && m.uid !== team.captain_uid && (
                <button
                  onClick={() => removeMutation.mutate(m.uid)}
                  className="text-xs font-medium text-red-600 hover:underline shrink-0"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>

        {isCaptain && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              inviteMutation.mutate();
            }}
            className="flex gap-2 pt-2 border-t border-border"
          >
            <input
              placeholder="Player uid"
              value={inviteUid}
              onChange={(e) => setInviteUid(e.target.value)}
              required
              className="flex-1 rounded-full border border-border bg-surface px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              placeholder="Name"
              value={inviteName}
              onChange={(e) => setInviteName(e.target.value)}
              required
              className="w-24 rounded-full border border-border bg-surface px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <Button
              type="submit"
              variant="gradient"
              pill
              disabled={inviteMutation.isPending}
              className="text-xs px-4 py-2 shrink-0 flex items-center gap-1"
            >
              <UserPlus size={13} strokeWidth={2.5} />
              Invite
            </Button>
          </form>
        )}
      </Card>

      <Card className="space-y-3">
        <p className="text-sm font-semibold">Looking for opponent</p>

        {isCaptain && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createChallengeMutation.mutate();
            }}
            className="grid grid-cols-3 gap-2"
          >
            <input
              type="date"
              value={challengeDate}
              onChange={(e) => setChallengeDate(e.target.value)}
              required
              className="rounded-full border border-border bg-surface px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              type="time"
              value={challengeTime}
              onChange={(e) => setChallengeTime(e.target.value)}
              required
              className="rounded-full border border-border bg-surface px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              type="number"
              value={numPlayers}
              onChange={(e) => setNumPlayers(e.target.value)}
              className="rounded-full border border-border bg-surface px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <Button
              type="submit"
              variant="gradient"
              pill
              disabled={createChallengeMutation.isPending}
              className="col-span-3 text-xs flex items-center justify-center gap-1.5"
            >
              <Swords size={13} strokeWidth={2.5} />
              Post challenge
            </Button>
          </form>
        )}

        <div className="space-y-2">
          {challenges?.map((c) => (
            <div key={c.challenge_id} className="flex items-center justify-between text-sm rounded-xl bg-surface-muted/60 px-3 py-2.5">
              <span className="text-foreground">
                {c.date} {c.time} · {c.number_of_players} players
              </span>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant={CHALLENGE_BADGE_VARIANT[c.status] ?? "neutral"}>{c.status}</Badge>
                {isCaptain && c.status === "pending" && c.from_team_id !== teamId && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => acceptMutation.mutate(c.challenge_id)}
                      className="text-xs font-medium text-emerald-600 hover:underline"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => rejectMutation.mutate(c.challenge_id)}
                      className="text-xs font-medium text-red-600 hover:underline"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {challenges && challenges.length === 0 && (
            <EmptyState icon={Swords} title="No opponent challenges yet" description="Post one above to find a match." />
          )}
        </div>
      </Card>
    </div>
  );
}
