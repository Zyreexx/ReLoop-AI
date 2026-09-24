import { NextRequest, NextResponse } from "next/server";
import { saveAssessment, getAssessment } from "@/lib/assessmentsStore";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { id, userId } = body;

    if (!id || !userId) {
      return NextResponse.json(
        { error: "Assessment ID and authenticated User ID are required." },
        { status: 400 }
      );
    }

    saveAssessment(id, body);

    return NextResponse.json({
      success: true,
      message: "Assessment saved successfully",
      assessmentId: id,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: "Failed to save assessment." },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json({ error: "Assessment ID missing" }, { status: 400 });
  }

  const found = getAssessment(id);
  if (!found) {
    return NextResponse.json({ error: "Assessment not found" }, { status: 404 });
  }

  return NextResponse.json({ success: true, assessment: found });
}
