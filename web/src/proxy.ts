import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/signup"];
const AUTH_ONLY_PATHS = ["/login", "/signup"];

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const uid = req.cookies.get("sportsos_uid")?.value;
  const isPublic = PUBLIC_PATHS.includes(pathname);

  if (!uid && !isPublic) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  if (uid && (AUTH_ONLY_PATHS.includes(pathname) || pathname === "/")) {
    return NextResponse.redirect(new URL("/home", req.url));
  }
  return NextResponse.next();
}

export const config = {
  // Exclude API routes, Next internals, and any request for a static file (has a dot in the last
  // path segment — icons, images, fonts, etc.) so public assets are never gated behind login.
  matcher: ["/((?!api|_next/static|_next/image|.*\\.[\\w]+$).*)"],
};
