export type SupportedModel = {
  id: string;
  manufacturer: string;
  model: string;
  category: string;
  defaultDesignCapacityMWh: number;
};

export const MVP_SUPPORTED_MODELS: SupportedModel[] = [
  {
    id: "dell-latitude-5420",
    manufacturer: "Dell",
    model: "Latitude 5420",
    category: "Enterprise Laptop",
    defaultDesignCapacityMWh: 51000,
  },
  {
    id: "apple-macbook-pro-16-m1",
    manufacturer: "Apple",
    model: 'MacBook Pro 16" (M1 Max)',
    category: "Professional Laptop",
    defaultDesignCapacityMWh: 99600,
  },
  {
    id: "lenovo-thinkpad-x1-gen9",
    manufacturer: "Lenovo",
    model: "ThinkPad X1 Carbon Gen 9",
    category: "Ultrabook",
    defaultDesignCapacityMWh: 57000,
  },
  {
    id: "apple-macbook-air-m1",
    manufacturer: "Apple",
    model: "MacBook Air M1 (2020)",
    category: "Ultrabook",
    defaultDesignCapacityMWh: 49900,
  },
  {
    id: "hp-elitebook-840-g8",
    manufacturer: "HP",
    model: "EliteBook 840 G8",
    category: "Enterprise Laptop",
    defaultDesignCapacityMWh: 53000,
  },
];

export type EvidenceSourceType = "VISUAL" | "DIAGNOSTIC" | "USER_REPORTED";

export type VisualObservation = {
  id: string;
  component: "chassis" | "display" | "keyboard" | "hinge" | "ports" | "trackpad";
  condition: "no_visible_damage" | "minor_wear" | "surface_scratches" | "loose_part" | "visible_crack" | "missing_key";
  observation: string;
  confidence: number;
};

export type VisualInspectionData = {
  images: string[];
  identifiedProduct: {
    manufacturer: string;
    model: string;
    confidence: number;
    confirmed: boolean;
  };
  visibleObservations: VisualObservation[];
};

export type BatteryDiagnostic = {
  designCapacity: number;
  fullChargeCapacity: number;
  cycleCount: number;
  unit: "mWh" | "Wh";
  healthPercentage: number;
  notProvided?: boolean;
};

export type SSDDiagnostic = {
  healthPercentage?: number;
  powerOnHours?: number;
  smartStatus: "PASS" | "FAIL" | "NOT_TESTED";
  notProvided?: boolean;
};

export type RAMDiagnostic = {
  capacityGB: number;
  testResult: "PASS" | "FAIL" | "NOT_TESTED";
  notProvided?: boolean;
};

export type ThermalsDiagnostic = {
  cpuTempC?: number;
  gpuTempC?: number;
  thermalThrottling: "DETECTED" | "NOT_DETECTED" | "UNKNOWN";
  overheatingSymptoms: boolean;
  notProvided?: boolean;
};

export type SystemDiagnostic = {
  hardwareResult: "PASS" | "FAIL" | "NOT_TESTED";
  criticalFaults: string;
  notProvided?: boolean;
};

export type DiagnosticData = {
  deviceAgeYears: number;
  battery: BatteryDiagnostic;
  ssd: SSDDiagnostic;
  ram: RAMDiagnostic;
  thermals: ThermalsDiagnostic;
  system: SystemDiagnostic;
};

export type UserSymptomItem = {
  symptomId: string;
  label: string;
  frequency: "never" | "occasionally" | "frequently" | "almost_always";
};

export type UserObjective = "lowest_cost" | "max_life" | "environmental" | "fastest_recovery";

export type UserSymptomsData = {
  selectedSymptoms: UserSymptomItem[];
  userDescription: string;
  userObjective: UserObjective;
};

export type ComponentStatus = "good" | "needs_attention" | "needs_service" | "fault";

export type ComponentConditionRecord = {
  component: string;
  status: ComponentStatus;
  statusLabel: string;
  summary: string;
  confidence: string;
  evidence: {
    text: string;
    source: EvidenceSourceType;
  }[];
  sourceTypes: EvidenceSourceType[];
};

export type FullAssessmentData = {
  id: string;
  userId: string;
  userEmail: string;
  createdAt: string;
  visual: VisualInspectionData;
  diagnostics: DiagnosticData;
  symptoms: UserSymptomsData;
  conditionProfile?: ComponentConditionRecord[];
};
