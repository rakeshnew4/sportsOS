import { apiFetch } from "./client";
import type { StaffMember } from "@/lib/types";

export function listStaff(tenantId: string) {
  return apiFetch<StaffMember[]>(`/venues/${tenantId}/staff`);
}

export function addStaff(tenantId: string, userUid: string, role: "staff" | "owner" = "staff") {
  return apiFetch<StaffMember>(`/venues/${tenantId}/staff`, {
    method: "POST",
    body: JSON.stringify({ user_uid: userUid, role }),
  });
}

export function removeStaff(tenantId: string, staffUid: string) {
  return apiFetch<{ success: boolean; message: string }>(`/venues/${tenantId}/staff/${staffUid}`, {
    method: "DELETE",
  });
}
