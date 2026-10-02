import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VisualInspectionStep } from "./VisualInspectionStep";
import { LanguageProvider } from "@/context/LanguageContext";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  identifyProduct: vi.fn(),
  getProductCatalog: vi.fn().mockResolvedValue([
    { manufacturer: "Dell", model: "Latitude 5420" },
    { manufacturer: "Apple", model: "MacBook Air (M1, 2020)" },
    { manufacturer: "HP", model: "EliteBook 840 G7" },
    { manufacturer: "Lenovo", model: "ThinkPad T14 Gen 1" },
  ]),
}));

const emptyInitialData = {
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

const renderWithContext = (props = {}) => {
  const onComplete = vi.fn();
  const utils = render(
    <LanguageProvider>
      <VisualInspectionStep
        initialData={emptyInitialData}
        onComplete={onComplete}
        {...props}
      />
    </LanguageProvider>
  );
  return { ...utils, onComplete };
};

const createMockFile = (name = "laptop.jpg", type = "image/jpeg") => {
  const file = new File(["dummy-content"], name, { type });
  return file;
};

describe("VisualInspectionStep", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("1. 0 images uploaded -> no error banner, no model picker, no verified card", async () => {
    renderWithContext();

    expect(screen.queryByTestId("error-banner")).not.toBeInTheDocument();
    expect(screen.queryByTestId("model-picker")).not.toBeInTheDocument();
    expect(screen.queryByTestId("verified-model-card")).not.toBeInTheDocument();
    expect(screen.getByText(/0 \/ 6/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(api.getProductCatalog).toHaveBeenCalled();
    });
  });

  it("2. identification returns UNKNOWN -> error banner AND picker both visible with working retry link", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "UNKNOWN",
      identified_model: null,
      candidate_id: "UNKNOWN",
      is_supported: false,
      confidence: 0.2,
      confidence_level: "UNKNOWN",
      needs_confirmation: true,
      message: "Model could not be identified.",
    } as any);

    renderWithContext();

    const file = createMockFile();
    const input = screen.getByTestId("file-upload-input");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByTestId("error-banner")).toBeInTheDocument();
    });

    expect(screen.getByTestId("model-picker")).toBeInTheDocument();
    expect(screen.getByTestId("retry-detection-btn")).toBeInTheDocument();
    expect(screen.queryByTestId("verified-model-card")).not.toBeInTheDocument();
  });

  it("3. identification returns AI_UNAVAILABLE -> error banner AND picker both visible", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "AI_UNAVAILABLE",
      identified_model: null,
      message: "AI identification is temporarily unavailable.",
    } as any);

    renderWithContext();

    const file = createMockFile();
    const input = screen.getByTestId("file-upload-input");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByTestId("error-banner")).toBeInTheDocument();
      expect(screen.getByTestId("model-picker")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("verified-model-card")).not.toBeInTheDocument();
  });

  it("4. identification returns INVALID_EVIDENCE -> error banner AND picker both visible", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "INVALID_EVIDENCE",
      identified_model: null,
      message: "Unable to analyze these photos.",
    } as any);

    renderWithContext();

    const file = createMockFile();
    const input = screen.getByTestId("file-upload-input");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByTestId("error-banner")).toBeInTheDocument();
      expect(screen.getByTestId("model-picker")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("verified-model-card")).not.toBeInTheDocument();
  });

  it("5. identification succeeds -> no error banner, no picker, verified model card shown", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "IDENTIFIED",
      identified_model: {
        manufacturer: "Dell",
        model: "Latitude 5420",
      },
      confidence: 0.95,
      confidence_level: "HIGH",
      needs_confirmation: false,
      visual_clues: ["Dell logo on chassis", "Latitude 5420 regulatory label"],
    } as any);

    renderWithContext();

    const file = createMockFile();
    const input = screen.getByTestId("file-upload-input");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByTestId("verified-model-card")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("error-banner")).not.toBeInTheDocument();
    expect(screen.queryByTestId("model-picker")).not.toBeInTheDocument();
    expect(screen.getByText(/Dell Latitude 5420/i)).toBeInTheDocument();
  });

  it("6. removing all images after a failed attempt -> error and picker clear", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "UNKNOWN",
      identified_model: null,
      message: "Model could not be identified.",
    } as any);

    renderWithContext();

    const file = createMockFile();
    const input = screen.getByTestId("file-upload-input");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByTestId("error-banner")).toBeInTheDocument();
      expect(screen.getByTestId("model-picker")).toBeInTheDocument();
    });

    // Remove the only uploaded image
    const removeBtn = screen.getByTestId("remove-image-btn-0");
    fireEvent.click(removeBtn);

    expect(screen.queryByTestId("error-banner")).not.toBeInTheDocument();
    expect(screen.queryByTestId("model-picker")).not.toBeInTheDocument();
    expect(screen.queryByTestId("verified-model-card")).not.toBeInTheDocument();
  });

  it("7. picking a model manually -> proceeds correctly and shows confirmed model card", async () => {
    vi.mocked(api.identifyProduct).mockResolvedValueOnce({
      status: "UNKNOWN",
      identified_model: null,
      message: "Model could not be identified.",
    } as any);

    const onComplete = vi.fn();
    render(
      <LanguageProvider>
        <VisualInspectionStep
          initialData={emptyInitialData}
          onComplete={onComplete}
        />
      </LanguageProvider>
    );

    const file = createMockFile();
    const input = screen.getByTestId("file-upload-input");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByTestId("model-picker")).toBeInTheDocument();
    });

    // Select manual model option
    const modelOption = screen.getByTestId("catalog-model-option-latitude-5420");
    fireEvent.click(modelOption);

    // Picker closes, error clears, verified card is displayed
    expect(screen.queryByTestId("model-picker")).not.toBeInTheDocument();
    expect(screen.queryByTestId("error-banner")).not.toBeInTheDocument();
    expect(screen.getByTestId("verified-model-card")).toBeInTheDocument();
    expect(screen.getByText(/Dell Latitude 5420/i)).toBeInTheDocument();

    // Click Confirm & Continue
    const confirmBtn = screen.getByText(/Confirm & Continue/i);
    fireEvent.click(confirmBtn);

    expect(onComplete).toHaveBeenCalledWith(
      expect.objectContaining({
        identifiedProduct: expect.objectContaining({
          manufacturer: "Dell",
          model: "Latitude 5420",
          confirmed: true,
        }),
      })
    );
  });
});
