"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createAdminAccount, listAdminAccounts, resetAdminPassword } from "@/lib/api/adminAccounts";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { ApiError } from "@/lib/api/client";

export default function SuperadminPage() {
  const session = useSession();
  const queryClient = useQueryClient();

  const { data: accounts, isLoading } = useQuery({
    queryKey: queryKeys.adminAccounts(),
    queryFn: listAdminAccounts,
    enabled: session.is_superadmin,
  });

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [lastCreated, setLastCreated] = useState<{ email: string; password: string } | null>(null);
  const [resetResult, setResetResult] = useState<{ email: string | null; password: string } | null>(null);

  const createMutation = useMutation({
    mutationFn: () => createAdminAccount({ display_name: displayName, email, phone, password }),
    onSuccess: () => {
      setLastCreated({ email, password });
      setDisplayName("");
      setEmail("");
      setPhone("");
      setPassword("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.adminAccounts() });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create account"),
  });

  const resetMutation = useMutation({
    mutationFn: (uid: string) => resetAdminPassword(uid),
    onSuccess: (data) => setResetResult({ email: data.email, password: data.new_password }),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not reset password"),
  });

  if (!session.is_superadmin) {
    return <p className="text-sm text-neutral-500">Superadmin access required.</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Admin accounts</h1>
        <p className="text-neutral-500 text-sm">
          Create login credentials for venue owners. Hand the email/password to them directly — there&apos;s no
          self-signup for admin accounts.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          createMutation.mutate();
        }}
        className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3"
      >
        <p className="text-sm font-semibold text-neutral-700">Create a venue owner account</p>
        <input
          placeholder="Display name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          placeholder="Phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          type="text"
          placeholder="Password (min 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending ? "Creating…" : "Create account"}
        </Button>
      </form>

      {lastCreated && (
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm">
          <p className="font-medium text-emerald-900">Account created — share these credentials with the owner:</p>
          <p className="font-mono text-emerald-800 mt-1">{lastCreated.email}</p>
          <p className="font-mono text-emerald-800">{lastCreated.password}</p>
        </div>
      )}
      {resetResult && (
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm">
          <p className="font-medium text-amber-900">Password reset — share the new password:</p>
          <p className="font-mono text-amber-800 mt-1">{resetResult.email}</p>
          <p className="font-mono text-amber-800">{resetResult.password}</p>
        </div>
      )}

      <div className="space-y-2">
        <p className="text-sm font-semibold text-neutral-700">Existing admin accounts</p>
        {isLoading && <FootballSpinner />}
        {accounts?.map((account) => (
          <div
            key={account.uid}
            className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white p-3"
          >
            <div>
              <p className="font-medium text-neutral-900">
                {account.display_name} {account.is_superadmin && <span className="text-xs text-indigo-600">(superadmin)</span>}
              </p>
              <p className="text-sm text-neutral-500">{account.email}</p>
              <p className="text-xs text-neutral-400">
                Owns {account.owner_of.length} venue{account.owner_of.length === 1 ? "" : "s"}
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => resetMutation.mutate(account.uid)}
              disabled={resetMutation.isPending}
            >
              Reset password
            </Button>
          </div>
        ))}
        {accounts?.length === 0 && <p className="text-sm text-neutral-500">No admin accounts yet.</p>}
      </div>
    </div>
  );
}
