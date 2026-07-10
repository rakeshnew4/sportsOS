import { apiFetch } from "./client";
import type { JoinWaitlistResponse, MyWaitlistPosition } from "@/lib/types";

export function joinWaitlist(tenantId: string, bookingId: string) {
  return apiFetch<JoinWaitlistResponse>(`/venues/${tenantId}/bookings/${bookingId}/waitlist`, {
    method: "POST",
  });
}

export function getMyWaitlistPosition(bookingId: string) {
  return apiFetch<MyWaitlistPosition>(`/players/me/waitlist/${bookingId}`);
}

export function confirmWaitlistPromotion(bookingId: string) {
  return apiFetch<{ success: boolean; message: string }>(`/players/me/waitlist/${bookingId}/confirm`, {
    method: "POST",
  });
}

export function declineWaitlistPromotion(bookingId: string) {
  return apiFetch<{ success: boolean; message: string }>(`/players/me/waitlist/${bookingId}/decline`, {
    method: "POST",
  });
}

export function leaveWaitlist(bookingId: string) {
  return apiFetch<{ success: boolean; message: string }>(`/players/me/waitlist/${bookingId}`, {
    method: "DELETE",
  });
}
