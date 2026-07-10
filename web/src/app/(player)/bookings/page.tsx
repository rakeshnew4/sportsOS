"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listMyBookings } from "@/lib/api/bookings";
import { queryKeys } from "@/lib/queryKeys";
import type { BookingStatus } from "@/lib/types";

const STATUS_STYLES: Record<BookingStatus, string> = {
  confirmed: "bg-emerald-50 text-emerald-700",
  pending_payment: "bg-amber-50 text-amber-700",
  completed: "bg-neutral-100 text-neutral-600",
  cancelled: "bg-red-50 text-red-600",
};

export default function BookingsPage() {
  const { data: bookings, isLoading } = useQuery({
    queryKey: queryKeys.myBookings(),
    queryFn: listMyBookings,
  });

  const sorted = bookings?.slice().sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">My bookings</h1>
        <p className="text-neutral-500 text-sm">Courts you've booked.</p>
      </div>

      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
      {sorted && sorted.length === 0 && (
        <p className="text-sm text-neutral-500">No bookings yet — go book a court.</p>
      )}

      <div className="space-y-3">
        {sorted?.map((booking) => (
          <Link
            key={booking.booking_id}
            href={`/bookings/${booking.booking_id}`}
            className="block rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm hover:border-neutral-300"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-neutral-900">{booking.sport.replace("_", " ")}</p>
                <p className="text-sm text-neutral-500">
                  {booking.date} · {booking.start_time} – {booking.end_time}
                </p>
                {booking.team_name && (
                  <p className="text-xs text-neutral-400 mt-1">{booking.team_name}</p>
                )}
              </div>
              <span
                className={`text-xs font-medium rounded-full px-2 py-1 ${STATUS_STYLES[booking.status]}`}
              >
                {booking.status.replace("_", " ")}
              </span>
            </div>
            <p className="text-sm font-medium text-neutral-700 mt-2">₹{booking.price}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
