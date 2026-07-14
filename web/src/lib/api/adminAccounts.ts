import { apiFetch } from "./client";
import type { AdminAccountResponse, AdminPasswordResetResponse, MeResponse } from "@/lib/types";

export function listAdminAccounts() {
  return apiFetch<AdminAccountResponse[]>(`/admin/accounts`);
}

export interface CreateAdminAccountPayload {
  email: string;
  password: string;
  display_name: string;
  phone: string;
}

export function createAdminAccount(payload: CreateAdminAccountPayload) {
  return apiFetch<MeResponse>(`/admin/accounts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resetAdminPassword(uid: string) {
  return apiFetch<AdminPasswordResetResponse>(`/admin/accounts/${uid}/reset-password`, {
    method: "POST",
  });
}
