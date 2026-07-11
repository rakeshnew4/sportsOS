"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getVenueOverview } from "@/lib/api/kpis";
import { getVenue, updateVenue } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
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

function PaymentInfoCard({ tenantId }: { tenantId: string }) {
  const { data: venue } = useQuery({
    queryKey: queryKeys.venue(tenantId),
    queryFn: () => getVenue(tenantId),
  });

  if (!venue) return null;
  return <PaymentInfoForm key={`${venue.upi_id ?? ""}-${venue.booking_phone ?? ""}`} tenantId={tenantId} venue={venue} />;
}

function PaymentInfoForm({
  tenantId,
  venue,
}: {
  tenantId: string;
  venue: { upi_id: string | null; booking_phone: string | null };
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [upiId, setUpiId] = useState(venue.upi_id ?? "");
  const [bookingPhone, setBookingPhone] = useState(venue.booking_phone ?? "");

  const saveMutation = useMutation({
    mutationFn: () =>
      updateVenue(tenantId, { upi_id: upiId.trim() || undefined, booking_phone: bookingPhone.trim() || undefined }),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.venue(tenantId) });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not save"),
  });

  const dirty = venue && (upiId !== (venue.upi_id ?? "") || bookingPhone !== (venue.booking_phone ?? ""));
  const missing = venue && (!venue.upi_id || !venue.booking_phone);

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3">
      <div>
        <p className="text-sm font-semibold text-neutral-900">Payment info</p>
        <p className="text-xs text-neutral-500 mt-0.5">
          Players see this UPI ID and phone number to pay you directly for a booking.
        </p>
      </div>
      {missing && (
        <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
          Add both so players know how to pay you — bookings still work without it, but players won&apos;t
          know where to send payment.
        </p>
      )}
      <div className="grid grid-cols-2 gap-2">
        <input
          placeholder="UPI ID"
          value={upiId}
          onChange={(e) => setUpiId(e.target.value)}
          className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          placeholder="Booking phone"
          value={bookingPhone}
          onChange={(e) => setBookingPhone(e.target.value)}
          className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {dirty && (
        <Button
          variant="secondary"
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="text-xs px-3 py-1.5"
        >
          {saveMutation.isPending ? "Saving…" : "Save"}
        </Button>
      )}
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

      <PaymentInfoCard tenantId={tenantId} />

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
