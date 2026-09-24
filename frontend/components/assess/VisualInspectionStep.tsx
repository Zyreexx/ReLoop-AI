"use client";

import React, { useState, useRef } from "react";
import { Upload, X, CheckCircle2, AlertCircle, Camera, Sparkles, RefreshCw, Eye } from "lucide-react";
import { MVP_SUPPORTED_MODELS, VisualInspectionData, VisualObservation } from "@/types/assessment";

interface VisualInspectionStepProps {
  initialData: VisualInspectionData;
  onComplete: (data: VisualInspectionData) => void;
}

export const VisualInspectionStep: React.FC<VisualInspectionStepProps> = ({
  initialData,
  onComplete,
}) => {
  const [images, setImages] = useState<string[]>(initialData.images || []);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(initialData.identifiedProduct.confirmed);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [identifiedProduct, setIdentifiedProduct] = useState(
    initialData.identifiedProduct || {
      manufacturer: "Dell",
      model: "Latitude 5420",
      confidence: 0.91,
      confirmed: false,
    }
  );

  const [visibleObservations, setVisibleObservations] = useState<VisualObservation[]>(
    initialData.visibleObservations || []
  );

  const [showModelPicker, setShowModelPicker] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);
    processFiles(files);
  };

  const processFiles = (files: File[]) => {
    setErrorMsg(null);
    const validFormats = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
    const newImages: string[] = [...images];

    for (const file of files) {
      if (!validFormats.includes(file.type)) {
        setErrorMsg("Invalid file format. Please upload JPG, PNG, or WEBP images.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setErrorMsg("File size too large. Maximum size is 10MB per image.");
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result && newImages.length < 3) {
          newImages.push(e.target.result as string);
          setImages([...newImages]);
          setAnalyzed(false); // Reset analysis on new image upload
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = (index: number) => {
    const updated = images.filter((_, i) => i !== index);
    setImages(updated);
    if (updated.length === 0) {
      setAnalyzed(false);
      setVisibleObservations([]);
    }
  };

  const runVisionAnalysis = async () => {
    if (images.length === 0) {
      setErrorMsg("Please upload at least 1 image of your device before analyzing.");
      return;
    }

    setAnalyzing(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/assessments/visual-inspection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ images }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Unable to analyze images.");
      }

      setIdentifiedProduct(data.identified_product);
      setVisibleObservations(data.visible_observations);
      setAnalyzed(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Unable to analyze these images right now. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmModel = () => {
    const updatedProduct = { ...identifiedProduct, confirmed: true };
    setIdentifiedProduct(updatedProduct);

    onComplete({
      images,
      identifiedProduct: updatedProduct,
      visibleObservations,
    });
  };

  const handleSelectCustomModel = (modelId: string) => {
    const found = MVP_SUPPORTED_MODELS.find((m) => m.id === modelId);
    if (found) {
      setIdentifiedProduct({
        manufacturer: found.manufacturer,
        model: found.model,
        confidence: 1.0,
        confirmed: true,
      });
    }
    setShowModelPicker(false);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20 mb-2 inline-block">
          VISUAL EVIDENCE
        </span>
        <h2 className="text-3xl font-bold text-[#1D1D1F] tracking-tight">
          1. Visual Inspection
        </h2>
        <p className="text-[#6E6E73] text-sm sm:text-base mt-1">
          Show us the device. We&apos;ll identify the product and inspect visible condition.
        </p>
      </div>

      {/* Non-negotiable technical rule disclaimer */}
      <div className="mb-8 p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs sm:text-sm flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">ReLoop Evidence Rule:</span>
          Photos are strictly used for product identification and visible surface inspection.
          Photos are <strong>never</strong> used to guess internal health of batteries, SSDs, RAM, or motherboard thermals.
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            type="button"
            onClick={runVisionAnalysis}
            className="text-xs font-semibold underline text-red-800 hover:text-red-950"
          >
            Try again
          </button>
        </div>
      )}

      {/* Photo Upload Slots */}
      <div className="apple-card p-6 sm:p-8 mb-8 bg-white">
        <h3 className="text-lg font-bold text-[#1D1D1F] mb-1">
          Upload Device Photos (2–3 recommended)
        </h3>
        <p className="text-xs text-[#6E6E73] mb-6">
          Suggested views: 1. Front / open laptop &nbsp;•&nbsp; 2. Underside / back label &nbsp;•&nbsp; 3. Ports / damaged area
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {/* Slot 1, 2, 3 */}
          {[0, 1, 2].map((idx) => {
            const imgSrc = images[idx];
            const slotLabels = ["1. Front / Open", "2. Underside", "3. Side / Ports"];

            return (
              <div
                key={idx}
                className="relative h-44 rounded-2xl border-2 border-dashed border-[#D2D2D7] bg-[#F5F5F7] hover:bg-[#FBFBFD] transition-all flex flex-col items-center justify-center p-3 text-center overflow-hidden group"
              >
                {imgSrc ? (
                  <>
                    <img
                      src={imgSrc}
                      alt={`Uploaded image ${idx + 1}`}
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      <button
                        type="button"
                        onClick={() => removeImage(idx)}
                        className="p-2 rounded-full bg-white text-[#FF3B30] hover:bg-red-50 transition-colors shadow-md"
                        aria-label="Remove image"
                      >
                        <X size={16} />
                      </button>
                    </div>
                    <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/60 text-white text-[10px] font-semibold backdrop-blur-sm">
                      {slotLabels[idx]}
                    </span>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-4 text-[#6E6E73] hover:text-[#0071E3]"
                  >
                    <Upload className="w-6 h-6 mb-2 text-[#86868B]" />
                    <span className="text-xs font-semibold text-[#1D1D1F] block">
                      {slotLabels[idx]}
                    </span>
                    <span className="text-[11px] text-[#86868B]">Click or drop photo</span>
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#E5E5E7]">
          <div className="flex items-center gap-2 text-xs text-[#6E6E73]">
            <Camera className="w-4 h-4 text-[#0071E3]" />
            <span>Supported: JPG, PNG, WEBP (Max 10MB each)</span>
          </div>

          <button
            type="button"
            disabled={images.length === 0 || analyzing}
            onClick={runVisionAnalysis}
            className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
              images.length > 0 && !analyzing
                ? "bg-[#0071E3] hover:bg-[#0077ED] text-white shadow-xs"
                : "bg-[#E8E8ED] text-[#86868B] cursor-not-allowed"
            }`}
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Analyzing device photos...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>{analyzed ? "Re-analyze Photos" : "Run Vision AI Inspection"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress Bar during analysis */}
      {analyzing && (
        <div className="mb-8 p-6 rounded-2xl bg-white border border-[#E5E5E7] text-center">
          <p className="text-sm font-semibold text-[#1D1D1F] mb-3">
            Analyzing your device photos...
          </p>
          <div className="w-full bg-[#E5E5E7] h-2 rounded-full overflow-hidden max-w-md mx-auto">
            <div className="bg-[#0071E3] h-full animate-pulse w-3/4 rounded-full" />
          </div>
          <p className="text-xs text-[#6E6E73] mt-2">
            Detecting laptop manufacturer, model, and visible surface conditions
          </p>
        </div>
      )}

      {/* Vision AI Output Results */}
      {analyzed && !analyzing && (
        <div className="space-y-6">
          {/* Model Confirmation Box */}
          <div className="apple-card p-6 bg-white border-l-4 border-l-[#0071E3]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#0071E3] block mb-1">
                  MODEL IDENTIFICATION
                </span>
                <h4 className="text-xl font-bold text-[#1D1D1F]">
                  {identifiedProduct.manufacturer} {identifiedProduct.model}
                </h4>
                <p className="text-xs text-[#6E6E73] mt-1">
                  Model identified with {Math.round(identifiedProduct.confidence * 100)}% confidence
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setShowModelPicker(true)}
                  className="px-4 py-2 rounded-full border border-[#D2D2D7] text-xs font-semibold text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors cursor-pointer"
                >
                  Change model
                </button>
                <button
                  type="button"
                  onClick={handleConfirmModel}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#34C759] hover:bg-[#2FB34F] text-white text-xs font-semibold transition-all shadow-xs cursor-pointer"
                >
                  <CheckCircle2 size={15} />
                  <span>Confirm Device</span>
                </button>
              </div>
            </div>
          </div>

          {/* Model Picker Modal */}
          {showModelPicker && (
            <div className="p-4 rounded-2xl bg-[#F5F5F7] border border-[#D2D2D7]">
              <div className="flex items-center justify-between mb-3">
                <h5 className="text-xs font-bold uppercase tracking-wider text-[#1D1D1F]">
                  Select Supported MVP Laptop Model
                </h5>
                <button
                  type="button"
                  onClick={() => setShowModelPicker(false)}
                  className="text-xs text-[#6E6E73] hover:text-[#1D1D1F]"
                >
                  Close
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {MVP_SUPPORTED_MODELS.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleSelectCustomModel(m.id)}
                    className="p-3 rounded-xl bg-white border border-[#E5E5E7] hover:border-[#0071E3] text-left transition-all cursor-pointer"
                  >
                    <span className="text-xs font-bold text-[#1D1D1F] block">{m.model}</span>
                    <span className="text-[11px] text-[#6E6E73]">{m.manufacturer} • {m.category}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Visible Observations Grid */}
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider text-[#6E6E73] mb-4">
              Detected Visible Observations
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {visibleObservations.map((obs) => (
                <div
                  key={obs.id}
                  className="p-4 rounded-2xl bg-white border border-[#E5E5E7] shadow-2xs"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold capitalize text-[#1D1D1F]">
                      {obs.component}
                    </span>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-bold">
                      VISUAL
                    </span>
                  </div>
                  <p className="text-xs text-[#1D1D1F] font-semibold mb-1">
                    {obs.observation}
                  </p>
                  <span className="text-[11px] text-[#86868B] block">
                    Based on visual inspection
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Continue CTA */}
          <div className="pt-6 flex justify-end">
            <button
              type="button"
              onClick={handleConfirmModel}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer"
            >
              <span>Continue to Diagnostics →</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
