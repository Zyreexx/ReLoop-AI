import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * POST /api/auth/verify-otp
 * Proxies to the FastAPI backend /api/auth/verify-otp
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/api/auth/verify-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      const errorMessage =
        (typeof data.error === "object" ? data.error?.message : data.error) ||
        data.detail ||
        "Verification failed.";
      return NextResponse.json(
        { error: errorMessage },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "Could not reach the backend server (http://localhost:8000). Please start the backend in a terminal." },
      { status: 503 }
    );
  }
}
