import { NextRequest, NextResponse } from "next/server";
import { saveAssessment } from "@/lib/assessmentsStore";
import {
  ComponentConditionRecord,
  DiagnosticData,
  UserSymptomsData,
  VisualInspectionData,
  VisualObservation,
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
        status: "needs_attention",
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
    if (diagnostics.ram.notProvided || ramResult === "NOT_TESTED") {
      conditionProfile.push({
        component: "RAM Memory",
        status: "needs_attention",
        statusLabel: "Unchecked",
        summary: "Memory diagnostics not provided",
        confidence: "Medium",
        evidence: [{ text: "Memory diagnostics not provided", source: "DIAGNOSTIC" }],
        sourceTypes: ["DIAGNOSTIC"],
      });
    } else {
      conditionProfile.push({
        component: "RAM Memory",
        status: ramResult === "PASS" ? "good" : ramResult === "FAIL" ? "fault" : "needs_attention",
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
    }

    // 4. THERMALS COMPONENT
    const throttled = diagnostics.thermals.thermalThrottling === "DETECTED";
    const userOverheat = symptoms.selectedSymptoms.some((s) => s.symptomId === "overheating");
    if (diagnostics.thermals.notProvided || diagnostics.thermals.thermalThrottling === "UNKNOWN") {
      conditionProfile.push({
        component: "Thermals & Cooling",
        status: userOverheat ? "needs_service" : "needs_attention",
        statusLabel: userOverheat ? "Overheating Reported" : "Unmeasured",
        summary: userOverheat ? "User reported overheating" : "Thermal telemetry not provided",
        confidence: "Medium",
        evidence: [
          ...(userOverheat
            ? [{ text: "User reported overheating during usage", source: "USER_REPORTED" as const }]
            : [{ text: "No thermal diagnostics provided", source: "DIAGNOSTIC" as const }]),
        ],
        sourceTypes: userOverheat ? ["USER_REPORTED"] : ["DIAGNOSTIC"],
      });
    } else {
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
    }

    // Helper for exterior component synthesis (strictly prioritizes severe damage over minor wear/clean)
    const evaluateVisualComponent = (
      keywords: string[],
      fallbackName: string
    ) => {
      const matchingFindings: Array<{ description: string; severity: string; confidence: number }> = [];
      if (Array.isArray(visual.damageFindings)) {
        for (const f of visual.damageFindings) {
          const compLower = (f.component || "").toLowerCase();
          const descLower = (f.description || "").toLowerCase();
          if (keywords.some((kw) => compLower.includes(kw) || descLower.includes(kw))) {
            matchingFindings.push({
              description: f.description,
              severity: (f.severity || "LOW").toUpperCase(),
              confidence: f.confidence || 0.85,
            });
          }
        }
      }

      const matchingObs: VisualObservation[] = [];
      if (Array.isArray(visual.visibleObservations)) {
        for (const obs of visual.visibleObservations) {
          const compLower = (obs.component || "").toLowerCase();
          const obsLower = (obs.observation || "").toLowerCase();
          if (keywords.some((kw) => compLower.includes(kw) || obsLower.includes(kw))) {
            matchingObs.push(obs);
          }
        }
      }

      // Check for severe damage (crack, missing key, broken part, HIGH/CRITICAL)
      const severeFinding = matchingFindings.find(
        (f) => f.severity === "HIGH" || f.severity === "CRITICAL"
      );
      const severeObs = matchingObs.find(
        (o) =>
          o.severity === "HIGH" ||
          o.severity === "CRITICAL" ||
          o.condition === "visible_crack" ||
          o.condition === "missing_key"
      );

      if (severeFinding || severeObs) {
        const text = severeFinding?.description || severeObs?.observation || `${fallbackName} structural damage detected`;
        return {
          status: "fault" as const,
          statusLabel: "Damage Detected",
          summary: text,
          confidence: "High",
          evidenceText: text,
          hasEvidence: true,
        };
      }

      // Check for moderate wear / loose part (MODERATE/MEDIUM)
      const moderateFinding = matchingFindings.find(
        (f) => f.severity === "MODERATE" || f.severity === "MEDIUM"
      );
      const moderateObs = matchingObs.find(
        (o) =>
          o.severity === "MODERATE" ||
          o.condition === "loose_part"
      );

      if (moderateFinding || moderateObs) {
        const text = moderateFinding?.description || moderateObs?.observation || `${fallbackName} wear or loose part detected`;
        return {
          status: "needs_attention" as const,
          statusLabel: "Wear / Defect",
          summary: text,
          confidence: "High",
          evidenceText: text,
          hasEvidence: true,
        };
      }

      // Check for minor cosmetic wear (LOW)
      const minorFinding = matchingFindings.find((f) => f.severity === "LOW");
      const minorObs = matchingObs.find(
        (o) => o.severity === "LOW" || o.condition === "surface_scratches" || o.condition === "minor_wear"
      );
      if (minorFinding || minorObs) {
        const text = minorFinding?.description || minorObs?.observation || `${fallbackName} minor cosmetic wear`;
        return {
          status: "good" as const,
          statusLabel: "Cosmetic Wear",
          summary: text,
          confidence: "High",
          evidenceText: text,
          hasEvidence: true,
        };
      }

      // Check for explicit clean finding (NONE or no_visible_damage with clean observation)
      const cleanFinding = matchingFindings.find((f) => f.severity === "NONE");
      const cleanObs = matchingObs.find(
        (o) =>
          (o.severity === "NONE" || o.condition === "no_visible_damage") &&
          (o.source === "DAMAGE_ANALYSIS" || !o.source || o.observation.toLowerCase().includes(keywords[0]))
      );

      if (cleanFinding || cleanObs) {
        const text = cleanFinding?.description || cleanObs?.observation || `${fallbackName} inspected with no visible damage`;
        return {
          status: "good" as const,
          statusLabel: "Good",
          summary: text,
          confidence: "High",
          evidenceText: text,
          hasEvidence: true,
        };
      }

      // Fallback: If no visual evidence for this component, do NOT mark healthy
      return {
        status: "needs_attention" as const,
        statusLabel: "Untested / Not Inspected",
        summary: `Insufficient visual evidence to assess ${fallbackName.toLowerCase()}`,
        confidence: "Low",
        evidenceText: `No visual photos or observations provided for ${fallbackName.toLowerCase()}`,
        hasEvidence: false,
      };
    };

    // 5. DISPLAY COMPONENT
    const dispEval = evaluateVisualComponent(["display", "screen", "lcd"], "Display Panel");
    const userDisplay = symptoms.selectedSymptoms.some((s) => s.symptomId === "display");
    const dispStatus = dispEval.status === "fault" ? "fault" : userDisplay ? "needs_attention" : dispEval.status;
    const dispLabel = dispEval.status === "fault" ? "Cracked / Damaged" : userDisplay ? "Issues Reported" : dispEval.statusLabel;
    conditionProfile.push({
      component: "Display Panel",
      status: dispStatus,
      statusLabel: dispLabel,
      summary: userDisplay && dispEval.status !== "fault" ? "User reported display flicker or visual defects" : dispEval.summary,
      confidence: dispEval.confidence,
      evidence: [
        { text: dispEval.evidenceText, source: "VISUAL" },
        ...(userDisplay ? [{ text: "User reported display flicker or visual defects", source: "USER_REPORTED" as const }] : []),
      ],
      sourceTypes: userDisplay ? (dispEval.hasEvidence ? ["VISUAL", "USER_REPORTED"] : ["USER_REPORTED"]) : ["VISUAL"],
    });

    // 6. KEYBOARD COMPONENT
    const kbdEval = evaluateVisualComponent(["keyboard", "key"], "Keyboard");
    const userKbd = symptoms.selectedSymptoms.some((s) => s.symptomId === "keyboard");
    const kbdStatus = kbdEval.status === "fault" ? "fault" : userKbd ? "needs_attention" : kbdEval.status;
    const kbdLabel = kbdEval.status === "fault" ? "Missing / Damaged Keys" : userKbd ? "Service Needed" : kbdEval.statusLabel;
    conditionProfile.push({
      component: "Keyboard",
      status: kbdStatus,
      statusLabel: kbdLabel,
      summary: userKbd && kbdEval.status !== "fault" ? "User reported unresponsive key switches" : kbdEval.summary,
      confidence: kbdEval.confidence,
      evidence: [
        { text: kbdEval.evidenceText, source: "VISUAL" },
        ...(userKbd ? [{ text: "User reported unresponsive key switches", source: "USER_REPORTED" as const }] : []),
      ],
      sourceTypes: userKbd ? (kbdEval.hasEvidence ? ["VISUAL", "USER_REPORTED"] : ["USER_REPORTED"]) : ["VISUAL"],
    });

    // 7. TRACKPAD COMPONENT
    const padEval = evaluateVisualComponent(["trackpad", "touchpad", "swelling"], "Trackpad");
    const userTrackpad = symptoms.selectedSymptoms.some((s) => s.symptomId === "trackpad");
    const padStatus = padEval.status === "fault" ? "fault" : userTrackpad ? "needs_attention" : padEval.status;
    conditionProfile.push({
      component: "Trackpad",
      status: padStatus,
      statusLabel: padEval.status === "fault" ? "Surface Damage / Swelling" : userTrackpad ? "Issues Reported" : padEval.statusLabel,
      summary: userTrackpad && padEval.status !== "fault" ? "User reported trackpad click issues" : padEval.summary,
      confidence: padEval.confidence,
      evidence: [
        { text: padEval.evidenceText, source: "VISUAL" },
        ...(userTrackpad ? [{ text: "User reported trackpad click issues", source: "USER_REPORTED" as const }] : []),
      ],
      sourceTypes: userTrackpad ? (padEval.hasEvidence ? ["VISUAL", "USER_REPORTED"] : ["USER_REPORTED"]) : ["VISUAL"],
    });

    // 8. CHASSIS COMPONENT
    const chasEval = evaluateVisualComponent(["chassis", "casing", "lid", "bottom", "palmrest"], "Chassis / Case");
    conditionProfile.push({
      component: "Chassis / Case",
      status: chasEval.status,
      statusLabel: chasEval.status === "fault" ? "Structural Damage" : chasEval.statusLabel,
      summary: chasEval.summary,
      confidence: chasEval.confidence,
      evidence: [{ text: chasEval.evidenceText, source: "VISUAL" }],
      sourceTypes: ["VISUAL"],
    });

    // 9. HINGE COMPONENT
    const hingeEval = evaluateVisualComponent(["hinge"], "Hinge Mechanism");
    const userHinge = symptoms.selectedSymptoms.some((s) => s.symptomId === "hinge");
    const hingeStatus = hingeEval.status === "fault" ? "fault" : userHinge ? "needs_attention" : hingeEval.status;
    conditionProfile.push({
      component: "Hinge Mechanism",
      status: hingeStatus,
      statusLabel: hingeEval.status === "fault" ? "Broken Hinge" : userHinge ? "Loose / Creaking" : hingeEval.statusLabel,
      summary: userHinge && hingeEval.status !== "fault" ? "User reported loose hinge or creaking" : hingeEval.summary,
      confidence: hingeEval.confidence,
      evidence: [
        { text: hingeEval.evidenceText, source: "VISUAL" },
        ...(userHinge ? [{ text: "User reported loose hinge or creaking", source: "USER_REPORTED" as const }] : []),
      ],
      sourceTypes: userHinge ? (hingeEval.hasEvidence ? ["VISUAL", "USER_REPORTED"] : ["USER_REPORTED"]) : ["VISUAL"],
    });

    // 10. PORTS & CONNECTORS COMPONENT
    const portsEval = evaluateVisualComponent(["port", "ports", "usb", "hdmi", "type-c"], "Ports & Connectors");
    const userPorts = symptoms.selectedSymptoms.some((s) => s.symptomId === "ports" || s.symptomId === "port");
    const portsStatus = portsEval.status === "fault" ? "fault" : userPorts ? "needs_attention" : portsEval.status;
    conditionProfile.push({
      component: "Ports & Connectors",
      status: portsStatus,
      statusLabel: portsEval.status === "fault" ? "Damaged Ports" : userPorts ? "Port Issues Reported" : portsEval.statusLabel,
      summary: userPorts && portsEval.status !== "fault" ? "User reported port connectivity issues" : portsEval.summary,
      confidence: portsEval.confidence,
      evidence: [
        { text: portsEval.evidenceText, source: "VISUAL" },
        ...(userPorts ? [{ text: "User reported port connectivity issues", source: "USER_REPORTED" as const }] : []),
      ],
      sourceTypes: userPorts ? (portsEval.hasEvidence ? ["VISUAL", "USER_REPORTED"] : ["USER_REPORTED"]) : ["VISUAL"],
    });

    // 11. SYSTEM DIAGNOSTICS COMPONENT
    const sysResult = diagnostics.system.hardwareResult;
    if (diagnostics.system.notProvided || sysResult === "NOT_TESTED") {
      conditionProfile.push({
        component: "System / Motherboard",
        status: "needs_attention",
        statusLabel: "Unchecked",
        summary: "System hardware diagnostics not provided",
        confidence: "Low",
        evidence: [{ text: "Hardware diagnostics not provided", source: "DIAGNOSTIC" }],
        sourceTypes: ["DIAGNOSTIC"],
      });
    } else {
      conditionProfile.push({
        component: "System / Motherboard",
        status: sysResult === "PASS" ? "good" : sysResult === "FAIL" ? "fault" : "needs_attention",
        statusLabel: sysResult === "PASS" ? "No Faults Detected" : sysResult === "FAIL" ? "Fault Detected" : "Unchecked",
        summary: sysResult === "PASS" ? "No critical faults detected from available diagnostics" : "Critical system hardware faults reported",
        confidence: "High",
        evidence: [
          {
            text: `Hardware diagnostics status: ${sysResult}`,
            source: "DIAGNOSTIC",
          },
        ],
        sourceTypes: ["DIAGNOSTIC"],
      });
    }

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
