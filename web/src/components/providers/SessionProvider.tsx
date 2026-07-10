"use client";

import { createContext, useContext } from "react";
import type { MeResponse } from "@/lib/types";

const SessionContext = createContext<MeResponse | null>(null);

export function SessionProvider({
  session,
  children,
}: {
  session: MeResponse;
  children: React.ReactNode;
}) {
  return <SessionContext.Provider value={session}>{children}</SessionContext.Provider>;
}

export function useSession(): MeResponse {
  const session = useContext(SessionContext);
  if (!session) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return session;
}
