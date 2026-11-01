import { NextRequest, NextResponse } from "next/server";
import {
  saveAssessment,
  getAssessment,
  getUserAssessments,
  deleteAssessment,
  getDemoAssessments,
} from "@/lib/assessmentsStore";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { id, userId, userEmail, seedDemo } = body;

    // Handle seeding demo records
    if (seedDemo && (userId || userEmail)) {
      const email = userEmail || userId;
      const demoList = getDemoAssessments(email);
      for (const item of demoList) {
        saveAssessment(item.id, item);
      }
      return NextResponse.json({
        success: true,
        message: "Demo cases seeded successfully",
        count: demoList.length,
      });
    }

    if (!id || (!userId && !userEmail)) {
      return NextResponse.json(
        { error: "Assessment ID and authenticated User ID / Email are required." },
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
  const userId = searchParams.get("userId") || searchParams.get("userEmail");
  const seedIfEmpty = searchParams.get("seedIfEmpty") === "true";

  // 1. Get specific assessment by ID
  if (id) {
    const found = getAssessment(id);
    if (!found) {
      return NextResponse.json({ error: "Assessment not found" }, { status: 404 });
    }
    return NextResponse.json({ success: true, assessment: found });
  }

  // 2. Get all assessments for a user
  if (userId) {
    let list = getUserAssessments(userId);

    // If empty and seedIfEmpty requested, seed realistic demo cases
    if (list.length === 0 && seedIfEmpty) {
      const demoList = getDemoAssessments(userId);
      for (const item of demoList) {
        saveAssessment(item.id, item);
      }
      list = demoList;
    }

    return NextResponse.json({
      success: true,
      assessments: list,
      count: list.length,
    });
  }

  return NextResponse.json(
    { error: "Either 'id' or 'userId' / 'userEmail' query parameter is required." },
    { status: 400 }
  );
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json(
        { error: "Assessment ID is required for deletion." },
        { status: 400 }
      );
    }

    const removed = deleteAssessment(id);
    return NextResponse.json({
      success: true,
      deleted: removed,
      message: removed ? "Assessment deleted successfully" : "Assessment not found",
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: "Failed to delete assessment." },
      { status: 500 }
    );
  }
}
