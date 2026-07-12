import { cookies } from "next/headers";
import type { NextRequest } from "next/server";
import type { MeResponse } from "./types";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";
export const SESSION_COOKIE = "sportsos_uid";

// Browsers silently drop `Secure` cookies on a plain-http response, which
// breaks login entirely on deployments without TLS in front. Base the flag
// on the actual request instead of NODE_ENV, so it's correct over http now
// and picks up https automatically once a reverse proxy terminates TLS
// (proxies set x-forwarded-proto).
export function isSecureRequest(req: NextRequest): boolean {
  return req.headers.get("x-forwarded-proto") === "https" || req.nextUrl.protocol === "https:";
}

export async function getSession(): Promise<MeResponse | null> {
  const cookieStore = await cookies();
  const uid = cookieStore.get(SESSION_COOKIE)?.value;
  if (!uid) return null;

  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${uid}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}
