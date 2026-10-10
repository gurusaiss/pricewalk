import { jwtVerify } from "jose";
import { type NextRequest, NextResponse } from "next/server";

const COOKIE_NAME = "pw_access";
const PROTECTED_PREFIXES = ["/seller", "/buyer", "/settings", "/onboarding"];

type TokenPayload = {
  sub: string;
  role: "seller" | "buyer" | null;
};

async function readSession(request: NextRequest): Promise<TokenPayload | null> {
  const token = request.cookies.get(COOKIE_NAME)?.value;
  const secret = process.env.JWT_SECRET;
  if (!token || !secret) return null;

  try {
    const { payload } = await jwtVerify(token, new TextEncoder().encode(secret));
    return { sub: payload.sub as string, role: (payload.role as TokenPayload["role"]) ?? null };
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  if (!isProtected) {
    return NextResponse.next();
  }

  const session = await readSession(request);
  if (!session) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (!session.role) {
    if (!pathname.startsWith("/onboarding")) {
      return NextResponse.redirect(new URL("/onboarding/role", request.url));
    }
    return NextResponse.next();
  }

  // Block cross-role access: a seller can't browse /buyer/* and vice versa.
  if (pathname.startsWith("/seller") && session.role !== "seller") {
    return NextResponse.redirect(new URL(`/${session.role}`, request.url));
  }
  if (pathname.startsWith("/buyer") && session.role !== "buyer") {
    return NextResponse.redirect(new URL(`/${session.role}`, request.url));
  }
  if (pathname.startsWith("/onboarding")) {
    return NextResponse.redirect(new URL(`/${session.role}`, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/seller/:path*", "/buyer/:path*", "/settings/:path*", "/onboarding/:path*"],
};
