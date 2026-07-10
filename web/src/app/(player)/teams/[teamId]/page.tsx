"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

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

  if (isLoading) return <p className="text-sm text-neutral-500">Loading…</p>;
  if (!team) return <p className="text-sm text-neutral-500">Team not found.</p>;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">{team.team_name}</h1>
        <p className="text-neutral-500 text-sm">
          {team.sport.replace("_", " ")} · {team.wins}W-{team.losses}L · rating {team.rating}
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
        <p className="text-sm font-semibold text-neutral-700">Members ({team.total_members})</p>
        {team.members.map((m) => (
          <div key={m.uid} className="flex items-center justify-between text-sm">
            <span className="text-neutral-700">
              {m.display_name || m.uid} {m.uid === team.captain_uid && "(captain)"}
            </span>
            {(isCaptain || m.uid === session.uid) && m.uid !== team.captain_uid && (
              <button
                onClick={() => removeMutation.mutate(m.uid)}
                className="text-xs text-red-600 hover:underline"
              >
                Remove
              </button>
            )}
          </div>
        ))}

        {isCaptain && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              inviteMutation.mutate();
            }}
            className="flex gap-2 pt-2"
          >
            <input
              placeholder="Player uid"
              value={inviteUid}
              onChange={(e) => setInviteUid(e.target.value)}
              required
              className="flex-1 rounded-lg border border-neutral-300 px-2 py-1.5 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <input
              placeholder="Name"
              value={inviteName}
              onChange={(e) => setInviteName(e.target.value)}
              required
              className="w-24 rounded-lg border border-neutral-300 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <Button type="submit" disabled={inviteMutation.isPending} className="text-xs px-3 py-1.5">
              Invite
            </Button>
          </form>
        )}
      </div>

      <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3">
        <p className="text-sm font-semibold text-neutral-700">Looking for opponent</p>

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
              className="rounded-lg border border-neutral-300 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <input
              type="time"
              value={challengeTime}
              onChange={(e) => setChallengeTime(e.target.value)}
              required
              className="rounded-lg border border-neutral-300 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <input
              type="number"
              value={numPlayers}
              onChange={(e) => setNumPlayers(e.target.value)}
              className="rounded-lg border border-neutral-300 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <Button type="submit" disabled={createChallengeMutation.isPending} className="col-span-3 text-xs">
              Post challenge
            </Button>
          </form>
        )}

        <div className="space-y-2">
          {challenges?.map((c) => (
            <div key={c.challenge_id} className="flex items-center justify-between text-sm">
              <span className="text-neutral-700">
                {c.date} {c.time} · {c.number_of_players} players · {c.status}
              </span>
              {isCaptain && c.status === "pending" && c.from_team_id !== teamId && (
                <div className="flex gap-2">
                  <button
                    onClick={() => acceptMutation.mutate(c.challenge_id)}
                    className="text-xs text-emerald-600 hover:underline"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => rejectMutation.mutate(c.challenge_id)}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
          {challenges && challenges.length === 0 && (
            <p className="text-sm text-neutral-500">No opponent challenges yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
