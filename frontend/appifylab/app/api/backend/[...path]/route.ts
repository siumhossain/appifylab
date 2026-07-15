import { NextRequest, NextResponse } from "next/server";
import {
  BACKEND_URL,
  clearAuthCookies,
  getAuthTokens,
  isExpiringSoon,
  refreshTokens,
  setAuthCookies,
  type TokenPair,
} from "@/lib/server/auth";

type Ctx = { params: Promise<{ path: string[] }> };

async function proxy(req: NextRequest, { params }: Ctx) {
  const { path } = await params;
  const tokens = getAuthTokens(req);
  let access = tokens.access;
  const refresh = tokens.refresh;

  let rotated: TokenPair | null = null;
  if (refresh && (!access || isExpiringSoon(access))) {
    rotated = await refreshTokens(refresh);
    if (rotated) access = rotated.access_token;
  }

  if (!access) {
    const res = NextResponse.json(
      { results: null, message: "Not authenticated" },
      { status: 401 }
    );
    clearAuthCookies(res);
    return res;
  }

  const url = `${BACKEND_URL}/${path.join("/")}${req.nextUrl.search}`;
  const headers = new Headers({ Authorization: `Bearer ${access}` });
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);

  let backendRes: Response;
  try {
    backendRes = await fetch(url, {
      method: req.method,
      headers,
      body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer(),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { results: null, message: "Unable to reach the server. Please try again." },
      { status: 502 }
    );
  }

  const res = new NextResponse(backendRes.body, {
    status: backendRes.status,
    headers: { "Content-Type": backendRes.headers.get("content-type") ?? "application/json" },
  });
  if (rotated) setAuthCookies(res, rotated);
  return res;
}

export {
  proxy as GET,
  proxy as POST,
  proxy as PUT,
  proxy as PATCH,
  proxy as DELETE,
};
