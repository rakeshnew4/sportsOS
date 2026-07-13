"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronRight, Plus, Star, Users2 } from "lucide-react";
import { createTeam, listMyTeams, listTeams } from "@/lib/api/teams";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { SportFilterChips } from "@/components/ui/SportFilterChips";
import { ApiError } from "@/lib/api/client";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

export default function TeamsPage() {
  const queryClient = useQueryClient();
  const [sportFilter, setSportFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [teamName, setTeamName] = useState("");
  const [sport, setSport] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: myTeams, isLoading: myTeamsLoading } = useQuery({
    queryKey: queryKeys.myTeams(),
    queryFn: listMyTeams,
  });
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
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Teams</h1>
          <p className="text-ink-muted text-sm">Your squads and teams to challenge.</p>
        </div>
        <Button
          variant={showCreate ? "secondary" : "gradient"}
          pill
          onClick={() => setShowCreate((s) => !s)}
          className="shrink-0 flex items-center gap-1.5 text-sm px-4"
        >
          {showCreate ? (
            "Cancel"
          ) : (
            <>
              <Plus size={15} strokeWidth={2.5} />
              New team
            </>
          )}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate();
          }}
          className="rounded-2xl border border-border bg-surface shadow-sm p-4 space-y-3"
        >
          <input
            placeholder="Team name"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            required
            className="w-full rounded-full border border-border bg-surface px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <div>
            <p className="text-xs font-semibold text-ink-muted mb-2">Sport</p>
            <SportFilterChips value={sport} onChange={setSport} allowAll={false} />
          </div>
          <Button
            type="submit"
            variant="gradient"
            pill
            disabled={createMutation.isPending || !teamName || !sport}
            className="w-full"
          >
            {createMutation.isPending ? "Creating…" : "Create team"}
          </Button>
        </form>
      )}

      <div>
        <p className="text-sm font-semibold mb-2">My teams</p>
        {myTeamsLoading && <FootballSpinner />}
        {myTeams && myTeams.length === 0 && (
          <EmptyState icon={Users2} title="You're not on a team yet" description="Create one or browse teams below." />
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
          {myTeams?.map((team) => {
            const theme = getSportTheme(team.sport);
            const Icon = theme.icon;
            return (
              <Link key={team.team_id} href={`/teams/${team.team_id}`}>
                <Card interactive>
                  <div className="flex items-center gap-3">
                    <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${theme.light}`}>
                      <Icon size={19} strokeWidth={2.25} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold truncate">{team.team_name}</p>
                      <p className="text-xs text-ink-muted mt-0.5">
                        {sportLabel(team.sport)} · {team.total_members} members · {team.wins}W-{team.losses}L
                      </p>
                    </div>
                    <ChevronRight size={18} className="text-ink-muted shrink-0" />
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold mb-2">Browse teams</p>
        <SportFilterChips value={sportFilter} onChange={setSportFilter} />
        {isLoading && <FootballSpinner />}
        {allTeams && allTeams.length === 0 && (
          <div className="mt-3">
            <EmptyState icon={Users2} title="No teams found" description="Try a different sport." />
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3 mt-3">
          {allTeams?.map((team) => {
            const theme = getSportTheme(team.sport);
            const Icon = theme.icon;
            return (
              <Link key={team.team_id} href={`/teams/${team.team_id}`}>
                <Card interactive>
                  <div className="flex items-center gap-3">
                    <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${theme.light}`}>
                      <Icon size={19} strokeWidth={2.25} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold truncate">{team.team_name}</p>
                      <p className="text-xs text-ink-muted mt-0.5">
                        {sportLabel(team.sport)} · captain {team.captain_name}
                      </p>
                    </div>
                    <span className="shrink-0 flex items-center gap-1 text-xs font-semibold text-amber-600 bg-amber-50 rounded-full px-2.5 py-1">
                      <Star size={12} strokeWidth={2.5} fill="currentColor" />
                      {team.rating}
                    </span>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
