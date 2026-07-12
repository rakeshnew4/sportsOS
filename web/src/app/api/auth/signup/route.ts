import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { isSecureRequest, SESSION_COOKIE } from "@/lib/session";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  const { role, display_name, phone } = await req.json();
  const endpoint = role === "owner" ? "/auth/register/owner" : "/auth/register/player";

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name, phone }),
  });

  const data = await res.json();
  if (!res.ok) {
    return NextResponse.json(data, { status: res.status });
  }

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, data.uid, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: isSecureRequest(req),
  });

  return NextResponse.json(data);
}
