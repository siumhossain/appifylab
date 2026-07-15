import { createCipheriv, createDecipheriv, createHash, randomBytes } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const COOKIE_SECRET = process.env.COOKIE_SECRET;
if (!COOKIE_SECRET) throw new Error("COOKIE_SECRET env var is required");
const COOKIE_KEY = createHash("sha256").update(COOKIE_SECRET).digest();

function seal(value: string): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", COOKIE_KEY, iv);
  const encrypted = Buffer.concat([cipher.update(value, "utf8"), cipher.final()]);
  return Buffer.concat([iv, cipher.getAuthTag(), encrypted]).toString("base64url");
}

function unseal(sealed: string): string | null {
  try {
    const buf = Buffer.from(sealed, "base64url");
    const decipher = createDecipheriv("aes-256-gcm", COOKIE_KEY, buf.subarray(0, 12));
    decipher.setAuthTag(buf.subarray(12, 28));
    return Buffer.concat([decipher.update(buf.subarray(28)), decipher.final()]).toString("utf8");
  } catch {
    return null;
  }
}

export const ACCESS_COOKIE = "_sa";
export const REFRESH_COOKIE = "_sr";
export const REFRESH_THRESHOLD_MS = 60_000;

export type TokenPair = { access_token: string; refresh_token: string };

const COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: "lax",
  path: "/api",
  secure: process.env.NODE_ENV === "production",
} as const;

export function tokenExpiresAt(token: string): number {
  try {
    const payload = JSON.parse(
      Buffer.from(token.split(".")[1], "base64url").toString()
    ) as { exp?: number };
    return (payload.exp ?? 0) * 1000;
  } catch {
    return 0;
  }
}

export function isExpiringSoon(token: string): boolean {
  return tokenExpiresAt(token) - Date.now() < REFRESH_THRESHOLD_MS;
}

export function setAuthCookies(res: NextResponse, tokens: TokenPair): void {
  res.cookies.set(ACCESS_COOKIE, seal(tokens.access_token), {
    ...COOKIE_OPTIONS,
    maxAge: Math.max(0, Math.floor((tokenExpiresAt(tokens.access_token) - Date.now()) / 1000)),
  });
  res.cookies.set(REFRESH_COOKIE, seal(tokens.refresh_token), {
    ...COOKIE_OPTIONS,
    maxAge: Math.max(0, Math.floor((tokenExpiresAt(tokens.refresh_token) - Date.now()) / 1000)),
  });
}

export function getAuthTokens(req: NextRequest): { access: string | null; refresh: string | null } {
  const access = req.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
  return {
    access: access ? unseal(access) : null,
    refresh: refresh ? unseal(refresh) : null,
  };
}

export function clearAuthCookies(res: NextResponse): void {
  res.cookies.set(ACCESS_COOKIE, "", { ...COOKIE_OPTIONS, maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, "", { ...COOKIE_OPTIONS, maxAge: 0 });
}

export async function authenticate(backendPath: string, rawBody: string): Promise<NextResponse> {
  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: rawBody,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { results: null, message: "Unable to reach the server. Please try again." },
      { status: 502 }
    );
  }

  const body = (await backendRes.json().catch(() => null)) as {
    results: (TokenPair & { user: unknown }) | null;
    message: string;
  } | null;

  if (!backendRes.ok || !body?.results) {
    return NextResponse.json(
      { results: null, message: body?.message ?? "Request failed" },
      { status: backendRes.status || 500 }
    );
  }

  const { access_token, refresh_token, user } = body.results;
  const res = NextResponse.json({ results: { user }, message: body.message });
  setAuthCookies(res, { access_token, refresh_token });
  return res;
}

export async function refreshTokens(refreshToken: string): Promise<TokenPair | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/users/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = (await res.json()) as { results: TokenPair };
    return body.results;
  } catch {
    return null;
  }
}
