"use client";

import { useEffect } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { useQueryClient } from "@tanstack/react-query";
import { getFirebaseDb } from "@/lib/firebase";
import { queryKeys } from "@/lib/queryKeys";
import type { BookingResponse, ParticipantResponse } from "@/lib/types";

interface MatchDoc {
  status?: string;
  is_joinable?: boolean;
  slots_total?: number;
  slots_open?: number;
  participants?: { uid: string; display_name: string | null }[];
}

/** Subscribes to live Join Match state (participants joining, slot count) for a
 * booking and patches it straight into the existing React Query caches — the
 * REST queries remain the initial load, this hook only pushes updates. */
export function useMatchLive(tenantId: string | undefined, bookingId: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const db = getFirebaseDb();
    if (!db || !tenantId) return;

    const unsubscribe = onSnapshot(doc(db, "matches", bookingId), (snapshot) => {
      const data = snapshot.data() as MatchDoc | undefined;
      if (!data) return;

      queryClient.setQueryData<BookingResponse | undefined>(
        [...queryKeys.myBookings(), bookingId],
        (old) =>
          old
            ? {
                ...old,
                status: (data.status as BookingResponse["status"]) ?? old.status,
                is_joinable: data.is_joinable ?? old.is_joinable,
                slots_total: data.slots_total ?? old.slots_total,
                slots_open: data.slots_open ?? old.slots_open,
              }
            : old
      );

      if (data.participants) {
        queryClient.setQueryData<ParticipantResponse[] | undefined>(
          queryKeys.matchParticipants(tenantId, bookingId),
          (old) =>
            data.participants!.map((p) => ({
              uid: p.uid,
              display_name: p.display_name,
              joined_at: old?.find((existing) => existing.uid === p.uid)?.joined_at ?? new Date().toISOString(),
            }))
        );
      }
    });

    return () => unsubscribe();
  }, [tenantId, bookingId, queryClient]);
}
