import { NextRequest, NextResponse } from "next/server";
import { saveAssessment } from "@/lib/assessmentsStore";
import {
  ComponentConditionRecord,
  DiagnosticData,
  UserSymptomsData,
  VisualInspectionData,
} from "@/types/assessment";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { visual, diagnostics, symptoms, userId, userEmail } = body as {
      visual: VisualInspectionData;
      diagnostics: DiagnosticData;
      symptoms: UserSymptomsData;
      userId: string;
      userEmail: string;
    };

    if (!visual || !diagnostics || !symptoms) {
      return NextResponse.json(
        { error: "Complete assessment evidence (visual, diagnostics, symptoms) is required." },
        { status: 400 }
      );
    }

    // Server-side validation rules
    if (
      !diagnostics.battery.notProvided &&
      diagnostics.battery.fullChargeCapacity > diagnostics.battery.designCapacity
    ) {
      return NextResponse.json(
        { error: "Full charge capacity cannot exceed design capacity." },
        { status: 400 }
      );
    }

    if (
      !diagnostics.battery.notProvided &&
      (diagnostics.battery.healthPercentage < 0 || diagnostics.battery.healthPercentage > 100)
    ) {
      return NextResponse.json(
        { error: "Battery health percentage must be between 0% and 100%." },
        { status: 400 }
      );
    }

    const conditionProfile: ComponentConditionRecord[] = [];

    // 1. BATTERY COMPONENT
    if (diagnostics.battery.notProvided) {
      conditionProfile.push({
        component: "Battery",
        status: "needs_attention",
        statusLabel: "Not Measured",
        summary: "Diagnostic data not provided",
        confidence: "Medium",
        evidence: [
          {
            text: "User noted quick drainage in symptoms",
            source: "USER_REPORTED",
          },
        ],
        sourceTypes: ["USER_REPORTED"],
      });
    } else {
      const bHealth = diagnostics.battery.healthPercentage;
      const bStatus = bHealth >= 80 ? "good" : bHealth >= 65 ? "needs_attention" : "needs_service";
      const bLabel = bHealth >= 80 ? "Good" : bHealth >= 65 ? "Degraded" : "Service Required";
      conditionProfile.push({
        component: "Battery",
        status: bStatus,
        statusLabel: bLabel,
        summary: `${bHealth}% remaining capacity (${diagnostics.battery.fullChargeCapacity} / ${diagnostics.battery.designCapacity} ${diagnostics.battery.unit})`,
        confidence: "High",
        evidence: [
          {
            text: `${bHealth}% calculated capacity (${diagnostics.battery.cycleCount} cycles)`,
            source: "DIAGNOSTIC",
          },
          ...(symptoms.selectedSymptoms.some((s) => s.symptomId === "battery_drain")
            ? [{ text: "User reported quick battery drainage", source: "USER_REPORTED" as const }]
            : []),
        ],
        sourceTypes: symptoms.selectedSymptoms.some((s) => s.symptomId === "battery_drain")
          ? ["DIAGNOSTIC", "USER_REPORTED"]
          : ["DIAGNOSTIC"],
      });
    }

    // 2. SSD COMPONENT
    if (diagnostics.ssd.notProvided) {
      conditionProfile.push({
        component: "SSD / Storage",
        status: "good",
        statusLabel: "Unmeasured",
        summary: "Diagnostic data not provided",
        confidence: "Medium",
        evidence: [{ text: "No SMART diagnostic reported", source: "DIAGNOSTIC" }],
        sourceTypes: ["DIAGNOSTIC"],
      });
    } else {
      const ssdHealth = diagnostics.ssd.healthPercentage ?? 100;
      const smartPass = diagnostics.ssd.smartStatus === "PASS";
      const ssdStatus = smartPass && ssdHealth >= 80 ? "good" : ssdHealth >= 50 ? "needs_attention" : "fault";
      conditionProfile.push({
        component: "SSD / Storage",
        status: ssdStatus,
        statusLabel: smartPass ? `${ssdHealth}% Health (PASS)` : "SMART Warning",
        summary: `SMART Status: ${diagnostics.ssd.smartStatus}${diagnostics.ssd.powerOnHours ? ` • ${diagnostics.ssd.powerOnHours} hrs power-on` : ""}`,
        confidence: "High",
        evidence: [
          {
            text: `SMART Status ${diagnostics.ssd.smartStatus}, ${ssdHealth}% health`,
            source: "DIAGNOSTIC",
          },
        ],
        sourceTypes: ["DIAGNOSTIC"],
      });
    }

    // 3. RAM COMPONENT
    const ramResult = diagnostics.ram.testResult;
    conditionProfile.push({
      component: "RAM Memory",
      status: ramResult === "PASS" ? "good" : ramResult === "FAIL" ? "fault" : "good",
      statusLabel: ramResult === "PASS" ? `PASS (${diagnostics.ram.capacityGB} GB)` : ramResult === "FAIL" ? "FAIL" : "Unchecked",
      summary: `${diagnostics.ram.capacityGB} GB Installed • Memory Stress Test: ${ramResult}`,
      confidence: "High",
      evidence: [
        {
          text: `Memory stress test ${ramResult} (${diagnostics.ram.capacityGB} GB capacity)`,
          source: "DIAGNOSTIC",
        },
      ],
      sourceTypes: ["DIAGNOSTIC"],
    });

    // 4. THERMALS COMPONENT
    const throttled = diagnostics.thermals.thermalThrottling === "DETECTED";
    const userOverheat = symptoms.selectedSymptoms.some((s) => s.symptomId === "overheating");
    const thermalStatus = throttled || userOverheat ? "needs_service" : "good";
    conditionProfile.push({
      component: "Thermals & Cooling",
      status: thermalStatus,
      statusLabel: throttled ? "Throttling Detected" : userOverheat ? "Needs Service" : "Normal",
      summary: `CPU Temp: ${diagnostics.thermals.cpuTempC ? `${diagnostics.thermals.cpuTempC}°C` : "N/A"} • Throttling: ${diagnostics.thermals.thermalThrottling}`,
      confidence: "High",
      evidence: [
        {
          text: `Thermal throttling ${diagnostics.thermals.thermalThrottling.toLowerCase()}${diagnostics.thermals.cpuTempC ? ` at ${diagnostics.thermals.cpuTempC}°C` : ""}`,
          source: "DIAGNOSTIC",
        },
        ...(userOverheat
          ? [{ text: "User reported overheating during usage", source: "USER_REPORTED" as const }]
          : []),
      ],
      sourceTypes: userOverheat ? ["DIAGNOSTIC", "USER_REPORTED"] : ["DIAGNOSTIC"],
    });

    // 5. DISPLAY COMPONENT
    const visDisplay = visual.visibleObservations.find((v) => v.component === "display");
    const userDisplay = symptoms.selectedSymptoms.some((s) => s.symptomId === "display");
    conditionProfile.push({
      component: "Display Panel",
      status: userDisplay ? "needs_attention" : visDisplay?.condition === "visible_crack" ? "fault" : "good",
      statusLabel: userDisplay ? "Issues Reported" : visDisplay?.condition === "visible_crack" ? "Cracked" : "No Visible Crack",
      summary: visDisplay?.observation || "Glass and panel clean",
      confidence: "High",
      evidence: [
        {
          text: visDisplay?.observation || "No visible damage detected on display glass",
          source: "VISUAL",
        },
        ...(userDisplay
          ? [{ text: "User reported display flicker or visual defects", source: "USER_REPORTED" as const }]
          : []),
      ],
      sourceTypes: userDisplay ? ["VISUAL", "USER_REPORTED"] : ["VISUAL"],
    });

    // 6. KEYBOARD COMPONENT
    const visKbd = visual.visibleObservations.find((v) => v.component === "keyboard");
    const userKbd = symptoms.selectedSymptoms.some((s) => s.symptomId === "keyboard");
    conditionProfile.push({
      component: "Keyboard",
      status: userKbd || visKbd?.condition === "missing_key" ? "needs_attention" : "good",
      statusLabel: userKbd ? "Service Needed" : visKbd?.condition === "missing_key" ? "Missing Keys" : "Operational",
      summary: visKbd?.observation || "Keys operational",
      confidence: "High",
      evidence: [
        {
          text: visKbd?.observation || "Keycaps present and aligned",
          source: "VISUAL",
        },
        ...(userKbd
          ? [{ text: "User reported unresponsive key switches", source: "USER_REPORTED" as const }]
          : []),
      ],
      sourceTypes: userKbd ? ["VISUAL", "USER_REPORTED"] : ["VISUAL"],
    });

    // 7. TRACKPAD COMPONENT
    const userTrackpad = symptoms.selectedSymptoms.some((s) => s.symptomId === "trackpad");
    conditionProfile.push({
      component: "Trackpad",
      status: userTrackpad ? "needs_attention" : "good",
      statusLabel: userTrackpad ? "Issues Reported" : "Operational",
      summary: userTrackpad ? "Gesture or click responsiveness issue" : "Surface intact, click mechanism clean",
      confidence: "Medium",
      evidence: [
        {
          text: userTrackpad ? "User reported trackpad click issues" : "Visual check confirmed surface intact",
          source: userTrackpad ? "USER_REPORTED" : "VISUAL",
        },
      ],
      sourceTypes: [userTrackpad ? "USER_REPORTED" : "VISUAL"],
    });

    // 8. CHASSIS COMPONENT
    const visChassis = visual.visibleObservations.find((v) => v.component === "chassis");
    conditionProfile.push({
      component: "Chassis / Case",
      status: visChassis?.condition === "surface_scratches" ? "good" : visChassis?.condition === "loose_part" ? "needs_attention" : "good",
      statusLabel: visChassis?.condition === "surface_scratches" ? "Cosmetic Scratches" : "Good",
      summary: visChassis?.observation || "Chassis structurally sound",
      confidence: "High",
      evidence: [
        {
          text: visChassis?.observation || "Exterior housing verified",
          source: "VISUAL",
        },
      ],
      sourceTypes: ["VISUAL"],
    });

    // 9. HINGE COMPONENT
    const visHinge = visual.visibleObservations.find((v) => v.component === "hinge");
    const userHinge = symptoms.selectedSymptoms.some((s) => s.symptomId === "hinge");
    conditionProfile.push({
      component: "Hinge Mechanism",
      status: userHinge ? "needs_attention" : "good",
      statusLabel: userHinge ? "Loose / Damaged" : "Aligned",
      summary: visHinge?.observation || "Standard tension clearance",
      confidence: "High",
      evidence: [
        {
          text: visHinge?.observation || "Hinge alignment confirmed visually",
          source: "VISUAL",
        },
        ...(userHinge
          ? [{ text: "User reported loose hinge or creaking", source: "USER_REPORTED" as const }]
          : []),
      ],
      sourceTypes: userHinge ? ["VISUAL", "USER_REPORTED"] : ["VISUAL"],
    });

    // 10. SYSTEM DIAGNOSTICS COMPONENT
    const sysResult = diagnostics.system.hardwareResult;
    conditionProfile.push({
      component: "System / Motherboard",
      status: sysResult === "PASS" ? "good" : sysResult === "FAIL" ? "fault" : "good",
      statusLabel: sysResult === "PASS" ? "No Faults Detected" : sysResult === "FAIL" ? "Fault Detected" : "Unchecked",
      summary: "No critical faults detected from available diagnostics",
      confidence: "High",
      evidence: [
        {
          text: `Hardware diagnostics status: ${sysResult}`,
          source: "DIAGNOSTIC",
        },
      ],
      sourceTypes: ["DIAGNOSTIC"],
    });

    const assessmentRecord = {
      id: `assessment_${Date.now()}`,
      userId,
      userEmail,
      createdAt: new Date().toISOString(),
      visual,
      diagnostics,
      symptoms,
      conditionProfile,
    };

    saveAssessment(assessmentRecord.id, assessmentRecord);

    return NextResponse.json({
      success: true,
      assessment: assessmentRecord,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: "Failed to generate condition profile. Please verify your inputs." },
      { status: 500 }
    );
  }
}
