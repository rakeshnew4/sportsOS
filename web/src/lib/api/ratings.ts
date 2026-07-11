import { apiFetch } from "./client";
import type { PlayerRatingsStats, RatingCreate, RatingResponse, VenueRatingsStats } from "@/lib/types";

export function createRating(payload: RatingCreate) {
  return apiFetch<RatingResponse>(`/ratings/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getPlayerRatingsStats(uid: string) {
  return apiFetch<PlayerRatingsStats>(`/ratings/players/${uid}/stats`);
}

export function listPlayerReviews(uid: string, limit = 10) {
  return apiFetch<RatingResponse[]>(`/ratings/players/${uid}/reviews?limit=${limit}`);
}

export function getVenueRatingsStats(tenantId: string) {
  return apiFetch<VenueRatingsStats>(`/ratings/venues/${tenantId}/stats`);
}
