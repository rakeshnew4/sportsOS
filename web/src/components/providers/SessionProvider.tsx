"use client";

import { createContext, useContext, useEffect } from "react";
import { signInWithCustomToken } from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";
import { apiFetch } from "@/lib/api/client";
import type { MeResponse } from "@/lib/types";

const SessionContext = createContext<MeResponse | null>(null);

export function SessionProvider({
  session,
  children,
}: {
  session: MeResponse;
  children: React.ReactNode;
}) {
  // Best-effort Firebase sign-in so Firestore listeners (live match/slot state)
  // can authenticate as this uid. If Firebase isn't configured yet or the
  // request fails, realtime features simply stay off — nothing else depends on this.
  useEffect(() => {
    const auth = getFirebaseAuth();
    if (!auth) return;
    apiFetch<{ token: string }>("/realtime/token")
      .then(({ token }) => signInWithCustomToken(auth, token))
      .catch(() => {});
  }, [session.uid]);

  return <SessionContext.Provider value={session}>{children}</SessionContext.Provider>;
}

export function useSession(): MeResponse {
  const session = useContext(SessionContext);
  if (!session) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return session;
}
