"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Calendar, Clock, MapPin, Star, Trophy } from "lucide-react";
import { getPlayerProfile, updateMySkills } from "@/lib/api/players";
import { listPlayerReviews } from "@/lib/api/ratings";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { StatTile } from "@/components/ui/StatTile";
import { ApiError } from "@/lib/api/client";
import { ALL_SPORTS, getSportTheme, sportLabel } from "@/lib/sportTheme";
import type { SkillLevel } from "@/lib/types";

const SKILL_LEVELS: SkillLevel[] = ["beginner", "intermediate", "advanced", "pro"];

export default function PlayerProfilePage({ params }: { params: Promise<{ uid: string }> }) {
  const { uid } = use(params);
  const session = useSession();
  const isOwnProfile = uid === session.uid;

  const { data: profile, isLoading } = useQuery({
    queryKey: queryKeys.playerProfile(uid),
    queryFn: () => getPlayerProfile(uid),
  });

  const { data: reviews } = useQuery({
    queryKey: queryKeys.playerReviews(uid),
    queryFn: () => listPlayerReviews(uid),
  });

  if (isLoading) return <FootballSpinner />;
  if (!profile) return <EmptyState icon={Trophy} title="Player not found" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-from to-brand-to text-white text-xl font-bold">
          {(profile.display_name || "?").charAt(0).toUpperCase()}
        </span>
        <div className="min-w-0">
          <h1 className="text-xl font-bold truncate flex items-center gap-2">
            {profile.display_name || "Player"}
            {isOwnProfile && (
              <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 rounded-full px-2 py-0.5">
                You
              </span>
            )}
          </h1>
          <div className="flex items-center gap-1 text-sm text-ink-muted mt-0.5">
            {profile.total_ratings > 0 ? (
              <>
                <Star size={13} strokeWidth={2.5} className="fill-amber-400 text-amber-400" />
                <span className="font-semibold text-foreground">{profile.avg_rating}</span>
                <span>({profile.total_ratings} rating{profile.total_ratings === 1 ? "" : "s"})</span>
              </>
            ) : (
              <span>No ratings yet</span>
            )}
          </div>
        </div>
      </div>

      <Card>
        <div className="grid grid-cols-4 gap-2">
          <StatTile icon={Calendar} label="Bookings" value={profile.total_bookings} />
          <StatTile icon={Trophy} label="Matches" value={profile.total_matches_played} accent="text-teal-600 bg-teal-50" />
          <StatTile icon={Clock} label="Hours" value={profile.total_hours_played} accent="text-amber-600 bg-amber-50" />
          <StatTile icon={MapPin} label="Venues" value={profile.repeat_venues_count} accent="text-emerald-600 bg-emerald-50" />
        </div>
        {profile.favorite_sport && (
          <p className="text-xs text-ink-muted mt-3 text-center">
            Favorite sport: <span className="font-medium text-foreground">{sportLabel(profile.favorite_sport)}</span>
          </p>
        )}
      </Card>

      <SkillLevelsCard uid={uid} skillLevels={profile.skill_levels} editable={isOwnProfile} />

      <div>
        <p className="text-sm font-semibold mb-2">Reviews</p>
        <div className="space-y-2">
          {reviews?.map((r) => (
            <Card key={r.rating_id}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <Star
                      key={n}
                      size={13}
                      strokeWidth={2.5}
                      className={n <= r.rating ? "fill-amber-400 text-amber-400" : "text-ink-muted/30"}
                    />
                  ))}
                </div>
                <p className="text-xs text-ink-muted">{new Date(r.created_at).toLocaleDateString()}</p>
              </div>
              {r.comment && <p className="text-sm text-ink-muted mt-1.5">{r.comment}</p>}
            </Card>
          ))}
          {reviews && reviews.length === 0 && (
            <EmptyState icon={Star} title="No reviews yet" description="Reviews appear here after completed matches." />
          )}
        </div>
      </div>
    </div>
  );
}

function SkillLevelsCard({
  uid,
  skillLevels,
  editable,
}: {
  uid: string;
  skillLevels: Record<string, SkillLevel>;
  editable: boolean;
}) {
  const queryClient = useQueryClient();
  const [sport, setSport] = useState("");
  const [level, setLevel] = useState<SkillLevel>("intermediate");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => updateMySkills({ ...skillLevels, [sport]: level }),
    onSuccess: () => {
      setError(null);
      setSport("");
      queryClient.invalidateQueries({ queryKey: queryKeys.playerProfile(uid) });
      queryClient.invalidateQueries({ queryKey: queryKeys.myProfile() });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not update skill level"),
  });

  const entries = Object.entries(skillLevels);

  return (
    <Card className="space-y-3">
      <p className="text-sm font-semibold">Skill levels</p>
      {entries.length === 0 && !editable && <p className="text-sm text-ink-muted">No skill levels set.</p>}
      <div className="flex flex-wrap gap-2">
        {entries.map(([s, lvl]) => {
          const theme = getSportTheme(s);
          return (
            <span
              key={s}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold ${theme.light}`}
            >
              {sportLabel(s)}
              <span className="capitalize opacity-70">· {lvl}</span>
            </span>
          );
        })}
      </div>

      {editable && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!sport) return;
            mutation.mutate();
          }}
          className="space-y-2 pt-1 border-t border-border"
        >
          <select
            value={sport}
            onChange={(e) => setSport(e.target.value)}
            className="w-full rounded-full border border-border bg-surface px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Add a sport…</option>
            {ALL_SPORTS.map((s) => (
              <option key={s} value={s}>
                {sportLabel(s)}
              </option>
            ))}
          </select>
          <div className="flex gap-1.5">
            {SKILL_LEVELS.map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLevel(l)}
                className={`flex-1 rounded-full py-1.5 text-xs font-semibold capitalize transition-colors ${
                  level === l
                    ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                    : "bg-surface-muted text-ink-muted"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <Button
            type="submit"
            variant="gradient"
            pill
            disabled={!sport || mutation.isPending}
            className="w-full text-xs"
          >
            {mutation.isPending ? "Saving…" : "Save skill level"}
          </Button>
        </form>
      )}
    </Card>
  );
}
