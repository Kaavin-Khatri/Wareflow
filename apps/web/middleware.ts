import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const sessionCookie = request.cookies.get("session")?.value;
  const { pathname } = request.nextUrl;

  // 1. If authenticated user visits login page, redirect to dashboard (except /login/2fa challenge)
  if (pathname === "/login" && sessionCookie) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // 2. Protect dashboard, operational, and administrative routes
  const isProtectedRoute =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/inventory") ||
    pathname.startsWith("/orders") ||
    pathname.startsWith("/invoices") ||
    pathname.startsWith("/returns") ||
    pathname.startsWith("/deliveries") ||
    pathname.startsWith("/reports") ||
    pathname.startsWith("/admin");

  if (isProtectedRoute && !sessionCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/dashboard/:path*",
    "/inventory/:path*",
    "/orders/:path*",
    "/invoices/:path*",
    "/returns/:path*",
    "/deliveries/:path*",
    "/reports/:path*",
    "/admin/:path*",
  ],
};
