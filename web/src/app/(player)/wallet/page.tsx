"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getWallet, getWalletTransactions, topupWallet } from "@/lib/api/wallet";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

export default function WalletPage() {
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: wallet } = useQuery({ queryKey: queryKeys.wallet(), queryFn: getWallet });
  const { data: transactions, isLoading } = useQuery({
    queryKey: queryKeys.walletTransactions(),
    queryFn: getWalletTransactions,
  });

  const topupMutation = useMutation({
    mutationFn: (value: number) => topupWallet(value),
    onSuccess: () => {
      setAmount("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.wallet() });
      queryClient.invalidateQueries({ queryKey: queryKeys.walletTransactions() });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Top-up failed");
    },
  });

  function handleTopup(e: React.FormEvent) {
    e.preventDefault();
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("Enter a valid amount");
      return;
    }
    topupMutation.mutate(value);
  }

  const sorted = transactions?.slice().sort((a, b) => (a.created_at < b.created_at ? 1 : -1));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Wallet</h1>
        <p className="text-neutral-500 text-sm">Balance and transaction history.</p>
      </div>

      <div className="rounded-2xl bg-emerald-600 text-white p-5">
        <p className="text-sm opacity-80">Balance</p>
        <p className="text-3xl font-bold">₹{wallet?.balance ?? "—"}</p>
      </div>

      <form onSubmit={handleTopup} className="flex gap-2">
        <input
          type="number"
          min="1"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <Button type="submit" disabled={topupMutation.isPending}>
          {topupMutation.isPending ? "Adding…" : "Top up"}
        </Button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div>
        <p className="text-sm font-semibold text-neutral-700 mb-2">Transactions</p>
        {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
        {sorted && sorted.length === 0 && (
          <p className="text-sm text-neutral-500">No transactions yet.</p>
        )}
        <div className="space-y-2">
          {sorted?.map((tx) => (
            <div
              key={tx.tx_id}
              className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-neutral-900">{tx.reason}</p>
                <p className="text-xs text-neutral-400">{new Date(tx.created_at).toLocaleString()}</p>
              </div>
              <p
                className={`text-sm font-semibold ${
                  tx.type === "credit" ? "text-emerald-600" : "text-red-600"
                }`}
              >
                {tx.type === "credit" ? "+" : "−"}₹{tx.amount}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
