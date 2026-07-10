import { apiFetch } from "./client";
import type { CourtResponse, VenueResponse } from "@/lib/types";

export function listVenues(params?: { city?: string; sport?: string }) {
  const qs = new URLSearchParams();
  if (params?.city) qs.set("city", params.city);
  if (params?.sport) qs.set("sport", params.sport);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<VenueResponse[]>(`/venues${suffix}`);
}

export function getVenue(tenantId: string) {
  return apiFetch<VenueResponse>(`/venues/${tenantId}`);
}

export function listCourts(tenantId: string) {
  return apiFetch<CourtResponse[]>(`/venues/${tenantId}/courts`);
}

export function getCourt(tenantId: string, courtId: string) {
  return apiFetch<CourtResponse>(`/venues/${tenantId}/courts/${courtId}`);
}

export interface CreateVenuePayload {
  name: string;
  city: string;
  geo: { lat: number; lng: number };
  sports: string[];
}

export function createVenue(payload: CreateVenuePayload) {
  return apiFetch<VenueResponse>(`/venues`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface CreateCourtPayload {
  name: string;
  sport: string;
  hourly_price: number;
  open_time: string;
  close_time: string;
  dynamic_pricing_enabled?: boolean;
}

export function createCourt(tenantId: string, payload: CreateCourtPayload) {
  return apiFetch<CourtResponse>(`/venues/${tenantId}/courts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface UpdateCourtPayload {
  name?: string;
  hourly_price?: number;
  open_time?: string;
  close_time?: string;
  is_active?: boolean;
}

export function updateCourt(tenantId: string, courtId: string, payload: UpdateCourtPayload) {
  return apiFetch<CourtResponse>(`/venues/${tenantId}/courts/${courtId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
