import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VisualInspectionStep } from "./VisualInspectionStep";
import { ReviewStep } from "./ReviewStep";
import { LanguageProvider } from "@/context/LanguageContext";
import * as api from "@/lib/api";
import { VisualInspectionData, DiagnosticData, UserSymptomsData } from "@/types/assessment";

vi.mock("@/lib/api", () => ({
  identifyProduct: vi.fn(),
  getProductCatalog: vi.fn().mockResolvedValue([
    { manufacturer: "Dell", model: "Latitude 5420" },
    { manufacturer: "Apple", model: "MacBook Air (M1, 2020)" },
    { manufacturer: "HP", model: "EliteBook 840 G7" },
  ]),
}));

const emptyInitialData: VisualInspectionData = {
  images: [],
  rawFiles: [],
  identifiedProduct: {
    manufacturer: "",
    model: "",
    confidence: 0,
    confirmed: false,
    visible_label_text: null,
  },
  visibleObservations: [],
};

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

describe("Visual Damage Analysis Pipeline & ReviewStep", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("1. VisualInspectionStep passes up to 6 uploaded files to identifyProduct (slice 0 to 6)", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "IDENTIFIED",
      identified_model: { manufacturer: "Dell", model: "Latitude 5420" },
      confidence: 0.95,
      visual_clues: ["Dell logo on chassis"],
      needs_confirmation: false,
    } as any);

    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={emptyInitialData}
          onComplete={vi.fn()}
        />
      </LanguageProvider>
    );

    const input = screen.getByTestId("file-upload-input");
    const mockFiles = Array.from({ length: 6 }, (_, i) =>
      new File([`content-${i}`], `photo-${i}.jpg`, { type: "image/jpeg" })
    );

    await userEvent.upload(input, mockFiles);

    await waitFor(() => {
      expect(api.identifyProduct).toHaveBeenCalledTimes(1);
    });

    const calledFiles = vi.mocked(api.identifyProduct).mock.calls[0][0];
    expect(calledFiles).toHaveLength(6);
  });

  it("2. VisualInspectionStep preserves damageFindings in onComplete callback", async () => {
    const onComplete = vi.fn();
    const dataWithDamage: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock1"],
      rawFiles: [new File(["dummy"], "p1.jpg", { type: "image/jpeg" })],
      identifiedProduct: {
        manufacturer: "Apple",
        model: "MacBook Pro 14",
        confidence: 0.95,
        confirmed: true,
        visible_label_text: null,
      },
      visibleObservations: [],
      damageFindings: [
        {
          component: "display",
          description: "Hairline crack on lower glass",
          severity: "HIGH",
          confidence: 0.9,
        },
      ],
      overallVisualCondition: "SERVICE_REQUIRED",
    };

    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={dataWithDamage}
          onComplete={onComplete}
        />
      </LanguageProvider>
    );

    const confirmBtn = screen.getByText(/Confirm & Continue/i);
    fireEvent.click(confirmBtn);

    expect(onComplete).toHaveBeenCalledWith(
      expect.objectContaining({
        damageFindings: expect.arrayContaining([
          expect.objectContaining({
            component: "display",
            severity: "HIGH",
          }),
        ]),
        overallVisualCondition: "SERVICE_REQUIRED",
      })
    );
  });

  it("3. VisualInspectionStep displays observations with damage severity badges when source is DAMAGE_ANALYSIS", async () => {
    const dataWithSeverity: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock1"],
      rawFiles: [],
      identifiedProduct: {
        manufacturer: "Dell",
        model: "Latitude 5420",
        confidence: 0.95,
        confirmed: true,
        visible_label_text: null,
      },
      visibleObservations: [
        {
          id: "vis-dmg-1",
          component: "display",
          condition: "visible_crack",
          observation: "Deep crack across panel",
          confidence: 0.92,
          severity: "HIGH",
          source: "DAMAGE_ANALYSIS",
        },
      ],
    };

    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={dataWithSeverity}
          onComplete={vi.fn()}
        />
      </LanguageProvider>
    );

    expect(screen.getByText("Deep crack across panel")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("4. VisualInspectionStep displays observations with MODEL CUE badge when source is MODEL_IDENTIFICATION", async () => {
    const dataWithModelCue: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock1"],
      rawFiles: [],
      identifiedProduct: {
        manufacturer: "Dell",
        model: "Latitude 5420",
        confidence: 0.95,
        confirmed: true,
        visible_label_text: null,
      },
      visibleObservations: [
        {
          id: "vis-cue-1",
          component: "chassis",
          condition: "no_visible_damage",
          observation: "Dell circular emblem centered on lid",
          confidence: 0.95,
          source: "MODEL_IDENTIFICATION",
        },
      ],
    };

    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={dataWithModelCue}
          onComplete={vi.fn()}
        />
      </LanguageProvider>
    );

    expect(screen.getByText("Dell circular emblem centered on lid")).toBeInTheDocument();
    expect(screen.getByText("MODEL CUE")).toBeInTheDocument();
  });

  it("5. ReviewStep displays actual damage findings with component name and severity badge", () => {
    const visualData: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Lenovo",
        model: "ThinkPad T14 Gen 1",
        confidence: 0.96,
        confirmed: true,
      },
      visibleObservations: [
        {
          id: "vis-cue-1",
          component: "chassis",
          condition: "no_visible_damage",
          observation: "ThinkPad red TrackPoint on keyboard",
          confidence: 0.95,
          source: "MODEL_IDENTIFICATION",
        },
      ],
      damageFindings: [
        {
          component: "keyboard",
          description: "Missing 'Ctrl' keycap on lower left",
          severity: "HIGH",
          confidence: 0.9,
        },
        {
          component: "chassis",
          description: "Light hairline scuff on base",
          severity: "LOW",
          confidence: 0.85,
        },
      ],
      overallVisualCondition: "SERVICE_REQUIRED",
    };

    render(
      <LanguageProvider>
        <ReviewStep
          visual={visualData}
          diagnostics={dummyDiagnostics}
          symptoms={dummySymptoms}
          onGenerateProfile={vi.fn()}
          isGenerating={false}
        />
      </LanguageProvider>
    );

    // Both damage findings should be rendered with severity badges
    expect(screen.getByText(/Missing 'Ctrl' keycap on lower left/i)).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText(/Light hairline scuff on base/i)).toBeInTheDocument();
    expect(screen.getByText("LOW")).toBeInTheDocument();

    // Model cue should be separated under hardware identification cues
    expect(screen.getByText(/ThinkPad red TrackPoint on keyboard/i)).toBeInTheDocument();
    expect(screen.getByText("MODEL CUE")).toBeInTheDocument();
  });

  it("6. ReviewStep displays 'No visible physical damage detected' when exterior is clean", () => {
    const cleanVisualData: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Apple",
        model: "MacBook Air",
        confidence: 0.98,
        confirmed: true,
      },
      visibleObservations: [],
      damageFindings: [],
      overallVisualCondition: "GOOD",
    };

    render(
      <LanguageProvider>
        <ReviewStep
          visual={cleanVisualData}
          diagnostics={dummyDiagnostics}
          symptoms={dummySymptoms}
          onGenerateProfile={vi.fn()}
          isGenerating={false}
        />
      </LanguageProvider>
    );

    expect(
      screen.getByText(/No visible physical damage detected on inspected exterior components/i)
    ).toBeInTheDocument();
  });

  it("7. ReviewStep displays 'Visual physical damage was not assessed' when analysis was unavailable", () => {
    const unassessedVisualData: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Dell",
        model: "Latitude 5420",
        confidence: 0.9,
        confirmed: true,
      },
      visibleObservations: [],
      damageFindings: [],
      overallVisualCondition: "NOT_ASSESSED",
    };

    render(
      <LanguageProvider>
        <ReviewStep
          visual={unassessedVisualData}
          diagnostics={dummyDiagnostics}
          symptoms={dummySymptoms}
          onGenerateProfile={vi.fn()}
          isGenerating={false}
        />
      </LanguageProvider>
    );

    expect(
      screen.getByText(/Visual physical damage was not assessed/i)
    ).toBeInTheDocument();
  });

  it("8. ReviewStep displays 'Visual physical damage was not assessed' when visualAnalysisStatus is FAILED", () => {
    const failedVisualData: VisualInspectionData = {
      images: ["data:image/jpeg;base64,mock"],
      identifiedProduct: {
        manufacturer: "Dell",
        model: "Latitude 5420",
        confidence: 0.9,
        confirmed: true,
      },
      visibleObservations: [],
      damageFindings: [],
      overallVisualCondition: "NOT_ASSESSED",
      visualAnalysisStatus: "FAILED",
      damageAnalysisCompleted: false,
    };

    render(
      <LanguageProvider>
        <ReviewStep
          visual={failedVisualData}
          diagnostics={dummyDiagnostics}
          symptoms={dummySymptoms}
          onGenerateProfile={vi.fn()}
          isGenerating={false}
        />
      </LanguageProvider>
    );

    expect(
      screen.getByText(/Visual physical damage was not assessed/i)
    ).toBeInTheDocument();
  });

  it("9. Mandatory visual inspection: manual model picker button is disabled when images.length === 0", () => {
    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={emptyInitialData}
          onComplete={vi.fn()}
        />
      </LanguageProvider>
    );

    const manualBtn = screen.getByText(/Select Model Manually/i);
    expect(manualBtn).toBeDisabled();
    expect(manualBtn).toHaveAttribute("title", "Please upload laptop photos first");
  });

  it("10. Non-laptop guard: VisualInspectionStep blocks manual selection when non-laptop detected", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "NON_LAPTOP_REJECTED",
      identified_model: null,
      is_laptop: false,
      allow_manual_selection: false,
      message: "Uploaded image appears to be a smartphone.",
    } as any);

    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={emptyInitialData}
          onComplete={vi.fn()}
        />
      </LanguageProvider>
    );

    const input = screen.getByTestId("file-upload-input");
    const mockFile = new File(["phone"], "phone.jpg", { type: "image/jpeg" });
    await userEvent.upload(input, mockFile);

    await waitFor(() => {
      expect(screen.getByText(/Uploaded image appears to be a smartphone/i)).toBeInTheDocument();
    });

    const manualBtn = screen.getByText(/Select Model Manually/i);
    expect(manualBtn).toBeDisabled();
    expect(screen.queryByTestId("model-picker")).not.toBeInTheDocument();
  });
});

