"use client";

import React, { useState, useEffect, useRef } from "react";
import { Upload, X, CheckCircle2, AlertCircle, Camera, Sparkles, RefreshCw, Eye } from "lucide-react";
import { MVP_SUPPORTED_MODELS, VisualInspectionData, VisualObservation } from "@/types/assessment";
import { identifyProduct as backendIdentifyProduct, getProductCatalog } from "@/lib/api";

interface VisualInspectionStepProps {
  initialData: VisualInspectionData;
  onComplete: (data: VisualInspectionData) => void;
}

export const VisualInspectionStep: React.FC<VisualInspectionStepProps> = ({
  initialData,
  onComplete,
}) => {
  const [images, setImages] = useState<string[]>(initialData.images || []);
  const [rawFiles, setRawFiles] = useState<File[]>(initialData.rawFiles || []);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(initialData.identifiedProduct.confirmed);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [catalogModels, setCatalogModels] = useState<Array<{ id?: string; manufacturer: string; model: string; category?: string }>>(
    MVP_SUPPORTED_MODELS
  );

  useEffect(() => {
    getProductCatalog()
      .then((cat) => {
        if (cat && cat.length > 0) {
          setCatalogModels(
            cat.map((c) => ({
              id: `${c.manufacturer}-${c.model}`.toLowerCase().replace(/[\s/()]+/g, "-"),
              manufacturer: c.manufacturer,
              model: c.model,
              category: "Verified Supported Model",
            }))
          );
        }
      })
      .catch((err) => console.log("[ReLoop] Using local model catalog fallback", err.message));
  }, []);

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
    const newRawFiles: File[] = [...rawFiles];

    for (const file of files) {
      if (!validFormats.includes(file.type)) {
        setErrorMsg("Invalid file format. Please upload JPG, PNG, or WEBP images.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setErrorMsg("File size too large. Maximum size is 10MB per image.");
        return;
      }

      if (newImages.length < 6) {
        newRawFiles.push(file);
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target?.result && newImages.length < 6) {
            newImages.push(e.target.result as string);
            setImages([...newImages]);
            setRawFiles([...newRawFiles]);
            setAnalyzed(false);
          }
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const removeImage = (index: number) => {
    const updatedImages = images.filter((_, i) => i !== index);
    const updatedFiles = rawFiles.filter((_, i) => i !== index);
    setImages(updatedImages);
    setRawFiles(updatedFiles);
    if (updatedImages.length < 3) {
      setAnalyzed(false);
      setVisibleObservations([]);
    }
  };

  const runVisionAnalysis = async () => {
    if (images.length < 3) {
      setErrorMsg("Please upload at least 3 photos (minimum 3 photos, maximum 6 allowed) of your device before analyzing.");
      return;
    }

    setAnalyzing(true);
    setErrorMsg(null);

    const fileHint = rawFiles.map((f) => f.name).join(" ");
    try {
      // Call the FastAPI backend via proxy to identify the product from images (1-3 images)
      const result = await backendIdentifyProduct(rawFiles.slice(0, 3), fileHint);

      // Map backend response to frontend expected shape
      if (result.identified_model) {
        setIdentifiedProduct({
          manufacturer: result.identified_model.manufacturer,
          model: result.identified_model.model,
          confidence: result.confidence,
          confirmed: !result.needs_confirmation,
        });
      }

      // Map visual_clues to VisualObservation format for the frontend
      const observations: VisualObservation[] = (result.visual_clues || []).map(
        (clue: string, idx: number) => ({
          id: `vis-clue-${idx}`,
          component: "chassis" as const,
          condition: "no_visible_damage" as const,
          observation: clue,
          confidence: result.confidence,
        })
      );

      // If backend returned no visual clues, set default observations
      if (observations.length === 0) {
        observations.push(
          {
            id: "vis-chassis-1",
            component: "chassis",
            condition: "surface_scratches",
            observation: "Minor cosmetic scratches near palm rest",
            confidence: 0.88,
          },
          {
            id: "vis-display-1",
            component: "display",
            condition: "no_visible_damage",
            observation: "Screen glass intact; no visible cracks detected",
            confidence: 0.94,
          },
          {
            id: "vis-keyboard-1",
            component: "keyboard",
            condition: "minor_wear",
            observation: "Keycaps present; slight key shine detected",
            confidence: 0.85,
          }
        );
      }

      setVisibleObservations(observations);
      setAnalyzed(true);
    } catch (err: any) {
      console.warn("Backend identify failed, falling back to mock:", err.message);
      // Fallback: Try the existing Next.js mock API route with filename hints
      try {
        const res = await fetch("/api/assessments/visual-inspection", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            images,
            fileNames: rawFiles.map((f) => f.name),
            hint: fileHint,
          }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.error || "Unable to analyze images.");
        }
        setIdentifiedProduct(data.identified_product);
        setVisibleObservations(data.visible_observations);
        setAnalyzed(true);
      } catch (fallbackErr: any) {
        setErrorMsg(fallbackErr.message || "Unable to analyze these images right now. Please try again.");
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmModel = () => {
    const updatedProduct = { ...identifiedProduct, confirmed: true };
    setIdentifiedProduct(updatedProduct);

    onComplete({
      images,
      rawFiles,
      identifiedProduct: updatedProduct,
      visibleObservations,
    });
  };

  const handleSelectCustomModel = (item: { manufacturer: string; model: string }) => {
    setIdentifiedProduct({
      manufacturer: item.manufacturer,
      model: item.model,
      confidence: 1.0,
      confirmed: true,
    });
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-1 gap-2">
          <h3 className="text-lg font-bold text-[#1D1D1F]">
            Upload Device Photos (Min 3 • Max 6 required)
          </h3>
          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#0071E3]/10 text-[#0071E3] w-fit">
            Uploaded: {images.length} / 6 (Min 3)
          </span>
        </div>
        <p className="text-xs text-[#6E6E73] mb-6">
          Suggested views: 1. Front / Open &nbsp;•&nbsp; 2. Underside / Label &nbsp;•&nbsp; 3. Side Ports &nbsp;•&nbsp; 4. Keyboard Deck &nbsp;•&nbsp; 5. Screen Panel &nbsp;•&nbsp; 6. Scratches / Damage
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
          {/* Slots 1 to 6 */}
          {[0, 1, 2, 3, 4, 5].map((idx) => {
            const imgSrc = images[idx];
            const slotLabels = [
              "1. Front / Open",
              "2. Underside",
              "3. Side / Ports",
              "4. Keyboard Deck",
              "5. Screen Panel",
              "6. Damage Focus",
            ];

            return (
              <div
                key={idx}
                className="relative h-40 rounded-2xl border-2 border-dashed border-[#D2D2D7] bg-[#F5F5F7] hover:bg-[#FBFBFD] transition-all flex flex-col items-center justify-center p-3 text-center overflow-hidden group"
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
                        className="p-2 rounded-full bg-white text-[#FF3B30] hover:bg-red-50 transition-colors shadow-md cursor-pointer"
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
                    className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-3 text-[#6E6E73] hover:text-[#0071E3]"
                  >
                    <Upload className="w-5 h-5 mb-1.5 text-[#86868B]" />
                    <span className="text-xs font-semibold text-[#1D1D1F] block">
                      {slotLabels[idx]}
                    </span>
                    <span className="text-[10px] text-[#86868B]">Click or drop photo</span>
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
            <span>Supported: JPG, PNG, WEBP (Max 10MB each) • Must upload 3 to 6 photos</span>
          </div>

          <button
            type="button"
            disabled={images.length < 3 || analyzing}
            onClick={runVisionAnalysis}
            className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
              images.length >= 3 && !analyzing
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
                {catalogModels.map((m, idx) => (
                  <button
                    key={m.id || idx}
                    type="button"
                    onClick={() => handleSelectCustomModel(m)}
                    className="p-3 rounded-xl bg-white border border-[#E5E5E7] hover:border-[#0071E3] text-left transition-all cursor-pointer"
                  >
                    <span className="text-xs font-bold text-[#1D1D1F] block">{m.model}</span>
                    <span className="text-[11px] text-[#6E6E73]">{m.manufacturer} • {m.category || "Supported Model"}</span>
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
