"use client";

import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getVenueOverview } from "@/lib/api/kpis";
import { queryKeys } from "@/lib/queryKeys";
import type { VenueKPIScope } from "@/lib/types";

const SCOPES: VenueKPIScope[] = ["today", "week", "month"];

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-3">
      <p className="text-xs text-neutral-500">{label}</p>
      <p className="text-lg font-semibold text-neutral-900">{value}</p>
    </div>
  );
}

export default function VenueOverviewPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const [scope, setScope] = useState<VenueKPIScope>("today");

  const { data: kpi, isLoading } = useQuery({
    queryKey: queryKeys.venueOverview(tenantId, scope),
    queryFn: () => getVenueOverview(tenantId, scope),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{kpi?.venue_name ?? "Overview"}</h1>
        <div className="flex gap-1 rounded-lg bg-neutral-100 p-1">
          {SCOPES.map((s) => (
            <button
              key={s}
              onClick={() => setScope(s)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize ${
                scope === s ? "bg-white shadow-sm text-neutral-900" : "text-neutral-500"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}

      {kpi && (
        <div className="space-y-4">
          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Revenue</p>
            <div className="grid grid-cols-2 gap-2">
              <StatCard label="Total revenue" value={`₹${kpi.revenue.total_revenue}`} />
              <StatCard label="Transactions" value={kpi.revenue.transaction_count} />
              <StatCard label="Avg transaction" value={`₹${kpi.revenue.avg_transaction_value}`} />
              <StatCard label="Avg occupancy" value={`${kpi.avg_occupancy_percent}%`} />
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Court occupancy</p>
            <div className="space-y-2">
              {kpi.occupancy.map((o) => (
                <div
                  key={o.court_id}
                  className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-neutral-900">{o.court_name}</p>
                    <p className="text-xs text-neutral-400">
                      {o.bookings_count} bookings · {o.no_show_count} no-shows · {o.cancelled_count} cancelled
                    </p>
                  </div>
                  <p className="text-sm font-semibold text-neutral-700">{o.utilization_percent}%</p>
                </div>
              ))}
              {kpi.occupancy.length === 0 && (
                <p className="text-sm text-neutral-500">No court activity in this period.</p>
              )}
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Customers</p>
            <div className="grid grid-cols-2 gap-2">
              <StatCard label="Active" value={kpi.customers.active_customers} />
              <StatCard label="New" value={kpi.customers.new_customers} />
              <StatCard label="Returning" value={kpi.customers.returning_customers} />
              <StatCard label="Repeat rate" value={`${kpi.customers.repeat_booking_percent}%`} />
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Teams & matchmaking</p>
            <div className="grid grid-cols-2 gap-2">
              <StatCard label="Teams formed" value={kpi.teams.teams_formed} />
              <StatCard label="Queue → matches" value={kpi.matchmaking.matches_formed} />
              <StatCard label="Match fill rate" value={`${kpi.matchmaking.match_fill_rate}%`} />
              <StatCard label="Queue cancellations" value={kpi.matchmaking.queue_cancellations} />
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Match completion</p>
            <div className="grid grid-cols-2 gap-2">
              <StatCard label="Completed" value={kpi.match_completion.matches_completed} />
              <StatCard label="Completion rate" value={`${kpi.match_completion.completion_rate}%`} />
              <StatCard label="No-show rate" value={`${kpi.match_completion.no_show_rate}%`} />
              <StatCard label="Disputes" value={kpi.match_completion.matches_with_disputes} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
