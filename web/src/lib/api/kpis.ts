import { apiFetch } from "./client";
import type { PlayerEngagementKPI, VenueKPIScope, VenueOverviewKPI } from "@/lib/types";

export function getPlayerEngagement(uid: string, scope: "month" | "quarter" | "year" | "all_time" = "month") {
  return apiFetch<PlayerEngagementKPI>(`/kpis/players/${uid}/engagement?scope=${scope}`);
}

export function getVenueOverview(tenantId: string, scope: VenueKPIScope = "today") {
  return apiFetch<VenueOverviewKPI>(`/kpis/venues/${tenantId}/overview?scope=${scope}`);
}
