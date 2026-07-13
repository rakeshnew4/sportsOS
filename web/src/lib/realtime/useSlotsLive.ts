"use client";

import { useEffect, useRef } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { useQueryClient } from "@tanstack/react-query";
import { getFirebaseDb } from "@/lib/firebase";
import { queryKeys } from "@/lib/queryKeys";

/** Subscribes to live slot-booking changes for a court+date and refetches the
 * slots REST query when they happen, so a slot another user just booked (or
 * freed by cancelling) disappears/reappears without a manual refresh. Refetching
 * (rather than patching availability locally) keeps dynamic pricing correct. */
export function useSlotsLive(tenantId: string, courtId: string, date: string) {
  const queryClient = useQueryClient();
  const isFirstSnapshot = useRef(true);

  useEffect(() => {
    const db = getFirebaseDb();
    if (!db) return;

    isFirstSnapshot.current = true;
    const docId = `${tenantId}_${courtId}_${date}`;
    const unsubscribe = onSnapshot(doc(db, "slots", docId), () => {
      // The initial snapshot fires immediately with current state, which the
      // REST query already loaded — only refetch on actual subsequent changes.
      if (isFirstSnapshot.current) {
        isFirstSnapshot.current = false;
        return;
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.slots(tenantId, courtId, date) });
    });

    return () => unsubscribe();
  }, [tenantId, courtId, date, queryClient]);
}
