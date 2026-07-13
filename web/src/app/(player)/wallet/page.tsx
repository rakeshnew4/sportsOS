"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDownLeft, ArrowUpRight, Receipt, Wallet as WalletIcon } from "lucide-react";
import { getWallet, getWalletTransactions, topupWallet } from "@/lib/api/wallet";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
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
        <p className="text-ink-muted text-sm">Balance and transaction history.</p>
      </div>

      <div className="rounded-3xl bg-gradient-to-br from-brand-from to-brand-to p-6 text-white shadow-lg shadow-indigo-600/20">
        <div className="flex items-center gap-2 opacity-80 mb-1">
          <WalletIcon size={15} strokeWidth={2.25} />
          <p className="text-sm">Balance</p>
        </div>
        <p className="text-3xl font-bold">
          {wallet ? `₹${wallet.balance}` : <span className="inline-block h-8 w-24 rounded-lg bg-white/20 animate-pulse" />}
        </p>
      </div>

      <Card>
        <form onSubmit={handleTopup} className="flex gap-2">
          <input
            type="number"
            min="1"
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="flex-1 rounded-full border border-border bg-surface px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <Button type="submit" variant="gradient" pill disabled={topupMutation.isPending} className="px-6">
            {topupMutation.isPending ? "Adding…" : "Top up"}
          </Button>
        </form>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </Card>

      <div>
        <p className="text-sm font-semibold mb-2">Transactions</p>
        {isLoading && <FootballSpinner />}
        {sorted && sorted.length === 0 && (
          <EmptyState icon={Receipt} title="No transactions yet" description="Top up your wallet to get started." />
        )}
        <div className="space-y-2">
          {sorted?.map((tx) => {
            const isCredit = tx.type === "credit";
            return (
              <Card key={tx.tx_id}>
                <div className="flex items-center gap-3">
                  <span
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                      isCredit ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"
                    }`}
                  >
                    {isCredit ? (
                      <ArrowDownLeft size={16} strokeWidth={2.25} />
                    ) : (
                      <ArrowUpRight size={16} strokeWidth={2.25} />
                    )}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{tx.reason}</p>
                    <p className="text-xs text-ink-muted">{new Date(tx.created_at).toLocaleString()}</p>
                  </div>
                  <p className={`text-sm font-semibold shrink-0 ${isCredit ? "text-emerald-600" : "text-red-600"}`}>
                    {isCredit ? "+" : "−"}₹{tx.amount}
                  </p>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
