import { NextRequest } from "next/server";
import { authenticate } from "@/lib/server/auth";

export async function POST(req: NextRequest) {
  return authenticate("/users/login", await req.text());
}
