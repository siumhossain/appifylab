import { NextResponse } from "next/server";
import { clearAuthCookies } from "@/lib/server/auth";

export async function POST() {
  const res = NextResponse.json({ results: null, message: "Logged out" });
  clearAuthCookies(res);
  return res;
}
