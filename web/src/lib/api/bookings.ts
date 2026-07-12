import { apiFetch } from "./client";
import type { BookingResponse, MatchCompletionResponse, SlotResponse } from "@/lib/types";

export function getSlots(tenantId: string, courtId: string, date: string, granularity = 60) {
  return apiFetch<SlotResponse[]>(
    `/venues/${tenantId}/courts/${courtId}/slots?date=${date}&granularity=${granularity}`
  );
}

export interface CreateBookingPayload {
  court_id: string;
  date: string;
  start_time: string;
  end_time: string;
  team_name?: string;
}

export function createBooking(tenantId: string, payload: CreateBookingPayload) {
  return apiFetch<BookingResponse>(`/venues/${tenantId}/bookings`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listMyBookings() {
  return apiFetch<BookingResponse[]>(`/players/me/bookings`);
}

export function getMyBooking(bookingId: string) {
  return listMyBookings().then((bookings) => {
    const booking = bookings.find((b) => b.booking_id === bookingId);
    if (!booking) throw new Error("Booking not found");
    return booking;
  });
}

export function cancelBooking(tenantId: string, bookingId: string) {
  return apiFetch<BookingResponse>(`/venues/${tenantId}/bookings/${bookingId}/cancel`, {
    method: "PATCH",
  });
}

export function confirmBooking(tenantId: string, bookingId: string) {
  return apiFetch<BookingResponse>(`/venues/${tenantId}/bookings/${bookingId}/confirm`, {
    method: "PATCH",
  });
}

export interface RescheduleBookingPayload {
  date: string;
  start_time: string;
  end_time: string;
  court_id?: string;
}

export function rescheduleBooking(tenantId: string, bookingId: string, payload: RescheduleBookingPayload) {
  return apiFetch<BookingResponse>(`/venues/${tenantId}/bookings/${bookingId}/reschedule`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function openToCommunity(tenantId: string, bookingId: string, slotsOpen: number) {
  return apiFetch<BookingResponse>(`/venues/${tenantId}/bookings/${bookingId}/open-to-community`, {
    method: "PATCH",
    body: JSON.stringify({ slots_open: slotsOpen }),
  });
}

export function listVenueBookings(tenantId: string, date?: string) {
  const suffix = date ? `?date=${date}` : "";
  return apiFetch<BookingResponse[]>(`/venues/${tenantId}/bookings${suffix}`);
}

export function checkinPlayer(tenantId: string, bookingId: string, playerUid: string) {
  return apiFetch<{ success: boolean; message: string; booking_id: string }>(
    `/venues/${tenantId}/bookings/${bookingId}/checkin`,
    { method: "POST", body: JSON.stringify({ player_uid: playerUid }) }
  );
}

export function completeMatch(tenantId: string, bookingId: string) {
  return apiFetch<MatchCompletionResponse>(`/venues/${tenantId}/bookings/${bookingId}/complete`, {
    method: "POST",
  });
}

export function getCheckins(tenantId: string, bookingId: string) {
  return apiFetch<{ booking_id: string; checked_in_count: number; checked_in_players: string[] }>(
    `/venues/${tenantId}/bookings/${bookingId}/checkins`
  );
}
