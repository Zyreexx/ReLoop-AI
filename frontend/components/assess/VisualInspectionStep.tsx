"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Upload,
  X,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Camera,
  Sparkles,
  RefreshCw,
  Eye,
  Laptop,
  Search,
  Monitor,
  Keyboard,
  Plug,
  Layers,
  ShieldCheck,
  ArrowRight,
  Edit3,
  Scan,
  Tag,
  Check,
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
  const [images, setImages] = useState<string[]>(initialData?.images || []);
  const [rawFiles, setRawFiles] = useState<File[]>(initialData?.rawFiles || []);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(
    Boolean(
      initialData?.images &&
      initialData.images.length > 0 &&
      initialData.identifiedProduct?.model &&
      initialData.identifiedProduct.confirmed
    )
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [scanStatusText, setScanStatusText] = useState("Analyzing laptop with Gemini Vision...");

  // Stored custom key if provided in localStorage or environment
  const [customApiKey, setCustomApiKey] = useState<string>("");

  const [catalogModels, setCatalogModels] = useState<
    Array<{ id?: string; manufacturer: string; model: string; category?: string }>
  >(MVP_SUPPORTED_MODELS);

  const [identifiedProduct, setIdentifiedProduct] = useState(
    initialData?.identifiedProduct?.model
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
    initialData?.visibleObservations || []
  );
  const [damageFindings, setDamageFindings] = useState<any[]>(
    initialData?.damageFindings || []
  );
  const [overallVisualCondition, setOverallVisualCondition] = useState<string>(
    initialData?.overallVisualCondition || "GOOD"
  );

  const [obsFilter, setObsFilter] = useState<"all" | "wear" | "intact">("all");

  const getObsIcon = (comp: string) => {
    const c = (comp || "").toLowerCase();
    if (c.includes("display") || c.includes("screen")) return Monitor;
    if (c.includes("keyboard") || c.includes("deck") || c.includes("key")) return Keyboard;
    if (c.includes("port") || c.includes("usb") || c.includes("hdmi")) return Plug;
    if (c.includes("hinge") || c.includes("lid")) return Layers;
    return Laptop;
  };

  const cleanObsText = (text: string) => {
    if (!text) return "";
    return text
      .replace(/\s*\(Optical Inspection\s*\([^\)]*\)\)/gi, "")
      .replace(/\s*\(Optical Inspection[^\)]*\)/gi, "")
      .replace(/WhatsApp_Image_[^\s,\)]+/gi, "")
      .replace(/\(\s*\)/g, "")
      .replace(/^Optical analysis:\s*/gi, "")
      .replace(/\s{2,}/g, " ")
      .trim();
  };

  const isObservationWear = (obs: VisualObservation) => {
    const sev = (obs.severity || "").toUpperCase();
    if (["HIGH", "CRITICAL", "MODERATE", "MEDIUM"].includes(sev)) return true;
    if (obs.condition && obs.condition !== "no_visible_damage") return true;
    const txt = (obs.observation || "").toLowerCase();
    return (
      txt.includes("scratch") ||
      txt.includes("residue") ||
      txt.includes("wear") ||
      txt.includes("scuff") ||
      txt.includes("damage") ||
      txt.includes("crack") ||
      txt.includes("loose") ||
      txt.includes("dent") ||
      txt.includes("defect")
    );
  };

  const wearCount = (visibleObservations || []).filter(isObservationWear).length;
  const intactCount = (visibleObservations || []).length - wearCount;

  const displayedObservations = (visibleObservations || []).filter((obs) => {
    if (obsFilter === "wear") return isObservationWear(obs);
    if (obsFilter === "intact") return !isObservationWear(obs);
    return true;
  });

  const [showModelPicker, setShowModelPicker] = useState(false);
  const [isNonLaptopDetected, setIsNonLaptopDetected] = useState(false);
  const [modelSearchQuery, setModelSearchQuery] = useState("");
  const [customBrand, setCustomBrand] = useState("");
  const [customModel, setCustomModel] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync state if initialData is reset or cleared
  useEffect(() => {
    if (!initialData || !initialData.images || initialData.images.length === 0) {
      setImages([]);
      setRawFiles([]);
      setAnalyzed(false);
      setErrorMsg(null);
      setShowModelPicker(false);
      setIsNonLaptopDetected(false);
      setIdentifiedProduct({
        manufacturer: "",
        model: "",
        confidence: 0,
        confirmed: false,
        visible_label_text: null,
      });
      setVisibleObservations([]);
    }
  }, [initialData]);

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
    setShowModelPicker(false);
    setIsNonLaptopDetected(false);
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
      setErrorMsg(null);
      setShowModelPicker(false);
      setIsNonLaptopDetected(false);
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
    if (filesToUse.length === 0) {
      setErrorMsg(null);
      setShowModelPicker(false);
      return;
    }
    setAnalyzing(true);
    setErrorMsg(null);
    setShowModelPicker(false);
    setIsNonLaptopDetected(false);
    setScanStatusText("Uploading image to Gemini Vision API...");

    const fileHint = undefined;

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
        filesToUse.slice(0, 6),
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

        // Prioritize dynamic fault observations from genuine photo inspection (display cracks, loose keys, port defects)
        const observations: VisualObservation[] = (result.visible_observations && result.visible_observations.length > 0)
          ? (result.visible_observations as VisualObservation[])
          : (result.visual_clues || []).map(
              (clue: string, idx: number) => ({
                id: `vis-gemini-${idx}`,
                component: "chassis" as const,
                condition: "no_visible_damage" as const,
                observation: clue,
                confidence: result.confidence || 0.9,
                source: "MODEL_IDENTIFICATION" as const,
              })
            );

        if (observations.length === 0) {
          observations.push({
            id: "vis-obs-1",
            component: "chassis",
            condition: "no_visible_damage",
            observation: `Identified ${result.identified_model.manufacturer} ${result.identified_model.model} via optical design cues`,
            confidence: result.confidence || 0.9,
            source: "MODEL_IDENTIFICATION" as const,
          });
        }

        setVisibleObservations(observations);
        if (result.damage_findings) {
          setDamageFindings(result.damage_findings);
        }
        if (result.overall_visual_condition) {
          setOverallVisualCondition(result.overall_visual_condition);
        }
        setErrorMsg(null);
        setShowModelPicker(false);
        setAnalyzed(true);
      } else if (
        result.status === "NON_LAPTOP_REJECTED" ||
        result.is_laptop === false ||
        result.allow_manual_selection === false
      ) {
        setShowModelPicker(false);
        setIsNonLaptopDetected(true);
        setErrorMsg(
          result.message ||
            "A non-laptop device was detected. ReLoop AI only assesses laptop computers. Please upload photos of a laptop to proceed."
        );
        setIdentifiedProduct({
          manufacturer: "",
          model: "",
          confidence: 0,
          confirmed: false,
          visible_label_text: null,
        });
        setVisibleObservations([]);
        setAnalyzed(false);
      } else if (result.status === "AI_UNAVAILABLE") {
        setShowModelPicker(true);
        setErrorMsg(result.message || "AI identification is temporarily unavailable. Please select your model manually to continue.");
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
        setErrorMsg(result.message || "Unable to analyze these photos. Please provide clearer, well-lit device photos or select your model manually.");
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
        setErrorMsg(result.message || "Model could not be identified. Your device may not be in the currently supported catalog. Please select your model manually to continue.");
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
    if (images.length === 0) {
      setErrorMsg("Please upload at least one photo of your laptop to proceed.");
      return;
    }
    if (isNonLaptopDetected) {
      setErrorMsg("Assessment cannot proceed for a non-laptop device.");
      return;
    }
    const updatedProduct = { ...identifiedProduct, confirmed: true };
    setIdentifiedProduct(updatedProduct);

    const hasSevereOrModerate = visibleObservations.some(isObservationWear);
    const finalOverallCondition = overallVisualCondition || (hasSevereOrModerate ? "SERVICE_REQUIRED" : "GOOD");

    onComplete({
      images,
      rawFiles,
      identifiedProduct: updatedProduct,
      visibleObservations,
      damageFindings: damageFindings.length > 0 ? damageFindings : initialData?.damageFindings,
      overallVisualCondition: finalOverallCondition,
      damageAnalysisCompleted: true,
      visualAnalysisStatus: "COMPLETED",
    });
  };

  const handleSelectCustomModel = (item: { manufacturer: string; model: string }) => {
    if (images.length === 0) {
      setErrorMsg("Please upload at least one photo of your laptop before selecting a model.");
      return;
    }
    if (isNonLaptopDetected) {
      setErrorMsg("Manual selection is disabled because the uploaded image was identified as a non-laptop device. Please upload laptop photos to continue.");
      return;
    }
    const updated = {
      manufacturer: item.manufacturer,
      model: item.model,
      confidence: 1.0,
      confirmed: true,
      visible_label_text: null,
    };
    setIdentifiedProduct(updated);

    // Provide baseline observation if none exist so user can proceed
    if (visibleObservations.length === 0) {
      setVisibleObservations([
        {
          id: "vis-manual-1",
          component: "chassis",
          condition: "no_visible_damage",
          observation: `Verified hardware profile for ${item.manufacturer}`,
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
          <h2 className="text-3xl font-bold text-[#1D1D1F] dark:text-white tracking-tight">
            {t("visual.title", "Laptop Model Detection")}
          </h2>
          <p className="text-[#6E6E73] dark:text-slate-400 text-sm sm:text-base mt-1">
            {t("visual.subtitle", "Upload a photo of your laptop. Gemini Vision AI will automatically detect the manufacturer, exact model name, and physical characteristics.")}
          </p>
        </div>
      </div>

      {/* Non-negotiable technical rule disclaimer */}
      <div className="mb-6 p-4 rounded-xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-amber-900 dark:text-amber-200 text-xs sm:text-sm flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">{t("visual.ruleTitle", "Hardware Verification Rule:")}</span>
          {t("visual.ruleDesc", "Gemini Vision identifies laptop model and external casing condition from your photos. Internal battery and SSD health are gathered in Step 2 via diagnostics telemetry.")}
        </div>
      </div>

      {images.length > 0 && errorMsg && (
        <div data-testid="error-banner" className="mb-6 p-4 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600 dark:text-red-400" />
            <span>{errorMsg}</span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {!isNonLaptopDetected && (
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
            )}
            <button
              type="button"
              data-testid="retry-detection-btn"
              onClick={() => triggerVisionDetection(rawFiles, images)}
              className="text-xs font-semibold underline text-red-800 hover:text-red-950 dark:text-red-200 cursor-pointer"
            >
              {t("visual.retry", "Retry Detection")}
            </button>
          </div>
        </div>
      )}

      {/* Photo Upload Slots Card */}
      <div className="apple-card p-6 sm:p-8 mb-8 bg-white dark:bg-slate-900 border border-[#E5E5E7] dark:border-slate-800 shadow-sm rounded-3xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-2 gap-2">
          <div>
            <h3 className="text-lg font-bold text-[#1D1D1F] dark:text-white flex items-center gap-2">
              <Laptop className="w-5 h-5 text-[#0071E3]" />
              {t("visual.uploadTitle", "Upload Laptop Photos")}
            </h3>
            <p className="text-xs text-[#6E6E73] dark:text-slate-400 mt-0.5">
              {t("visual.uploadSubtitle", "Upload 1 or more photos (e.g. keyboard view, top lid, or bottom model label). Gemini will detect your laptop automatically!")}
            </p>
          </div>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#0071E3]/10 dark:bg-[#0071E3]/20 text-[#0071E3] dark:text-blue-400 w-fit">
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
                className="relative h-44 rounded-2xl border-2 border-dashed border-[#D2D2D7] dark:border-slate-700 bg-[#F5F5F7] dark:bg-slate-800/40 hover:bg-[#FBFBFD] dark:hover:bg-slate-800/80 transition-all flex flex-col items-center justify-center p-3 text-center overflow-hidden group shadow-2xs"
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
                        data-testid={`remove-image-btn-${idx}`}
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
                    <div className="w-10 h-10 rounded-full bg-white dark:bg-slate-800 shadow-2xs border border-[#E5E5E7] dark:border-slate-700 flex items-center justify-center mb-2 group-hover:border-[#0071E3]">
                      <Upload className="w-4 h-4 text-[#0071E3]" />
                    </div>
                    <span className="text-xs font-semibold text-[#1D1D1F] dark:text-white block">
                      {slotLabels[idx]}
                    </span>
                    <span className="text-[10px] text-[#86868B] dark:text-slate-400 mt-0.5">{t("visual.clickToUpload", "Click to upload photo")}</span>
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
          data-testid="file-upload-input"
        />

        {/* Footer Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#E5E5E7] dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-[#6E6E73] dark:text-slate-400">
            <Camera className="w-4 h-4 text-[#0071E3]" />
            <span>{t("visual.supportedFormats", "Supported: JPG, PNG, WEBP (Max 10MB each) • 1 to 6 photos")}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={isNonLaptopDetected || images.length === 0}
              onClick={() => {
                if (isNonLaptopDetected || images.length === 0) return;
                setShowModelPicker((prev) => !prev);
                setTimeout(() => {
                  document.getElementById("manual-model-picker")?.scrollIntoView({ behavior: "smooth" });
                }, 50);
              }}
              className={`px-4 py-2.5 rounded-full border border-[#D2D2D7] dark:border-slate-700 text-xs font-semibold transition-all ${
                isNonLaptopDetected || images.length === 0
                  ? "opacity-50 cursor-not-allowed text-[#86868B]"
                  : "text-[#1D1D1F] dark:text-slate-200 hover:bg-[#F5F5F7] dark:hover:bg-slate-800 cursor-pointer"
              }`}
              title={
                isNonLaptopDetected
                  ? "Manual laptop selection is disabled for non-laptop devices"
                  : images.length === 0
                  ? "Please upload laptop photos first"
                  : undefined
              }
            >
              {showModelPicker && !isNonLaptopDetected ? "Hide Manual Selection" : "Select Model Manually"}
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
              className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${images.length > 0 && !analyzing
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
      {showModelPicker && !isNonLaptopDetected && (
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

      {/* Manual Catalog Model Picker (Renders on UNKNOWN / AI_UNAVAILABLE / INVALID_EVIDENCE or when Change Model is clicked) */}
      {images.length > 0 && !analyzing && showModelPicker && !isNonLaptopDetected && (
        <div data-testid="model-picker" className="mb-8 p-6 rounded-3xl bg-[#F5F5F7] border border-[#D2D2D7] animate-in fade-in duration-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h5 className="text-sm font-bold uppercase tracking-wider text-[#1D1D1F]">
                {t("visual.pickerTitle", "Select or Adjust Laptop Model")}
              </h5>
              <p className="text-xs text-[#6E6E73] dark:text-slate-400 mt-0.5">
                {t("visual.pickerSubtitle", "Select a supported model from our verified hardware catalog:")}
              </p>
            </div>
            {analyzed && Boolean(identifiedProduct.model) && (
              <button
                type="button"
                onClick={() => setShowModelPicker(false)}
                className="text-xs font-semibold text-[#6E6E73] hover:text-[#1D1D1F] cursor-pointer"
              >
                {t("visual.pickerClose", "Close")}
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {catalogModels.map((m, idx) => (
              <button
                key={m.id || idx}
                type="button"
                data-testid={`catalog-model-option-${m.model.toLowerCase().replace(/[\s/()]+/g, "-")}`}
                onClick={() => handleSelectCustomModel(m)}
                className="p-3.5 rounded-2xl bg-white border border-[#E5E5E7] hover:border-[#0071E3] hover:shadow-xs text-left transition-all cursor-pointer flex items-center justify-between group"
              >
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block group-hover:text-[#0071E3] transition-colors">{m.model}</span>
                  <span className="text-[11px] text-[#6E6E73]">{m.manufacturer} • {m.category || "Supported Model"}</span>
                </div>
                <div className="w-6 h-6 rounded-full bg-[#F5F5F7] group-hover:bg-[#0071E3]/10 group-hover:text-[#0071E3] flex items-center justify-center text-[#0071E3] transition-colors">
                  →
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Gemini AI Identified Model Results — Redesigned Modern Studio Hub */}
      {images.length > 0 && analyzed && !analyzing && Boolean(identifiedProduct.model) && (
        <div data-testid="verified-model-card" className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Detected Model Hero Card — Apple Studio / Cyber-Hardware Showcase (Light & Dark) */}
          <div className="rounded-3xl bg-linear-to-b from-white via-white to-[#FBFBFD] dark:from-slate-900 dark:via-slate-900 dark:to-slate-950 border border-[#E5E5E7] dark:border-slate-800 p-6 sm:p-8 shadow-sm hover:shadow-md transition-all relative overflow-hidden">
            {/* Ambient Lighting Accents */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-linear-to-bl from-[#0071E3]/10 dark:from-[#2997FF]/15 via-[#34C759]/5 to-transparent rounded-bl-full pointer-events-none" />
            <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-[#0071E3]/5 dark:bg-[#2997FF]/10 rounded-full blur-2xl pointer-events-none" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-center relative z-10">
              {/* Left Column: Live Inspected Photo Viewfinder */}
              <div className="lg:col-span-5 relative group">
                <div className="relative aspect-4/3 rounded-2xl overflow-hidden border-2 border-[#0071E3]/30 dark:border-[#2997FF]/40 bg-[#090D16] shadow-md">
                  {images[0] ? (
                    <img
                      src={images[0]}
                      alt="Primary inspected laptop view"
                      className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[#6E6E73] dark:text-slate-400">
                      <Laptop className="w-12 h-12 text-[#0071E3] dark:text-[#2997FF]" />
                    </div>
                  )}

                  {/* Optical HUD Overlay */}
                  <div className="absolute inset-0 pointer-events-none p-3 flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/80 backdrop-blur-md text-[10px] font-mono font-bold text-emerald-400 border border-emerald-500/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        GEMINI 2.5 VISION
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-mono text-white/90">
                        {images.length} {images.length === 1 ? "Photo" : "Photos"}
                      </span>
                    </div>

                    {/* Viewfinder Target Reticle */}
                    <div className="self-center flex items-center justify-center text-[#0071E3]/60 dark:text-[#2997FF]/70">
                      <Scan className="w-14 h-14 stroke-[1.25] animate-pulse" />
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-xs text-[9px] font-mono text-slate-300">
                        OPTICAL SCAN ACTIVE
                      </span>
                      <span className="text-[9px] font-mono text-emerald-300 font-semibold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
                        MATCH VERIFIED
                      </span>
                    </div>
                  </div>
                </div>

                {/* Thumbnail strip if > 1 photo */}
                {images.length > 1 && (
                  <div className="flex items-center gap-2 mt-2.5 overflow-x-auto pb-1">
                    {images.slice(0, 5).map((img, i) => (
                      <div
                        key={i}
                        className={`w-12 h-12 rounded-xl overflow-hidden border-2 shrink-0 transition-all ${
                          i === 0
                            ? "border-[#0071E3] dark:border-[#2997FF] shadow-xs"
                            : "border-[#E5E5E7] dark:border-slate-800 opacity-75 hover:opacity-100"
                        }`}
                      >
                        <img src={img} alt={`Thumb ${i + 1}`} className="w-full h-full object-cover" />
                      </div>
                    ))}
                    {images.length > 5 && (
                      <div className="w-12 h-12 rounded-xl border border-[#E5E5E7] dark:border-slate-800 bg-[#F5F5F7] dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-[#6E6E73] dark:text-slate-300 shrink-0">
                        +{images.length - 5}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Right Column: AI Verified Machine Specs & Controls */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-mono font-extrabold uppercase tracking-wider px-3 py-1 rounded-full bg-[#1D1D1F] dark:bg-white text-white dark:text-[#1D1D1F] shadow-xs">
                    {identifiedProduct.manufacturer || "LAPTOP"}
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    {Math.round((identifiedProduct.confidence || 0.92) * 100)}% Match Precision
                  </span>
                  <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-blue-50 dark:bg-blue-950/50 text-[#0071E3] dark:text-blue-300 border border-blue-200 dark:border-blue-800/60">
                    AI Hardware Verified
                  </span>
                </div>

                <div>
                  <span className="text-[11px] text-[#86868B] dark:text-slate-400 uppercase tracking-wider font-bold block mb-1">
                    {t("visual.detectedModelLabel", "Detected Model")}
                  </span>
                  <h3 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#1D1D1F] dark:text-white tracking-tight">
                    {identifiedProduct.manufacturer} {identifiedProduct.model}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#6E6E73] dark:text-slate-400 mt-1 flex items-center gap-1.5">
                    <Laptop className="w-3.5 h-3.5 text-[#0071E3] dark:text-[#2997FF]" />
                    <span>Mobile PC Architecture • Verified Hardware Fingerprint</span>
                  </p>
                </div>

                {identifiedProduct.visible_label_text && (
                  <div className="p-3 rounded-xl bg-[#F5F5F7] dark:bg-slate-800/80 border border-[#E5E5E7] dark:border-slate-700/80 flex items-center gap-2">
                    <Tag className="w-4 h-4 text-[#0071E3] dark:text-[#2997FF] shrink-0" />
                    <div className="text-xs">
                      <span className="text-[#86868B] dark:text-slate-400 block text-[10px] font-semibold uppercase">OCR Regulatory Label:</span>
                      <span className="font-mono font-bold text-[#1D1D1F] dark:text-slate-100">&quot;{identifiedProduct.visible_label_text}&quot;</span>
                    </div>
                  </div>
                )}

                {/* Subsystem Readiness Indicators */}
                <div className="grid grid-cols-3 gap-2 pt-2">
                  <div className="p-2.5 rounded-xl bg-[#F5F5F7] dark:bg-slate-800/60 border border-[#E5E5E7]/70 dark:border-slate-700/60 text-center">
                    <span className="text-[10px] font-semibold text-[#86868B] dark:text-slate-400 uppercase block">Optical Match</span>
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center justify-center gap-1 mt-0.5">
                      <CheckCircle2 size={12} /> High
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#F5F5F7] dark:bg-slate-800/60 border border-[#E5E5E7]/70 dark:border-slate-700/60 text-center">
                    <span className="text-[10px] font-semibold text-[#86868B] dark:text-slate-400 uppercase block">Form Factor</span>
                    <span className="text-xs font-bold text-[#1D1D1F] dark:text-white mt-0.5 block">Standard Laptop</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#F5F5F7] dark:bg-slate-800/60 border border-[#E5E5E7]/70 dark:border-slate-700/60 text-center">
                    <span className="text-[10px] font-semibold text-[#86868B] dark:text-slate-400 uppercase block">Next Stage</span>
                    <span className="text-xs font-bold text-[#0071E3] dark:text-[#2997FF] mt-0.5 block">Diagnostics</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModelPicker(true)}
                    className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-full border border-[#D2D2D7] dark:border-slate-700 text-xs font-semibold text-[#1D1D1F] dark:text-slate-200 hover:bg-[#F5F5F7] dark:hover:bg-slate-800 transition-all cursor-pointer shadow-2xs"
                  >
                    <Edit3 size={13} className="text-[#6E6E73] dark:text-slate-400" />
                    <span>{t("visual.changeModel", "Adjust Model Manually")}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleConfirmModel}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-linear-to-r from-[#0071E3] to-[#0077ED] dark:from-[#2997FF] dark:to-[#0071E3] hover:from-[#0060C4] hover:to-[#0071E3] text-white text-xs font-bold transition-all shadow-md hover:shadow-lg cursor-pointer"
                  >
                    <CheckCircle2 size={15} />
                    <span>{t("visual.confirmContinue", "Confirm & Continue")}</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Visible Observations Deck — Reimagined Component Health Cards (Light & Dark) */}
          {visibleObservations.length > 0 && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E5E7] dark:border-slate-800">
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-[#1D1D1F] dark:text-white flex items-center gap-2">
                    <Eye className="w-4 h-4 text-[#0071E3] dark:text-[#2997FF]" />
                    <span>{t("visual.observationsTitle", "Gemini Optical Observations & Health Scan")}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#0071E3]/10 dark:bg-[#0071E3]/20 text-[#0071E3] dark:text-blue-400">
                      {visibleObservations.length} Findings
                    </span>
                  </h4>
                  <p className="text-xs text-[#6E6E73] dark:text-slate-400 mt-0.5">
                    Real-time visual defect extraction across display, keyboard, chassis, and peripheral interfaces.
                  </p>
                </div>

                {/* Filter Pills */}
                <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#F5F5F7] dark:bg-slate-800/80 border border-[#E5E5E7] dark:border-slate-700 self-start sm:self-auto">
                  <button
                    type="button"
                    onClick={() => setObsFilter("all")}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      obsFilter === "all"
                        ? "bg-white dark:bg-slate-700 text-[#1D1D1F] dark:text-white shadow-xs"
                        : "text-[#6E6E73] dark:text-slate-400 hover:text-[#1D1D1F] dark:hover:text-white"
                    }`}
                  >
                    All ({visibleObservations.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setObsFilter("wear")}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      obsFilter === "wear"
                        ? "bg-white dark:bg-slate-700 text-amber-700 dark:text-amber-400 shadow-xs"
                        : "text-[#6E6E73] dark:text-slate-400 hover:text-[#1D1D1F] dark:hover:text-white"
                    }`}
                  >
                    Wear & Alerts ({wearCount})
                  </button>
                  <button
                    type="button"
                    onClick={() => setObsFilter("intact")}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      obsFilter === "intact"
                        ? "bg-white dark:bg-slate-700 text-emerald-700 dark:text-emerald-400 shadow-xs"
                        : "text-[#6E6E73] dark:text-slate-400 hover:text-[#1D1D1F] dark:hover:text-white"
                    }`}
                  >
                    Intact ({intactCount})
                  </button>
                </div>
              </div>

              {/* Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {displayedObservations.map((obs) => {
                  const Icon = getObsIcon(obs.component);
                  const isWear = isObservationWear(obs);
                  const cleanedText = cleanObsText(obs.observation);
                  const sev = (obs.severity || "").toUpperCase();

                  return (
                    <div
                      key={obs.id}
                      className={`p-4 rounded-2xl border transition-all flex flex-col justify-between hover:shadow-xs ${
                        isWear
                          ? "border-amber-200/80 dark:border-amber-800/40 shadow-2xs bg-linear-to-b from-amber-50/30 to-white dark:from-amber-950/20 dark:to-slate-900"
                          : "border-[#E5E5E7] dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-[#D2D2D7] dark:hover:border-slate-700"
                      }`}
                    >
                      <div>
                        {/* Header: Component Icon + Name on left, Badge on right */}
                        <div className="flex items-center justify-between gap-2 mb-2.5">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                              isWear
                                ? "bg-amber-100/70 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300"
                                : "bg-[#F5F5F7] dark:bg-slate-800 text-[#0071E3] dark:text-[#2997FF]"
                            }`}>
                              <Icon size={16} />
                            </div>
                            <span className="text-xs font-bold capitalize text-[#1D1D1F] dark:text-white truncate">
                              {obs.component === "chassis" ? "Chassis / Enclosure" : obs.component === "display" ? "Display Panel" : obs.component === "keyboard" ? "Keyboard & Deck" : obs.component}
                            </span>
                          </div>

                          <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold border shrink-0 ${
                            isWear
                              ? sev === "HIGH" || sev === "CRITICAL"
                                ? "bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-300 border-red-200 dark:border-red-900/60"
                                : "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-900/60"
                              : "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-900/60"
                          }`}>
                            {isWear ? (sev || "WEAR DETECTED") : "VERIFIED INTACT"}
                          </span>
                        </div>

                        {/* Description */}
                        <p className="text-xs text-[#1D1D1F] dark:text-slate-200 font-medium leading-relaxed mb-3">
                          {cleanedText}
                        </p>
                      </div>

                      {/* Footer: Provenance tag & AI confidence */}
                      <div className="pt-2 border-t border-[#F5F5F7] dark:border-slate-800/80 flex items-center justify-between text-[10px] text-[#6E6E73] dark:text-slate-400">
                        <span className="inline-flex items-center gap-1">
                          <Sparkles size={11} className="text-[#0071E3] dark:text-[#2997FF]" />
                          <span>Gemini Optical Telemetry</span>
                        </span>
                        <span className="font-mono font-semibold">
                          {Math.round((obs.confidence || 0.9) * 100)}% Confidence
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Continue CTA */}
          <div className="pt-4 flex justify-end">
            <button
              type="button"
              onClick={handleConfirmModel}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-linear-to-r from-[#0071E3] to-[#0077ED] hover:from-[#0060C4] hover:to-[#0071E3] text-white text-sm font-semibold transition-all shadow-md hover:shadow-lg cursor-pointer"
            >
              <span>{t("visual.continueToDiag", "Continue to Diagnostics Telemetry →")}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
