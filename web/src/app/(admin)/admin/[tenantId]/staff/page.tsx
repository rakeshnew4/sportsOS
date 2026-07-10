"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { addStaff, listStaff, removeStaff } from "@/lib/api/staff";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

export default function StaffPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const session = useSession();
  const isOwner = session.owner_of.includes(tenantId);
  const queryClient = useQueryClient();
  const [uid, setUid] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: staff, isLoading } = useQuery({
    queryKey: queryKeys.staff(tenantId),
    queryFn: () => listStaff(tenantId),
  });

  const addMutation = useMutation({
    mutationFn: () => addStaff(tenantId, uid),
    onSuccess: () => {
      setError(null);
      setUid("");
      queryClient.invalidateQueries({ queryKey: queryKeys.staff(tenantId) });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not add staff member"),
  });

  const removeMutation = useMutation({
    mutationFn: (staffUid: string) => removeStaff(tenantId, staffUid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.staff(tenantId) }),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not remove staff member"),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Staff</h1>

      {isOwner && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            addMutation.mutate();
          }}
          className="flex gap-2"
        >
          <input
            placeholder="Player uid"
            value={uid}
            onChange={(e) => setUid(e.target.value)}
            required
            className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <Button type="submit" disabled={addMutation.isPending}>
            {addMutation.isPending ? "Adding…" : "Add"}
          </Button>
        </form>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}

      <div className="space-y-2">
        {staff?.map((member) => (
          <div
            key={member.uid}
            className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-neutral-900">{member.display_name || member.uid}</p>
              <p className="text-xs text-neutral-400 capitalize">{member.role}</p>
            </div>
            {isOwner && (
              <Button
                variant="ghost"
                onClick={() => removeMutation.mutate(member.uid)}
                disabled={removeMutation.isPending}
                className="text-red-600"
              >
                Remove
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
