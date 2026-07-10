"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createTeam, listMyTeams, listTeams } from "@/lib/api/teams";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

export default function TeamsPage() {
  const queryClient = useQueryClient();
  const [sportFilter, setSportFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [teamName, setTeamName] = useState("");
  const [sport, setSport] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: myTeams } = useQuery({ queryKey: queryKeys.myTeams(), queryFn: listMyTeams });
  const { data: allTeams, isLoading } = useQuery({
    queryKey: queryKeys.teams(sportFilter || undefined),
    queryFn: () => listTeams(sportFilter || undefined),
  });

  const createMutation = useMutation({
    mutationFn: () => createTeam({ team_name: teamName, sport }),
    onSuccess: () => {
      setError(null);
      setTeamName("");
      setSport("");
      setShowCreate(false);
      queryClient.invalidateQueries({ queryKey: queryKeys.myTeams() });
      queryClient.invalidateQueries({ queryKey: ["teams"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create team"),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Teams</h1>
          <p className="text-neutral-500 text-sm">Your squads and teams to challenge.</p>
        </div>
        <Button variant="secondary" onClick={() => setShowCreate((s) => !s)}>
          {showCreate ? "Cancel" : "+ New team"}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate();
          }}
          className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3"
        >
          <input
            placeholder="Team name"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <input
            placeholder="Sport"
            value={sport}
            onChange={(e) => setSport(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <Button type="submit" disabled={createMutation.isPending} className="w-full">
            {createMutation.isPending ? "Creating…" : "Create team"}
          </Button>
        </form>
      )}

      <div>
        <p className="text-sm font-semibold text-neutral-700 mb-2">My teams</p>
        <div className="space-y-2">
          {myTeams?.map((team) => (
            <Link
              key={team.team_id}
              href={`/teams/${team.team_id}`}
              className="block rounded-xl border border-neutral-200 bg-white px-4 py-3 hover:border-neutral-300"
            >
              <p className="text-sm font-medium text-neutral-900">{team.team_name}</p>
              <p className="text-xs text-neutral-400">
                {team.sport.replace("_", " ")} · {team.total_members} members · {team.wins}W-{team.losses}L
              </p>
            </Link>
          ))}
          {myTeams && myTeams.length === 0 && (
            <p className="text-sm text-neutral-500">You're not on a team yet.</p>
          )}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold text-neutral-700">Browse teams</p>
          <input
            placeholder="Filter by sport"
            value={sportFilter}
            onChange={(e) => setSportFilter(e.target.value)}
            className="w-40 rounded-lg border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
        <div className="space-y-2">
          {allTeams?.map((team) => (
            <Link
              key={team.team_id}
              href={`/teams/${team.team_id}`}
              className="block rounded-xl border border-neutral-200 bg-white px-4 py-3 hover:border-neutral-300"
            >
              <p className="text-sm font-medium text-neutral-900">{team.team_name}</p>
              <p className="text-xs text-neutral-400">
                {team.sport.replace("_", " ")} · captain {team.captain_name} · rating {team.rating}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
