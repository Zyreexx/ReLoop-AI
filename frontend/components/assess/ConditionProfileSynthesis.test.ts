import { describe, it, expect } from "vitest";
import { POST } from "@/app/api/assessments/generate-condition-profile/route";
import { VisualInspectionData, DiagnosticData, UserSymptomsData } from "@/types/assessment";

const dummyDiagnostics: DiagnosticData = {
  deviceAgeYears: 2,
  battery: {
    designCapacity: 50000,
    fullChargeCapacity: 45000,
    cycleCount: 150,
    unit: "mWh",
    healthPercentage: 90,
    notProvided: false,
  },
  ssd: {
    healthPercentage: 98,
    powerOnHours: 1200,
    smartStatus: "PASS",
    notProvided: false,
  },
  ram: {
    capacityGB: 16,
    testResult: "PASS",
    notProvided: false,
  },
  thermals: {
    cpuTempC: 45,
    gpuTempC: 42,
    thermalThrottling: "NOT_DETECTED",
    overheatingSymptoms: false,
    notProvided: false,
  },
  system: {
    hardwareResult: "PASS",
    criticalFaults: "",
    notProvided: false,
  },
};

const dummySymptoms: UserSymptomsData = {
  selectedSymptoms: [],
  userDescription: "",
  userObjective: "max_life",
};

