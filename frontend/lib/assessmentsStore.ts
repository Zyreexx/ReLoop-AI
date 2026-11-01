// Server-side in-memory singleton store for assessment records
const globalStore: Map<string, any> = (global as any).__assessmentsStore || new Map<string, any>();
if (!(global as any).__assessmentsStore) {
  (global as any).__assessmentsStore = globalStore;
}

export function saveAssessment(id: string, data: any) {
  globalStore.set(id, {
    ...data,
    updatedAt: new Date().toISOString(),
  });
}

export function getAssessment(id: string) {
  return globalStore.get(id);
}

export function getUserAssessments(userIdOrEmail: string): any[] {
  const cleanId = (userIdOrEmail || "").trim().toLowerCase();
  const results: any[] = [];

  for (const record of globalStore.values()) {
    const rUserId = (record.userId || "").trim().toLowerCase();
    const rUserEmail = (record.userEmail || "").trim().toLowerCase();
    const rEmail = (record.user?.email || "").trim().toLowerCase();

    if (
      !cleanId ||
      rUserId === cleanId ||
      rUserEmail === cleanId ||
      rEmail === cleanId
    ) {
      results.push(record);
    }
  }

  // Sort newest first
  return results.sort((a, b) => {
    const timeA = new Date(a.createdAt || a.updatedAt || 0).getTime();
    const timeB = new Date(b.createdAt || b.updatedAt || 0).getTime();
    return timeB - timeA;
  });
}

export function deleteAssessment(id: string): boolean {
  return globalStore.delete(id);
}

