"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Upload,
  X,
  CheckCircle2,
  AlertCircle,
  Camera,
  Sparkles,
  RefreshCw,
  Eye,
  Laptop,
  Search,
} from "lucide-react";
import { MVP_SUPPORTED_MODELS, VisualInspectionData, VisualObservation } from "@/types/assessment";
import { identifyProduct as backendIdentifyProduct, getProductCatalog } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

interface VisualInspectionStepProps {
  initialData: VisualInspectionData;
  onComplete: (data: VisualInspectionData) => void;
}

export const VisualInspectionStep: React.FC<VisualInspectionStepProps> = ({
  initialData,
  onComplete,
}) => {
  const { t } = useLanguage();
  const [images, setImages] = useState<string[]>(initialData.images || []);
  const [rawFiles, setRawFiles] = useState<File[]>(initialData.rawFiles || []);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(
    Boolean(initialData.identifiedProduct?.model && initialData.identifiedProduct.confirmed)
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [scanStatusText, setScanStatusText] = useState("Analyzing laptop with Gemini Vision...");

  // Stored custom key if provided in localStorage or environment
  const [customApiKey, setCustomApiKey] = useState<string>("");

  const [catalogModels, setCatalogModels] = useState<
    Array<{ id?: string; manufacturer: string; model: string; category?: string }>
  >(MVP_SUPPORTED_MODELS);

  const [identifiedProduct, setIdentifiedProduct] = useState(
    initialData.identifiedProduct?.model
      ? initialData.identifiedProduct
      : {
          manufacturer: "",
          model: "",
          confidence: 0,
          confirmed: false,
          visible_label_text: null as string | null,
        }
  );

  const [visibleObservations, setVisibleObservations] = useState<VisualObservation[]>(
    initialData.visibleObservations || []
  );

  const [showModelPicker, setShowModelPicker] = useState(false);
  const [modelSearchQuery, setModelSearchQuery] = useState("");
  const [customBrand, setCustomBrand] = useState("");
  const [customModel, setCustomModel] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load stored custom Gemini key if any
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedKey = localStorage.getItem("reloop_gemini_api_key");
      if (storedKey) {
        setCustomApiKey(storedKey);
      }
    }
  }, []);

  // Load product catalog for manual override fallback
  useEffect(() => {
    getProductCatalog()
      .then((cat) => {
        if (cat && cat.length > 0) {
          setCatalogModels(
            cat.map((c) => ({
              id: `${c.manufacturer}-${c.model}`.toLowerCase().replace(/[\s/()]+/g, "-"),
              manufacturer: c.manufacturer,
              model: c.model,
              category: "Verified Catalog Model",
            }))
          );
        }
      })
      .catch((err) => console.log("[ReLoop] Using local model catalog fallback", err.message));
  }, []);


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);
    processFiles(files);
  };

  const processFiles = (files: File[]) => {
    setErrorMsg(null);
    const validFormats = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
    const addedFiles: File[] = [];

    for (const file of files) {
      if (!validFormats.includes(file.type)) {
        setErrorMsg("Invalid file format. Please upload JPG, PNG, or WEBP images.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setErrorMsg("File size too large. Maximum size is 10MB per image.");
        return;
      }
      addedFiles.push(file);
    }

    if (addedFiles.length === 0) return;

    // Load data URLs
    const readPromises = addedFiles.map(
      (file) =>
        new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.readAsDataURL(file);
        })
    );

    Promise.all(readPromises).then((newUrls) => {
      const combinedImages = [...images, ...newUrls].slice(0, 6);
      const combinedRawFiles = [...rawFiles, ...addedFiles].slice(0, 6);
      setImages(combinedImages);
      setRawFiles(combinedRawFiles);
      setAnalyzed(false);

      // Auto-trigger Gemini model detection upon upload
      triggerVisionDetection(combinedRawFiles, combinedImages);
    });
  };

  const removeImage = (index: number) => {
    const updatedImages = images.filter((_, i) => i !== index);
    const updatedFiles = rawFiles.filter((_, i) => i !== index);
    setImages(updatedImages);
    setRawFiles(updatedFiles);
    if (updatedImages.length === 0) {
      setAnalyzed(false);
      setVisibleObservations([]);
      setIdentifiedProduct({
        manufacturer: "",
        model: "",
        confidence: 0,
        confirmed: false,
        visible_label_text: null,
      });
    }
  };

  const triggerVisionDetection = async (filesToUse: File[], imagesToUse: string[]) => {
    if (filesToUse.length === 0) return;
    setAnalyzing(true);
    setErrorMsg(null);
    setScanStatusText("Uploading image to Gemini Vision API...");

    const fileHint = filesToUse.map((f) => f.name).join(" ");

    // Rotate status messages during AI inference
    const statusTimer = setInterval(() => {
      setScanStatusText((prev) => {
        if (prev.includes("Uploading")) return "Gemini AI scanning chassis, logos, and keyboard markings...";
        if (prev.includes("chassis")) return "Identifying laptop manufacturer and model number...";
        return "Finalizing hardware visual inspection...";
      });
    }, 1100);

    try {
      // 1. Try FastAPI backend proxy with Gemini client
      const activeKey = customApiKey || undefined;
      const result = await backendIdentifyProduct(
        filesToUse.slice(0, 3),
        fileHint,
        undefined,
        undefined,
        activeKey
      );

      clearInterval(statusTimer);

      if (result.status === "IDENTIFIED" && result.identified_model) {
        setIdentifiedProduct({
          manufacturer: result.identified_model.manufacturer,
          model: result.identified_model.model,
          confidence: result.confidence || 0.92,
          confirmed: !result.needs_confirmation,
          visible_label_text: result.visible_label_text || null,
        });

        const observations: VisualObservation[] = (result.visual_clues || []).map(
          (clue: string, idx: number) => ({
            id: `vis-gemini-${idx}`,
            component: "chassis" as const,
            condition: "no_visible_damage" as const,
            observation: clue,
            confidence: result.confidence || 0.9,
          })
        );

        if (observations.length === 0) {
          observations.push({
            id: "vis-obs-1",
            component: "chassis",
            condition: "no_visible_damage",
            observation: `Identified ${result.identified_model.manufacturer} ${result.identified_model.model} via optical design cues`,
            confidence: result.confidence || 0.9,
          });
        }

        setVisibleObservations(observations);
        setAnalyzed(true);
      } else if (result.status === "AI_UNAVAILABLE") {
        setShowModelPicker(true);
        setErrorMsg("AI identification is temporarily unavailable. Please select your model manually to continue.");
        setIdentifiedProduct({
          manufacturer: "",
          model: "",
          confidence: 0,
          confirmed: false,
          visible_label_text: null,
        });
        setVisibleObservations([]);
        setAnalyzed(false);
      } else if (result.status === "INVALID_EVIDENCE") {
        setShowModelPicker(true);
        setErrorMsg("Unable to analyze these photos. Please provide clearer, well-lit device photos or select your model manually.");
        setIdentifiedProduct({
          manufacturer: "",
          model: "",
          confidence: 0,
          confirmed: false,
          visible_label_text: null,
        });
        setVisibleObservations([]);
        setAnalyzed(false);
      } else {
        // UNKNOWN or unrecognized device
        setShowModelPicker(true);
        setErrorMsg("Model could not be identified. Your device may not be in the currently supported catalog. Please select your model manually to continue.");
        setIdentifiedProduct({
          manufacturer: "",
          model: "",
          confidence: 0,
          confirmed: false,
          visible_label_text: null,
        });
        setVisibleObservations([]);
        setAnalyzed(false);
      }
    } catch (backendErr: any) {
      console.warn("Backend identify error:", backendErr?.message || backendErr);
      clearInterval(statusTimer);
      setShowModelPicker(true);
      setErrorMsg("AI identification is temporarily unavailable. Please select your model manually to continue.");
      setIdentifiedProduct({
        manufacturer: "",
        model: "",
        confidence: 0,
        confirmed: false,
        visible_label_text: null,
      });
      setVisibleObservations([]);
      setAnalyzed(false);
    } finally {
      clearInterval(statusTimer);
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
    const updated = {
      manufacturer: item.manufacturer,
      model: item.model,
      confidence: 1.0,
      confirmed: true,
      visible_label_text: `Manually selected: ${item.manufacturer} ${item.model}`,
    };
    setIdentifiedProduct(updated);

    // Provide baseline observation if none exist so user can proceed
    if (visibleObservations.length === 0) {
      setVisibleObservations([
        {
          id: "vis-manual-1",
          component: "chassis",
          condition: "no_visible_damage",
          observation: `Manually verified ${item.manufacturer} ${item.model} chassis profile`,
          confidence: 1.0,
        },
      ]);
    }

    setShowModelPicker(false);
    setAnalyzed(true);
    setErrorMsg(null);
  };

  const filteredCatalog = catalogModels.filter((m) => {
    if (!modelSearchQuery.trim()) return true;
    const q = modelSearchQuery.toLowerCase().trim();
    return (
      m.manufacturer.toLowerCase().includes(q) ||
      m.model.toLowerCase().includes(q) ||
      (m.category && m.category.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header with Gemini Badge & Key Config */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20">
              {t("visual.stepBadge", "STEP 1: VISUAL INSPECTION")}
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              <Sparkles className="w-3 h-3 text-emerald-600 animate-pulse" />
              {t("visual.geminiBadge", "Gemini Vision AI Powered")}
            </span>
          </div>
          <h2 className="text-3xl font-bold text-[#1D1D1F] tracking-tight">
            {t("visual.title", "Laptop Model Detection")}
          </h2>
          <p className="text-[#6E6E73] text-sm sm:text-base mt-1">
            {t("visual.subtitle", "Upload a photo of your laptop. Gemini Vision AI will automatically detect the manufacturer, exact model name, and physical characteristics.")}
          </p>
        </div>

      </div>

      {/* Non-negotiable technical rule disclaimer */}
      <div className="mb-6 p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs sm:text-sm flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">{t("visual.ruleTitle", "Hardware Verification Rule:")}</span>
          {t("visual.ruleDesc", "Gemini Vision identifies laptop model and external casing condition from your photos. Internal battery and SSD health are gathered in Step 2 via diagnostics telemetry.")}
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600 dark:text-red-400" />
            <span>{errorMsg}</span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={() => {
                setShowModelPicker(true);
                setTimeout(() => {
                  document.getElementById("manual-model-picker")?.scrollIntoView({ behavior: "smooth" });
                }, 50);
              }}
              className="px-3.5 py-1.5 rounded-full bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              Select Model Manually ↓
            </button>
            <button
              type="button"
              onClick={() => triggerVisionDetection(rawFiles, images)}
              className="text-xs font-semibold underline text-red-800 hover:text-red-950 dark:text-red-200 cursor-pointer"
            >
              {t("visual.retry", "Retry Detection")}
            </button>
          </div>
        </div>
      )}

      {/* Photo Upload Slots Card */}
      <div className="apple-card p-6 sm:p-8 mb-8 bg-white border border-[#E5E5E7] shadow-sm rounded-3xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-2 gap-2">
          <div>
            <h3 className="text-lg font-bold text-[#1D1D1F] flex items-center gap-2">
              <Laptop className="w-5 h-5 text-[#0071E3]" />
              {t("visual.uploadTitle", "Upload Laptop Photos")}
            </h3>
            <p className="text-xs text-[#6E6E73] mt-0.5">
              {t("visual.uploadSubtitle", "Upload 1 or more photos (e.g. keyboard view, top lid, or bottom model label). Gemini will detect your laptop automatically!")}
            </p>
          </div>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#0071E3]/10 text-[#0071E3] w-fit">
            {t("visual.uploadedCount", "Uploaded")}: {images.length} / 6
          </span>
        </div>

        {/* Upload Slots Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 my-6">
          {[0, 1, 2, 3, 4, 5].map((idx) => {
            const imgSrc = images[idx];
            const slotLabels = [
              t("visual.slot1", "1. Full Laptop / Keyboard"),
              t("visual.slot2", "2. Bottom Label / Sticker"),
              t("visual.slot3", "3. Top Lid / Brand Logo"),
              t("visual.slot4", "4. Side Ports & Edge"),
              t("visual.slot5", "5. Display / Bezel"),
              t("visual.slot6", "6. Any Visible Scratches"),
            ];

            return (
              <div
                key={idx}
                className="relative h-44 rounded-2xl border-2 border-dashed border-[#D2D2D7] bg-[#F5F5F7] hover:bg-[#FBFBFD] transition-all flex flex-col items-center justify-center p-3 text-center overflow-hidden group shadow-2xs"
              >
                {imgSrc ? (
                  <>
                    <img
                      src={imgSrc}
                      alt={`Laptop photo ${idx + 1}`}
                      className="absolute inset-0 w-full h-full object-cover"
                    />

                    {/* Scanning radar sweep animation when analyzing */}
                    {analyzing && (
                      <div className="absolute inset-0 bg-[#0071E3]/20 backdrop-blur-[1px] flex flex-col items-center justify-center pointer-events-none">
                        <div className="w-full h-0.5 bg-[#0071E3] shadow-[0_0_10px_#0071E3] animate-[bounce_2s_infinite]" />
                        <span className="text-[10px] font-mono text-white bg-black/70 px-2 py-0.5 rounded-full mt-2 font-semibold">
                          SCANNING
                        </span>
                      </div>
                    )}

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
                    <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-white text-[10px] font-semibold backdrop-blur-xs">
                      {slotLabels[idx]}
                    </span>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-3 text-[#6E6E73] hover:text-[#0071E3] transition-colors"
                  >
                    <div className="w-10 h-10 rounded-full bg-white shadow-2xs border border-[#E5E5E7] flex items-center justify-center mb-2 group-hover:border-[#0071E3]">
                      <Upload className="w-4 h-4 text-[#0071E3]" />
                    </div>
                    <span className="text-xs font-semibold text-[#1D1D1F] block">
                      {slotLabels[idx]}
                    </span>
                    <span className="text-[10px] text-[#86868B] mt-0.5">{t("visual.clickToUpload", "Click to upload photo")}</span>
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

        {/* Footer Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#E5E5E7]">
          <div className="flex items-center gap-2 text-xs text-[#6E6E73]">
            <Camera className="w-4 h-4 text-[#0071E3]" />
            <span>{t("visual.supportedFormats", "Supported: JPG, PNG, WEBP (Max 10MB each) • 1 to 6 photos")}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setShowModelPicker((prev) => !prev);
                setTimeout(() => {
                  document.getElementById("manual-model-picker")?.scrollIntoView({ behavior: "smooth" });
                }, 50);
              }}
              className="px-4 py-2.5 rounded-full border border-[#D2D2D7] dark:border-slate-700 text-xs font-semibold text-[#1D1D1F] dark:text-slate-200 hover:bg-[#F5F5F7] dark:hover:bg-slate-800 transition-all cursor-pointer"
            >
              {showModelPicker ? "Hide Manual Selection" : "Select Model Manually"}
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2.5 rounded-full border border-[#D2D2D7] dark:border-slate-700 text-xs font-semibold text-[#1D1D1F] dark:text-slate-200 hover:bg-[#F5F5F7] dark:hover:bg-slate-800 transition-all cursor-pointer"
            >
              {t("visual.addPhoto", "Add Photo")}
            </button>
            <button
              type="button"
              disabled={images.length === 0 || analyzing}
              onClick={() => triggerVisionDetection(rawFiles, images)}
              className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                images.length > 0 && !analyzing
                  ? "bg-[#0071E3] hover:bg-[#0077ED] text-white shadow-sm hover:shadow"
                  : "bg-[#E8E8ED] text-[#86868B] cursor-not-allowed"
              }`}
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>{t("visual.detecting", "Detecting Model...")}</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>{analyzed ? t("visual.redetect", "Re-detect with Gemini") : t("visual.detectBtn", "Detect Model with Gemini AI")}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Manual Model Picker Section — Rendered prominently whenever showModelPicker is true */}
      {showModelPicker && (
        <div id="manual-model-picker" className="apple-card p-6 sm:p-8 mb-8 bg-[#F5F5F7] dark:bg-slate-900 border-2 border-[#0071E3]/40 rounded-3xl shadow-md animate-in fade-in slide-in-from-top-3 duration-300">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono font-bold uppercase px-2.5 py-0.5 rounded-full bg-[#0071E3] text-white">
                  MANUAL SELECTION
                </span>
                <span className="text-xs text-[#6E6E73] dark:text-slate-400">
                  Select your verified laptop model or type your model below
                </span>
              </div>
              <h4 className="text-lg font-bold text-[#1D1D1F] dark:text-white">
                {t("visual.pickerTitle", "Select or Adjust Laptop Model")}
              </h4>
            </div>
            <button
              type="button"
              onClick={() => setShowModelPicker(false)}
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white dark:bg-slate-800 text-[#6E6E73] dark:text-slate-300 hover:text-[#1D1D1F] border border-[#E5E5E7] dark:border-slate-700 shadow-2xs cursor-pointer"
            >
              {t("visual.pickerClose", "Close")}
            </button>
          </div>

          {/* Search bar */}
          <div className="relative mb-4">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-gray-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search by brand or model (e.g. ThinkPad, MacBook, Latitude, EliteBook)..."
              value={modelSearchQuery}
              onChange={(e) => setModelSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-[#E5E5E7] dark:border-slate-700 text-sm text-[#1D1D1F] dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
            />
          </div>

          {/* Catalog grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            {filteredCatalog.map((m, idx) => (
              <button
                key={m.id || idx}
                type="button"
                onClick={() => handleSelectCustomModel(m)}
                className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-[#E5E5E7] dark:border-slate-700 hover:border-[#0071E3] hover:shadow-md text-left transition-all cursor-pointer flex items-center justify-between group"
              >
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-[#0071E3]/10 text-[#0071E3] dark:bg-[#0071E3]/20 dark:text-blue-400 inline-block mb-1">
                    {m.manufacturer}
                  </span>
                  <span className="text-sm font-bold text-[#1D1D1F] dark:text-white block group-hover:text-[#0071E3] transition-colors">
                    {m.model}
                  </span>
                  <span className="text-[11px] text-[#6E6E73] dark:text-slate-400">
                    {m.category || "Supported Model"}
                  </span>
                </div>
                <div className="w-8 h-8 rounded-full bg-[#F5F5F7] dark:bg-slate-700 group-hover:bg-[#0071E3] group-hover:text-white flex items-center justify-center text-[#0071E3] dark:text-slate-200 transition-all font-bold">
                  →
                </div>
              </button>
            ))}
          </div>

          {/* Custom Model Direct Input */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-[#E5E5E7] dark:border-slate-700">
            <span className="text-xs font-bold text-[#1D1D1F] dark:text-white block mb-1">
              Can&apos;t find your laptop in the catalog? Enter it manually:
            </span>
            <div className="flex flex-col sm:flex-row gap-2 mt-2">
              <input
                type="text"
                placeholder="Brand / Manufacturer (e.g. Asus, Acer, Dell)"
                value={customBrand}
                onChange={(e) => setCustomBrand(e.target.value)}
                className="flex-1 px-3.5 py-2.5 rounded-xl bg-[#F5F5F7] dark:bg-slate-900 border border-[#E5E5E7] dark:border-slate-700 text-xs text-[#1D1D1F] dark:text-white focus:outline-none focus:ring-1 focus:ring-[#0071E3]"
              />
              <input
                type="text"
                placeholder="Model Name (e.g. ZenBook 14, Swift 3)"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
                className="flex-1 px-3.5 py-2.5 rounded-xl bg-[#F5F5F7] dark:bg-slate-900 border border-[#E5E5E7] dark:border-slate-700 text-xs text-[#1D1D1F] dark:text-white focus:outline-none focus:ring-1 focus:ring-[#0071E3]"
              />
              <button
                type="button"
                disabled={!customBrand.trim() || !customModel.trim()}
                onClick={() => handleSelectCustomModel({ manufacturer: customBrand.trim(), model: customModel.trim() })}
                className="px-5 py-2.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] disabled:bg-gray-300 dark:disabled:bg-slate-700 text-white text-xs font-bold transition-all cursor-pointer disabled:cursor-not-allowed shrink-0"
              >
                Set Model
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Card during Gemini Analysis */}
      {analyzing && (
        <div className="mb-8 p-6 rounded-3xl bg-linear-to-b from-[#0071E3]/5 to-transparent border border-[#0071E3]/20 text-center animate-in fade-in duration-300">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#0071E3]/10 text-[#0071E3] mb-3">
            <Sparkles className="w-6 h-6 animate-spin" />
          </div>
          <p className="text-base font-bold text-[#1D1D1F] mb-1">
            {scanStatusText}
          </p>
          <div className="w-full bg-[#E5E5E7] h-2 rounded-full overflow-hidden max-w-md mx-auto my-3">
            <div className="bg-linear-to-r from-[#0071E3] to-[#34C759] h-full animate-pulse w-3/4 rounded-full" />
          </div>
          <p className="text-xs text-[#6E6E73]">
            {t("visual.analyzingDesc", "Using Google Gemini multimodal vision to extract brand badges, model markings, and port configuration")}
          </p>
        </div>
      )}

      {/* Gemini AI Identified Model Results */}
      {analyzed && !analyzing && identifiedProduct.model && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-400">
          {/* Detected Model Hero Card */}
          <div className="apple-card p-6 sm:p-8 bg-white border border-[#E5E5E7] rounded-3xl shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-linear-to-bl from-[#0071E3]/10 via-[#34C759]/5 to-transparent rounded-bl-full pointer-events-none" />

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#0071E3] text-white">
                    {identifiedProduct.manufacturer || "LAPTOP"}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    {Math.round((identifiedProduct.confidence || 0.9) * 100)}% {t("visual.matchConfidence", "Match Confidence")}
                  </span>
                </div>

                <div>
                  <span className="text-xs text-[#86868B] uppercase tracking-wider font-semibold block">
                    {t("visual.detectedModelLabel", "Detected Model Name")}
                  </span>
                  <h4 className="text-2xl sm:text-3xl font-extrabold text-[#1D1D1F] tracking-tight">
                    {identifiedProduct.manufacturer} {identifiedProduct.model}
                  </h4>
                </div>

                {identifiedProduct.visible_label_text && (
                  <p className="text-xs text-[#6E6E73] bg-[#F5F5F7] px-3 py-1.5 rounded-lg inline-block font-mono">
                    {t("visual.foundOnLabel", "Found on label:")} &quot;{identifiedProduct.visible_label_text}&quot;
                  </p>
                )}
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <button
                  type="button"
                  onClick={() => setShowModelPicker(true)}
                  className="px-4 py-2.5 rounded-full border border-[#D2D2D7] text-xs font-semibold text-[#1D1D1F] hover:bg-[#F5F5F7] transition-all cursor-pointer"
                >
                  {t("visual.changeModel", "Change Model")}
                </button>
                <button
                  type="button"
                  onClick={handleConfirmModel}
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#34C759] hover:bg-[#2FB34F] text-white text-xs font-bold transition-all shadow-sm hover:shadow cursor-pointer"
                >
                  <CheckCircle2 size={16} />
                  <span>{t("visual.confirmContinue", "Confirm & Continue")}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Visible Observations Grid */}
          {visibleObservations.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#6E6E73] mb-3 flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-[#0071E3]" />
                {t("visual.observationsTitle", "Gemini Vision Observations")}
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {visibleObservations.map((obs) => (
                  <div
                    key={obs.id}
                    className="p-4 rounded-2xl bg-white border border-[#E5E5E7] shadow-2xs hover:border-[#D2D2D7] transition-all"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold capitalize text-[#1D1D1F]">
                        {obs.component}
                      </span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-[#0071E3] border border-blue-200 font-bold">
                        OPTICAL
                      </span>
                    </div>
                    <p className="text-xs text-[#1D1D1F] font-medium leading-relaxed">
                      {obs.observation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Continue CTA */}
          <div className="pt-6 flex justify-end">
            <button
              type="button"
              onClick={handleConfirmModel}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer"
            >
              <span>{t("visual.continueToDiag", "Continue to Diagnostics Telemetry →")}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
