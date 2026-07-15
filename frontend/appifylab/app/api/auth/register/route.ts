import { NextRequest } from "next/server";
import { authenticate } from "@/lib/server/auth";

export async function POST(req: NextRequest) {
  return authenticate("/users/register", await req.text());
}
