import { cookies } from "next/headers";
import type { MeResponse } from "./types";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";
export const SESSION_COOKIE = "sportsos_uid";

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
