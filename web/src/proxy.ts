import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/signup"];

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const uid = req.cookies.get("sportsos_uid")?.value;
  const isPublic = PUBLIC_PATHS.includes(pathname);

  if (!uid && !isPublic) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  if (uid && isPublic) {
    return NextResponse.redirect(new URL("/", req.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
