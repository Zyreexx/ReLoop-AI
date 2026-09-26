import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * POST /api/auth/google
 * Proxies Google ID token verification to the FastAPI backend.
 * Backend enforces:
 *  - Only valid Google-issued emails (email_verified=true from Google)
 *  - mode=login: user must already be registered (404 otherwise)
 *  - mode=register: creates account if new, logs in if already exists
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    if (!body.credential) {
      return NextResponse.json(
        { error: "Google credential is required." },
        { status: 400 }
      );
    }

    const res = await fetch(`${BACKEND_URL}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || "Google authentication failed." },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "Could not reach the server. Please try again." },
      { status: 503 }
    );
  }
}