describe("Condition Profile Synthesis Route (generate-condition-profile)", () => {
  it("1. Missing keyboard observation must NOT imply a healthy keyboard", async () => {
    // Only display evidence provided; keyboard has NO observations or damage findings
    const visual: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Dell",
        model: "Latitude 5420",
        confidence: 0.95,
        confirmed: true,
      },
      visibleObservations: [
        {
          id: "vis-disp-1",
          component: "display",
          condition: "no_visible_damage",
          observation: "Display panel clean",
          confidence: 0.9,
          severity: "NONE",
        },
      ],
      damageFindings: [
        {
          component: "display",
          description: "Display panel clean",
          severity: "NONE",
          confidence: 0.9,
        },
      ],
      overallVisualCondition: "GOOD",
    };

    const req = new Request("http://localhost:3000/api/assessments/generate-condition-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visual,
        diagnostics: dummyDiagnostics,
        symptoms: dummySymptoms,
        userId: "test-user",
        userEmail: "test@example.com",
      }),
    });

    const res = await POST(req as any);
    expect(res.status).toBe(200);
    const body = await res.json();
    const profile = body.assessment.conditionProfile;

    // Display should be good
    const displayComp = profile.find((c: any) => c.component === "Display Panel");
    expect(displayComp).toBeDefined();
    expect(displayComp.status).toBe("good");

    // Keyboard was NOT observed: must NOT be healthy
    const kbdComp = profile.find((c: any) => c.component === "Keyboard");
    expect(kbdComp).toBeDefined();
    expect(kbdComp.status).not.toBe("good");
    expect(kbdComp.status).toBe("needs_attention");
    expect(kbdComp.statusLabel).toMatch(/Untested|Not Inspected/i);
  });

  it("2. Severe display damage must be reflected in the condition profile as fault", async () => {
    const visual: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Apple",
        model: "MacBook Pro",
        confidence: 0.95,
        confirmed: true,
      },
      visibleObservations: [],
      damageFindings: [
        {
          component: "display",
          description: "Shattered LCD glass panel",
          severity: "HIGH",
          confidence: 0.95,
        },
      ],
      overallVisualCondition: "SERVICE_REQUIRED",
    };

    const req = new Request("http://localhost:3000/api/assessments/generate-condition-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visual,
        diagnostics: dummyDiagnostics,
        symptoms: dummySymptoms,
        userId: "test-user",
        userEmail: "test@example.com",
      }),
    });

    const res = await POST(req as any);
    const body = await res.json();
    const displayComp = body.assessment.conditionProfile.find((c: any) => c.component === "Display Panel");
    expect(displayComp.status).toBe("fault");
    expect(displayComp.statusLabel).toBe("Cracked / Damaged");
    expect(displayComp.summary).toContain("Shattered LCD glass panel");
  });

  it("3. Severe hinge fracture must be reflected as fault in Hinge Mechanism", async () => {
    const visual: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Lenovo",
        model: "ThinkPad T14",
        confidence: 0.95,
        confirmed: true,
      },
      visibleObservations: [
        {
          id: "vis-scuff",
          component: "chassis",
          condition: "surface_scratches",
          observation: "Minor scuff on base",
          confidence: 0.8,
          severity: "LOW",
        },
      ],
      damageFindings: [
        {
          component: "chassis",
          description: "Minor scuff on base",
          severity: "LOW",
          confidence: 0.8,
        },
        {
          component: "hinge",
          description: "Broken right hinge mount with casing separation",
          severity: "HIGH",
          confidence: 0.95,
        },
      ],
      overallVisualCondition: "SERVICE_REQUIRED",
    };

    const req = new Request("http://localhost:3000/api/assessments/generate-condition-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visual,
        diagnostics: dummyDiagnostics,
        symptoms: dummySymptoms,
        userId: "test-user",
        userEmail: "test@example.com",
      }),
    });

    const res = await POST(req as any);
    const body = await res.json();
    const hingeComp = body.assessment.conditionProfile.find((c: any) => c.component === "Hinge Mechanism");
    expect(hingeComp.status).toBe("fault");
    expect(hingeComp.statusLabel).toBe("Broken Hinge");
  });

  it("4. Port damage must not be dropped and reflected in Ports & Connectors as fault", async () => {
    const visual: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "HP",
        model: "EliteBook",
        confidence: 0.95,
        confirmed: true,
      },
      visibleObservations: [],
      damageFindings: [
        {
          component: "ports",
          description: "Fractured USB-C connector with bent pins",
          severity: "HIGH",
          confidence: 0.92,
        },
      ],
      overallVisualCondition: "SERVICE_REQUIRED",
    };

    const req = new Request("http://localhost:3000/api/assessments/generate-condition-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visual,
        diagnostics: dummyDiagnostics,
        symptoms: dummySymptoms,
        userId: "test-user",
        userEmail: "test@example.com",
      }),
    });

    const res = await POST(req as any);
    const body = await res.json();
    const portsComp = body.assessment.conditionProfile.find((c: any) => c.component === "Ports & Connectors");
    expect(portsComp).toBeDefined();
    expect(portsComp.status).toBe("fault");
    expect(portsComp.statusLabel).toBe("Damaged Ports");
  });

  it("5. Photographs never set internal battery, SSD, or RAM status to healthy", async () => {
    // Visual inspection has clean observations, but diagnostics are notProvided
    const visual: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Dell",
        model: "Latitude 5420",
        confidence: 0.95,
        confirmed: true,
      },
      visibleObservations: [
        {
          id: "fake-batt",
          component: "battery" as any,
          condition: "no_visible_damage",
          observation: "Battery looks intact through case",
          confidence: 0.95,
          severity: "NONE",
        },
      ],
      damageFindings: [],
      overallVisualCondition: "GOOD",
    };

    const unprovidedDiagnostics: DiagnosticData = {
      deviceAgeYears: 0,
      battery: {
        designCapacity: 0,
        fullChargeCapacity: 0,
        cycleCount: 0,
        unit: "mWh",
        healthPercentage: 0,
        notProvided: true,
      },
      ssd: {
        healthPercentage: 0,
        powerOnHours: 0,
        smartStatus: "NOT_TESTED",
        notProvided: true,
      },
      ram: {
        capacityGB: 0,
        testResult: "NOT_TESTED",
        notProvided: true,
      },
      thermals: {
        cpuTempC: 0,
        gpuTempC: 0,
        thermalThrottling: "UNKNOWN",
        overheatingSymptoms: false,
        notProvided: true,
      },
      system: {
        hardwareResult: "NOT_TESTED",
        criticalFaults: "",
        notProvided: true,
      },
    };

    const req = new Request("http://localhost:3000/api/assessments/generate-condition-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visual,
        diagnostics: unprovidedDiagnostics,
        symptoms: dummySymptoms,
        userId: "test-user",
        userEmail: "test@example.com",
      }),
    });

    const res = await POST(req as any);
    const body = await res.json();
    const profile = body.assessment.conditionProfile;

    // None of the internal components may be GOOD
    const batteryComp = profile.find((c: any) => c.component === "Battery");
    expect(batteryComp.status).not.toBe("good");
    expect(batteryComp.status).toBe("needs_attention");

    const ssdComp = profile.find((c: any) => c.component === "SSD / Storage");
    expect(ssdComp.status).not.toBe("good");
    expect(ssdComp.status).toBe("needs_attention");

    const ramComp = profile.find((c: any) => c.component === "RAM Memory");
    expect(ramComp.status).not.toBe("good");
    expect(ramComp.status).toBe("needs_attention");
  });
});

