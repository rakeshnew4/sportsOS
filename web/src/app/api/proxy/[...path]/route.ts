import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/session";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

async function proxy(req: NextRequest, path: string[]) {
  const cookieStore = await cookies();
  const uid = cookieStore.get(SESSION_COOKIE)?.value;

  const targetUrl = new URL(`${API_BASE_URL}/${path.join("/")}`);
  targetUrl.search = req.nextUrl.search;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (uid) headers["Authorization"] = `Bearer ${uid}`;

  const hasBody = !["GET", "HEAD"].includes(req.method);
  const body = hasBody ? await req.text() : undefined;

  const res = await fetch(targetUrl, {
    method: req.method,
    headers,
    body: body && body.length > 0 ? body : undefined,
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
  });
}

type RouteParams = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}
export async function POST(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}
export async function PUT(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}
export async function DELETE(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}
