import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Authentication lives in per-tab sessionStorage so different portals can be
  // open concurrently. Shared cookies cannot safely authorize a specific tab.
  void request;
  return NextResponse.next();
}

export const config = {
  matcher: ["/change-password", "/dashboard/:path*", "/admin/:path*", "/teacher/:path*", "/student/:path*", "/parent/:path*", "/accounts/:path*"]
};
