import { apiFetch } from "./client";
import type { WalletResponse, WalletTransactionResponse } from "@/lib/types";

export function getWallet() {
  return apiFetch<WalletResponse>(`/wallet/me`);
}

export function getWalletTransactions() {
  return apiFetch<WalletTransactionResponse[]>(`/wallet/me/transactions`);
}

export function topupWallet(amount: number) {
  return apiFetch<WalletResponse>(`/wallet/me/topup`, {
    method: "POST",
    body: JSON.stringify({ amount, reason: "User topup" }),
  });
}