export function getDemoAssessments(userEmail: string = "demo@reloop.ai"): any[] {
  return [
    {
      id: "demo_dell_5420",
      userId: userEmail,
      userEmail: userEmail,
      createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
      backendProductId: "prod_dell_5420",
      overallHealth: "FAIR",
      visual: {
        images: [],
        identifiedProduct: {
          manufacturer: "Dell",
          model: "Latitude 5420",
          confidence: 0.94,
          confirmed: true,
        },
        visibleObservations: [
          "Minor chassis scratches on top cover",
          "Display bezel intact with no glass cracks",
          "Two keyboard keycaps slightly worn",
        ],
      },
      diagnostics: {
        deviceAgeYears: 4.5,
        battery: {
          designCapacity: 51000,
          fullChargeCapacity: 37230,
          cycleCount: 482,
          unit: "mWh",
          healthPercentage: 73,
          notProvided: false,
        },
        ssd: {
          healthPercentage: 91,
          powerOnHours: 3420,
          smartStatus: "PASS",
          notProvided: false,
        },
        ram: {
          capacityGB: 16,
          testResult: "PASS",
        },
        thermals: {
          cpuTempC: 88,
          gpuTempC: 75,
          thermalThrottling: "DETECTED",
          overheatingSymptoms: true,
        },
        system: {
          hardwareResult: "PASS",
          criticalFaults: "None reported",
        },
      },
      symptoms: {
        selectedSymptoms: [
          { symptomId: "battery_drain", label: "Battery drains quickly", frequency: "frequently" },
          { symptomId: "overheating", label: "Device overheats under load", frequency: "occasionally" },
        ],
        userDescription: "Works great when plugged into power, but drains within 45 mins unplugged. Fan runs loud.",
        userObjective: "max_life",
      },
      conditionProfile: [
        {
          component: "Battery",
          status: "needs_attention",
          statusLabel: "Degraded (73%)",
          summary: "73% capacity remaining (482 cycles). Service advised for mobile use.",
          confidence: "High",
          evidence: [{ text: "Battery diagnostic: 37230/51000 mWh", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC", "USER_REPORTED"],
        },
        {
          component: "SSD / Storage",
          status: "good",
          statusLabel: "Healthy (91%)",
          summary: "SMART status PASS. 3,420 power-on hours with high endurance remaining.",
          confidence: "High",
          evidence: [{ text: "SMART test passed with 0 uncorrectable errors", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
        {
          component: "RAM / Memory",
          status: "good",
          statusLabel: "Healthy (16 GB)",
          summary: "16 GB DDR4 tested and fully functional. Passing all memtest patterns.",
          confidence: "High",
          evidence: [{ text: "Hardware memory diagnostic PASS", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
        {
          component: "Thermals & Cooling",
          status: "needs_service",
          statusLabel: "Service Required",
          summary: "CPU peak 88°C with thermal throttling observed. Thermal paste replacement needed.",
          confidence: "High",
          evidence: [{ text: "Thermal benchmark detected throttling at 88°C", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC", "USER_REPORTED"],
        },
        {
          component: "Display",
          status: "good",
          statusLabel: "Intact",
          summary: "No cracks, dead pixels, or delamination visible.",
          confidence: "High",
          evidence: [{ text: "Visual photo review shows clear panel", source: "VISUAL" }],
          sourceTypes: ["VISUAL"],
        },
        {
          component: "Keyboard & Trackpad",
          status: "good",
          statusLabel: "Functional",
          summary: "Normal wear on select keycaps, fully responsive membrane switches.",
          confidence: "Medium",
          evidence: [{ text: "Visual inspection verified all keys present", source: "VISUAL" }],
          sourceTypes: ["VISUAL"],
        },
        {
          component: "Chassis & Hinge",
          status: "good",
          statusLabel: "Solid",
          summary: "Standard minor cosmetic scuffs on edges. Hinges firm with no play.",
          confidence: "High",
          evidence: [{ text: "Visual inspection of hinge alignment", source: "VISUAL" }],
          sourceTypes: ["VISUAL"],
        },
        {
          component: "Motherboard & System",
          status: "good",
          statusLabel: "Healthy",
          summary: "All system diagnostics passed. No voltage irregularities or BIOS faults.",
          confidence: "High",
          evidence: [{ text: "System controller self-test: PASS", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
      ],
      topPathway: {
        pathway: "REPAIR",
        title: "Component Repair & Thermal Servicing",
        action: "Replace battery pack & re-paste heatsink assembly",
        lifeExtensionYears: 3.5,
        avoidedCo2Kg: 215,
        estimatedCostUsd: 65,
        turnaroundDays: 2,
      },
    },
    {
      id: "demo_lenovo_t14",
      userId: userEmail,
      userEmail: userEmail,
      createdAt: new Date(Date.now() - 86400000 * 5).toISOString(),
      backendProductId: "prod_lenovo_t14",
      overallHealth: "GOOD",
      visual: {
        images: [],
        identifiedProduct: {
          manufacturer: "Lenovo",
          model: "ThinkPad T14 Gen 1",
          confidence: 0.96,
          confirmed: true,
        },
        visibleObservations: [
          "Very clean corporate condition with minor palmrest wear",
          "Screen pristine, no dead pixels",
        ],
      },
      diagnostics: {
        deviceAgeYears: 3.8,
        battery: {
          designCapacity: 50000,
          fullChargeCapacity: 43500,
          cycleCount: 210,
          unit: "mWh",
          healthPercentage: 87,
          notProvided: false,
        },
        ssd: {
          healthPercentage: 94,
          powerOnHours: 2100,
          smartStatus: "PASS",
          notProvided: false,
        },
        ram: {
          capacityGB: 16,
          testResult: "PASS",
        },
        thermals: {
          cpuTempC: 72,
          gpuTempC: 68,
          thermalThrottling: "NONE",
          overheatingSymptoms: false,
        },
        system: {
          hardwareResult: "PASS",
          criticalFaults: "None reported",
        },
      },
      symptoms: {
        selectedSymptoms: [
          { symptomId: "slow_performance", label: "Needs more memory for multitasking", frequency: "frequently" },
        ],
        userDescription: "Excellent laptop, just needs more RAM and larger storage for data science workloads.",
        userObjective: "max_life",
      },
      conditionProfile: [
        {
          component: "Battery",
          status: "good",
          statusLabel: "Good (87%)",
          summary: "87% health with only 210 cycles. 5+ hours run-time.",
          confidence: "High",
          evidence: [{ text: "Battery diagnostic 43500/50000 mWh", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
        {
          component: "SSD / Storage",
          status: "good",
          statusLabel: "Healthy (94%)",
          summary: "512 GB NVMe SSD with 94% health remaining.",
          confidence: "High",
          evidence: [{ text: "SMART verified", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
        {
          component: "RAM / Memory",
          status: "good",
          statusLabel: "Upgrade Eligible",
          summary: "16 GB RAM with open SODIMM slot for expansion to 32 GB.",
          confidence: "High",
          evidence: [{ text: "16 GB tested PASS, SODIMM socket available", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC", "DATABASE"],
        },
        {
          component: "Thermals & Cooling",
          status: "good",
          statusLabel: "Cool & Quiet",
          summary: "Peak load temp 72°C. No throttling detected.",
          confidence: "High",
          evidence: [{ text: "Thermal check PASS", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
        {
          component: "Display",
          status: "good",
          statusLabel: "Pristine",
          summary: "FHD IPS anti-glare display in flawless condition.",
          confidence: "High",
          evidence: [{ text: "Visual inspection verified", source: "VISUAL" }],
          sourceTypes: ["VISUAL"],
        },
        {
          component: "Keyboard & Trackpad",
          status: "good",
          statusLabel: "Excellent",
          summary: "Classic ThinkPad keyboard in near-mint condition.",
          confidence: "High",
          evidence: [{ text: "Visual photo review verified", source: "VISUAL" }],
          sourceTypes: ["VISUAL"],
        },
        {
          component: "Chassis & Hinge",
          status: "good",
          statusLabel: "Rugged & Clean",
          summary: "Magnesium roll-cage chassis intact. Minimal wear.",
          confidence: "High",
          evidence: [{ text: "Visual inspection verified", source: "VISUAL" }],
          sourceTypes: ["VISUAL"],
        },
        {
          component: "Motherboard & System",
          status: "good",
          statusLabel: "Flawless",
          summary: "No hardware faults detected.",
          confidence: "High",
          evidence: [{ text: "Diagnostics PASS", source: "DIAGNOSTIC" }],
          sourceTypes: ["DIAGNOSTIC"],
        },
      ],
      topPathway: {
        pathway: "UPGRADE",
        title: "Modular RAM & Storage Upgrade",
        action: "Add 16 GB DDR4 SODIMM module + 1TB NVMe drive",
        lifeExtensionYears: 4.0,
        avoidedCo2Kg: 245,
        estimatedCostUsd: 85,
        turnaroundDays: 1,
      },
    },
  ];
}
