"use client";
import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import { useAuth } from "@/context/AuthContext";
import { StepProgress } from "@/components/assess/StepProgress";
import { VisualInspectionStep } from "@/components/assess/VisualInspectionStep";
import { DiagnosticsStep } from "@/components/assess/DiagnosticsStep";
import { UserSymptomsStep } from "@/components/assess/UserSymptomsStep";
import { ReviewStep } from "@/components/assess/ReviewStep";
import { ConditionProfileView } from "@/components/assess/ConditionProfileView";
import {
  ComponentConditionRecord,
  DiagnosticData,
  UserSymptomsData,
  VisualInspectionData,
  VisualObservation,
} from "@/types/assessment";
import {
  Lock,
  ArrowRight,
  ShieldCheck,
  ArrowLeft,
  RotateCcw,
  Clock,
  Trash2,
  FileText,
  CheckCircle2,
} from "lucide-react";
import {
  createProduct,
  validateDiagnostics,
  parseSymptoms,
  buildAssessment,
  analyzeVision,
  getReport,
} from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

const ASSESSMENT_DRAFT_KEY = "reloop_active_assessment_draft";

export default function AssessDevicePage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [assessmentId, setAssessmentId] = useState<string>("");
  const [productId, setProductId] = useState<string>("");
  // Step 1 data: Visual
  const [visualData, setVisualData] = useState<VisualInspectionData>({
    images: [],
    identifiedProduct: {
      manufacturer: "",
      model: "",
      confidence: 0,
      confirmed: false,
    },
    visibleObservations: [],
  });
  // Step 2 data: Diagnostics
  const [diagnosticsData, setDiagnosticsData] = useState<DiagnosticData>({
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
  });
  // Step 3 data: User symptoms
  const [symptomsData, setSymptomsData] = useState<UserSymptomsData>({
    selectedSymptoms: [],
    userDescription: "",
    userObjective: "max_life",
  });
  // Generated Condition Profile
  const [conditionProfile, setConditionProfile] = useState<ComponentConditionRecord[]>([]);
  // Restored draft indicator banner
  const [restoredDraftInfo, setRestoredDraftInfo] = useState<{
    name: string;
    step: number;
    updatedAt: string;
  } | null>(null);

  // Restore saved in-progress draft from localStorage on mount
  useEffect(() => {
    try {
      const draftStr = localStorage.getItem(ASSESSMENT_DRAFT_KEY);
      if (draftStr) {
        const draft = JSON.parse(draftStr);
        const hasData =
          (draft.currentStep && draft.currentStep > 1) ||
          Boolean(draft.visualData?.identifiedProduct?.model) ||
          Boolean(draft.productId) ||
          Boolean(draft.diagnosticsData?.battery?.healthPercentage > 0) ||
          Boolean(draft.symptomsData?.selectedSymptoms?.length > 0);

        if (hasData) {
          if (draft.currentStep && draft.currentStep >= 1 && draft.currentStep <= 4) {
            setCurrentStep(draft.currentStep);
          }
          if (draft.productId) setProductId(draft.productId);
          if (draft.assessmentId) setAssessmentId(draft.assessmentId);
          if (draft.visualData) {
            setVisualData((prev) => ({
              ...prev,
              ...draft.visualData,
              rawFiles: undefined,
            }));
          }
          if (draft.diagnosticsData) {
            setDiagnosticsData((prev) => ({
              ...prev,
              ...draft.diagnosticsData,
            }));
          }
          if (draft.symptomsData) {
            setSymptomsData((prev) => ({
              ...prev,
              ...draft.symptomsData,
            }));
          }
          if (draft.conditionProfile && Array.isArray(draft.conditionProfile)) {
            setConditionProfile(draft.conditionProfile);
          }

          const mfr = draft.visualData?.identifiedProduct?.manufacturer || "";
          const model = draft.visualData?.identifiedProduct?.model || "Laptop";
          const displayName = [mfr, model].filter(Boolean).join(" ") || "In-Progress Laptop";

          setRestoredDraftInfo({
            name: displayName,
            step: draft.currentStep || 1,
            updatedAt: draft.updatedAt || new Date().toISOString(),
          });
        }
      }
    } catch (err) {
      console.warn("[ReLoop] Error restoring assessment draft:", err);
    }
  }, []);

  // Helper to persist current progress into localStorage draft
  const saveAssessmentDraft = (overrides?: {
    step?: number;
    visual?: VisualInspectionData;
    diagnostics?: DiagnosticData;
    symptoms?: UserSymptomsData;
    prodId?: string;
    assessId?: string;
  }) => {
    try {
      const vData = overrides?.visual || visualData;
      // Strip non-serializable File objects & truncate oversized base64 to avoid quota issues
      const safeVisual: VisualInspectionData = {
        ...vData,
        rawFiles: undefined,
        images: (vData.images || []).map((img) => (img.length > 250000 ? "" : img)).filter(Boolean),
      };
      const draft = {
        currentStep: overrides?.step ?? currentStep,
        productId: overrides?.prodId ?? productId,
        assessmentId: overrides?.assessId ?? assessmentId,
        visualData: safeVisual,
        diagnosticsData: overrides?.diagnostics ?? diagnosticsData,
        symptomsData: overrides?.symptoms ?? symptomsData,
        updatedAt: new Date().toISOString(),
        userEmail: user?.email || undefined,
      };
      localStorage.setItem(ASSESSMENT_DRAFT_KEY, JSON.stringify(draft));
    } catch (err) {
      console.warn("[ReLoop] Could not save assessment draft:", err);
    }
  };

  // Discard draft and reset to Step 1 clean
  const handleDiscardDraft = () => {
    if (
      window.confirm(
        "Are you sure you want to discard this in-progress assessment and start fresh? All entered data will be cleared."
      )
    ) {
      localStorage.removeItem(ASSESSMENT_DRAFT_KEY);
      setRestoredDraftInfo(null);
      setCurrentStep(1);
      setProductId("");
      setAssessmentId("");
      setVisualData({
        images: [],
        identifiedProduct: {
          manufacturer: "",
          model: "",
          confidence: 0,
          confirmed: false,
        },
        visibleObservations: [],
      });
      setDiagnosticsData({
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
      });
      setSymptomsData({
        selectedSymptoms: [],
        userDescription: "",
        userObjective: "max_life",
      });
      setConditionProfile([]);
    }
  };

  // Warn before accidental unload if assessment in active progress
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (currentStep >= 2 && currentStep <= 4) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [currentStep]);

  // Guest access is fully allowed - no forced modal
  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };
  const handleVisualComplete = async (data: VisualInspectionData) => {
    let enrichedData: VisualInspectionData = { ...data };
    let currentProdId = productId;
    // Create product record in the backend if model identified
    if (data.identifiedProduct?.model) {
      try {
        if (!currentProdId) {
          const product = await createProduct({
            manufacturer: data.identifiedProduct.manufacturer || "Laptop",
            model: data.identifiedProduct.model,
            model_year: 2021, // Default estimate — could be enhanced
            category: "LAPTOP",
            age: 4.5,
          });
          currentProdId = product.id;
          setProductId(product.id);
          console.log("[ReLoop] Product created in backend:", product.id);
        }

        // Explicit analysis-completion tracking to prevent duplicate AI calls while distinguishing empty results from failures
        const alreadyAnalyzed = Boolean(
          enrichedData.damageAnalysisCompleted === true ||
          enrichedData.visualAnalysisStatus === "COMPLETED" ||
          (enrichedData.damageFindings !== undefined &&
           enrichedData.overallVisualCondition !== undefined &&
           enrichedData.overallVisualCondition !== "NOT_ASSESSED" &&
           enrichedData.visualAnalysisStatus !== "FAILED")
        );

        if (data.rawFiles && data.rawFiles.length > 0 && !alreadyAnalyzed && currentProdId) {
          try {
            const notes = `Model: ${data.identifiedProduct.manufacturer} ${data.identifiedProduct.model}`;
            const visionRes = await analyzeVision(currentProdId, data.rawFiles, notes);
            console.log("[ReLoop] Backend vision damage analysis result:", visionRes);

            if (visionRes && visionRes.findings !== undefined) {
              const findingsList = Array.isArray(visionRes.findings) ? visionRes.findings : [];
              const damageObs: VisualObservation[] = findingsList.map((f: any, idx: number) => {
                const compStr = String(f.component || "chassis").toLowerCase();
                const validComp = ["chassis", "display", "keyboard", "hinge", "ports", "trackpad"].includes(compStr)
                  ? (compStr as any)
                  : "chassis";
                const sevUpper = String(f.severity || "LOW").toUpperCase();
                const cond = ["HIGH", "CRITICAL"].includes(sevUpper)
                  ? ("visible_crack" as const)
                  : ["MODERATE", "MEDIUM"].includes(sevUpper)
                  ? ("loose_part" as const)
                  : ("minor_wear" as const);
                return {
                  id: `vis-dmg-${idx}`,
                  component: validComp,
                  condition: cond,
                  observation: f.description,
                  confidence: f.confidence || 0.85,
                  severity: sevUpper as any,
                  source: "DAMAGE_ANALYSIS" as const,
                };
              });

              // Preserve model identification clues with source explicitly set
              const modelObs = (data.visibleObservations || [])
                .filter((o) => o.source === "MODEL_IDENTIFICATION" || !o.source)
                .map((o) => ({ ...o, source: "MODEL_IDENTIFICATION" as const }));

              enrichedData = {
                ...data,
                damageFindings: findingsList,
                overallVisualCondition: visionRes.overall_visual_condition || (findingsList.length === 0 ? "GOOD" : "SERVICE_REQUIRED"),
                visualAnalysisStatus: "COMPLETED",
                damageAnalysisCompleted: true,
                visibleObservations: damageObs.length > 0 ? [...damageObs, ...modelObs] : modelObs,
              };
            }
          } catch (vErr: any) {
            console.warn("[ReLoop] Backend vision analysis warning:", vErr.message);
            // Non-blocking error handling allowing safe retry
            enrichedData = {
              ...data,
              overallVisualCondition: "NOT_ASSESSED",
              visualAnalysisStatus: "FAILED",
              damageAnalysisCompleted: false,
            };
          }
        }
      } catch (err: any) {
        console.warn("[ReLoop] Backend product creation failed, using local flow:", err.message);
      }
    }
    setVisualData(enrichedData);
    setCurrentStep(2);
    saveAssessmentDraft({ step: 2, visual: enrichedData, prodId: currentProdId });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const handleDiagnosticsComplete = async (data: DiagnosticData) => {
    setDiagnosticsData(data);
    // Send diagnostics to backend for validation and evidence recording
    if (productId) {
      try {
        const result = await validateDiagnostics({
          product_id: productId,
          battery: data.battery.notProvided
            ? undefined
            : {
                design_capacity: data.battery.designCapacity,
                full_charge_capacity: data.battery.fullChargeCapacity,
                cycle_count: data.battery.cycleCount,
                health_percent: data.battery.healthPercentage,
              },
          ssd: data.ssd.notProvided
            ? undefined
            : {
                health_percent: data.ssd.healthPercentage,
                smart_status: data.ssd.smartStatus,
                power_on_hours: data.ssd.powerOnHours,
              },
          ram: {
            test_result: data.ram.testResult,
            installed_gb: data.ram.capacityGB,
          },
          thermals: {
            max_temp_c: data.thermals.cpuTempC,
            throttling_detected: data.thermals.thermalThrottling === "DETECTED",
          },
          system: {
            critical_errors:
              data.system.criticalFaults === "None reported" ? [] : [data.system.criticalFaults],
            post_successful: data.system.hardwareResult === "PASS",
            motherboard_power_stable: data.system.hardwareResult !== "FAIL",
          },
        });
        console.log("[ReLoop] Diagnostics validated in backend:", result.summary);
      } catch (err: any) {
        console.warn("[ReLoop] Backend diagnostics validation failed:", err.message);
      }
    }
    setCurrentStep(3);
    saveAssessmentDraft({ step: 3, diagnostics: data });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const handleSymptomsComplete = async (data: UserSymptomsData) => {
    setSymptomsData(data);
    // Send symptoms to backend for parsing and evidence recording
    if (productId) {
      try {
        const symptomLabels = data.selectedSymptoms.map((s) => s.label);
        const objectiveMap: Record<string, string> = {
          max_life: "daily_office_and_web",
          lowest_cost: "backup_secondary",
          environmental: "daily_office_and_web",
          fastest_recovery: "daily_office_and_web",
        };
        await parseSymptoms({
          product_id: productId,
          symptoms: symptomLabels,
          notes: data.userDescription,
          intended_use: objectiveMap[data.userObjective] || "daily_office_and_web",
        });
        console.log("[ReLoop] Symptoms parsed in backend");
      } catch (err: any) {
        console.warn("[ReLoop] Backend symptoms parsing failed:", err.message);
      }
    }
    setCurrentStep(4);
    saveAssessmentDraft({ step: 4, symptoms: data });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const handleBackStep = () => {
    const prev = Math.max(1, currentStep - 1);
    setCurrentStep(prev);
    saveAssessmentDraft({ step: prev });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const handleGenerateProfile = async () => {
    setIsGenerating(true);
    try {
      // If we have a backend product_id, build the assessment in the backend
      if (productId) {
        try {
          const profile = await buildAssessment(productId);
          // Map backend ConditionProfile (components dict) to frontend ComponentConditionRecord[]
          const condProfile: ComponentConditionRecord[] = Object.entries(
            profile.components
          ).map(([key, comp]) => {
            const statusMap: Record<string, "good" | "needs_attention" | "needs_service" | "fault"> = {
              GOOD: "good",
              WEAR: "needs_attention",
              SERVICE_REQUIRED: "needs_attention",
              REPLACE: "needs_service",
              REPLACE_REQUIRED: "needs_service",
              DAMAGED: "fault",
              UNKNOWN: "needs_attention",
            };
            const labelMap: Record<string, string> = {
              battery: "Battery",
              ssd: "SSD / Storage",
              ram: "RAM Memory",
              thermals: "Thermals & Cooling",
              display: "Display Panel",
              keyboard: "Keyboard",
              chassis: "Chassis / Case",
              system: "System / Motherboard",
            };
            return {
              component: labelMap[key] || comp.label || key,
              status: statusMap[comp.status] || "good",
              statusLabel: comp.label || comp.status,
              summary: comp.observations.join(" • ") || "Evaluated",
              confidence: comp.confidence || "High",
              evidence: comp.evidence_ids.map((id: string) => ({
                text: id,
                source: comp.evidence_sources[0] || "DIAGNOSTIC" as any,
              })),
              sourceTypes: comp.evidence_sources.map((s: string) => s as any),
            };
          });
          const backendAssessmentId = productId;
          setConditionProfile(condProfile);
          setAssessmentId(backendAssessmentId);
          // Fetch or synthesize full report
          let reportData: any = null;
          try {
            reportData = await getReport(productId);
          } catch (rErr) {
            console.warn("[ReLoop] Backend report fetch fallback:", rErr);
          }

          const mfr = visualData.identifiedProduct.manufacturer || "Laptop";
          const model = visualData.identifiedProduct.model || "Custom Model";
          const userName = user?.name || (user?.email ? user.email.split("@")[0] : "Guest Evaluator");
          const userEmail = user?.email ? user.email.toLowerCase() : undefined;
          const primaryPw = reportData?.recommendations?.primary_pathway || "REPAIR";

          if (!reportData) {
            reportData = {
              assessment_id: backendAssessmentId,
              timestamp: new Date().toISOString(),
              product: {
                manufacturer: mfr,
                model: model,
                category: "LAPTOP",
                age: diagnosticsData.deviceAgeYears || 4,
              },
              user: {
                name: userName,
                email: userEmail || "guest@reloop.ai",
              },
              condition_profile: {
                overall_hardware_health: profile.overall_hardware_health || "FAIR",
                components: condProfile.reduce((acc, c) => ({
                  ...acc,
                  [c.component.toLowerCase().replace(/[^a-z0-9]/g, "_")]: {
                    status: c.status,
                    label: c.statusLabel,
                    summary: c.summary,
                    confidence: c.confidence,
                  },
                }), {}),
              },
              recommendations: {
                primary_pathway: primaryPw,
                avoided_co2_kg: 215,
                life_extension_years: 3.5,
                estimated_cost_usd: 55,
                estimated_cost_inr: 4500,
                confidence_score: 0.92,
              },
              diagnostics: diagnosticsData,
              symptoms: symptomsData,
            };
          }

          // Save to user store or guest store in localStorage
          const isGuest = !user;
          const assessmentRecord = {
            id: backendAssessmentId,
            userId: userEmail || "guest",
            userEmail: userEmail,
            userName: userName,
            isGuest,
            createdAt: new Date().toISOString(),
            laptop: {
              manufacturer: mfr,
              model: model,
              fullName: `${mfr} ${model}`.trim(),
              category: "LAPTOP",
              ageYears: diagnosticsData.deviceAgeYears || 4,
            },
            visual: visualData,
            diagnostics: diagnosticsData,
            symptoms: symptomsData,
            conditionProfile: condProfile,
            backendProductId: productId,
            overallHealth: profile.overall_hardware_health,
            topPathway: {
              pathway: primaryPw,
              title: primaryPw === "REPAIR"
                ? "Modular Repair & Thermal Servicing"
                : primaryPw === "REFURBISH"
                ? "Component Refurbishment & Renewal"
                : primaryPw === "REPURPOSE"
                ? "Repurpose as Home Server / Thin Client"
                : "Certified Material Harvesting & Recycling",
              action: "Restore optimal system performance & extend service life",
              lifeExtensionYears: reportData?.recommendations?.life_extension_years || 3.5,
              avoidedCo2Kg: reportData?.recommendations?.avoided_co2_kg || 215,
              estimatedCostUsd: reportData?.recommendations?.estimated_cost_usd || 55,
              estimatedCostInr: reportData?.recommendations?.estimated_cost_inr || 4500,
              turnaroundDays: 2,
            },
            report: reportData,
          };
          try {
            localStorage.setItem(`assessment_${backendAssessmentId}`, JSON.stringify(assessmentRecord));
            localStorage.setItem("current_assessment", JSON.stringify(assessmentRecord));
            if (userEmail) {
              const userListKey = `reloop_user_assessments_${userEmail}`;
              const storedList = JSON.parse(localStorage.getItem(userListKey) || "[]");
              const updatedList = [assessmentRecord, ...storedList.filter((a: any) => a.id !== backendAssessmentId)];
              localStorage.setItem(userListKey, JSON.stringify(updatedList));
              fetch("/api/assessments", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(assessmentRecord),
              }).catch((e) => console.warn("Failed to sync assessment to API:", e));
            } else {
              const guestList = JSON.parse(localStorage.getItem("reloop_guest_assessments") || "[]");
              const updatedGuestList = [assessmentRecord, ...guestList.filter((a: any) => a.id !== backendAssessmentId)];
              localStorage.setItem("reloop_guest_assessments", JSON.stringify(updatedGuestList));
            }
            // Clear in-progress draft once finalized
            localStorage.removeItem(ASSESSMENT_DRAFT_KEY);
            setRestoredDraftInfo(null);
          } catch (err) {
            console.warn("Could not write assessment to localStorage", err);
          }
          console.log("[ReLoop] Assessment built from backend:", profile.overall_hardware_health);
          setCurrentStep(5);
          window.scrollTo({ top: 0, behavior: "smooth" });
          return;
        } catch (backendErr: any) {
          console.warn("[ReLoop] Backend assessment build failed, falling back to local:", backendErr.message);
        }
      }
      // Fallback: Use the existing Next.js mock route
      const res = await fetch("/api/assessments/generate-condition-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visual: visualData,
          diagnostics: diagnosticsData,
          symptoms: symptomsData,
          userId: user?.email ? user.email.toLowerCase() : "guest",
          userEmail: user?.email || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Failed to generate profile.");
      }
      setConditionProfile(data.assessment.conditionProfile);
      setAssessmentId(data.assessment.id);
      try {
        const mfrFb = visualData.identifiedProduct.manufacturer || "Laptop";
        const modelFb = visualData.identifiedProduct.model || "Custom Model";
        const userNameFb = user?.name || (user?.email ? user.email.split("@")[0] : "Guest Evaluator");
        const userEmailFb = user?.email ? user.email.toLowerCase() : undefined;

        const fallbackReport = {
          assessment_id: data.assessment.id,
          timestamp: new Date().toISOString(),
          product: {
            manufacturer: mfrFb,
            model: modelFb,
            category: "LAPTOP",
            age: diagnosticsData.deviceAgeYears || 4,
          },
          user: {
            name: userNameFb,
            email: userEmailFb || "guest@reloop.ai",
          },
          condition_profile: {
            overall_hardware_health: data.assessment.overallHealth || "FAIR",
            components: (data.assessment.conditionProfile || []).reduce((acc: any, c: any) => ({
              ...acc,
              [c.component.toLowerCase().replace(/[^a-z0-9]/g, "_")]: {
                status: c.status,
                label: c.statusLabel,
                summary: c.summary,
                confidence: c.confidence,
              },
            }), {}),
          },
          recommendations: {
            primary_pathway: "REPAIR",
            avoided_co2_kg: 215,
            life_extension_years: 3.5,
            estimated_cost_usd: 45,
            confidence_score: 0.92,
          },
          diagnostics: diagnosticsData,
          symptoms: symptomsData,
        };

        const enrichedRecord = {
          ...data.assessment,
          backendProductId: productId || data.assessment.backendProductId || data.assessment.id,
          userId: userEmailFb || "guest",
          userEmail: userEmailFb,
          userName: userNameFb,
          isGuest: !user,
          laptop: {
            manufacturer: mfrFb,
            model: modelFb,
            fullName: `${mfrFb} ${modelFb}`.trim(),
            category: "LAPTOP",
            ageYears: diagnosticsData.deviceAgeYears || 4,
          },
          topPathway: data.assessment.topPathway || {
            pathway: "REPAIR",
            title: "Modular Repair & Thermal Servicing",
            action: "Restore optimal system performance & extend service life",
            lifeExtensionYears: 3.5,
            avoidedCo2Kg: 215,
            estimatedCostUsd: 45,
            turnaroundDays: 2,
          },
          report: fallbackReport,
        };
        localStorage.setItem(`assessment_${data.assessment.id}`, JSON.stringify(enrichedRecord));
        localStorage.setItem("current_assessment", JSON.stringify(enrichedRecord));
        if (userEmailFb) {
          const userListKey = `reloop_user_assessments_${userEmailFb}`;
          const storedList = JSON.parse(localStorage.getItem(userListKey) || "[]");
          const updatedList = [enrichedRecord, ...storedList.filter((a: any) => a.id !== data.assessment.id)];
          localStorage.setItem(userListKey, JSON.stringify(updatedList));
          fetch("/api/assessments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(enrichedRecord),
          }).catch((e) => console.warn("Failed to sync assessment to API:", e));
        } else {
          const guestList = JSON.parse(localStorage.getItem("reloop_guest_assessments") || "[]");
          const updatedGuestList = [enrichedRecord, ...guestList.filter((a: any) => a.id !== data.assessment.id)];
          localStorage.setItem("reloop_guest_assessments", JSON.stringify(updatedGuestList));
        }
        // Clear in-progress draft once finalized
        localStorage.removeItem(ASSESSMENT_DRAFT_KEY);
        setRestoredDraftInfo(null);
      } catch (err) {
        console.warn("Could not write assessment to localStorage", err);
      }
      setCurrentStep(5);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      alert(err.message || "Failed to generate condition profile.");
    } finally {
      setIsGenerating(false);
    }
  };
  return (
    <div className="min-h-screen flex flex-col bg-[#F5F5F7] text-[#1D1D1F]">
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
      <Navbar onOpenAuth={handleOpenAuth} />
      {/* Main Container */}
      <main className="flex-1">
        <div>
          {/* Guest Evaluation Banner */}
          {!user && (
            <div className="bg-[#0071E3]/5 border-b border-[#0071E3]/15 py-2.5 px-6">
              <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[#1D1D1F]">
                <span className="flex items-center gap-1.5 text-[#6E6E73]">
                  <span className="w-2 h-2 rounded-full bg-[#34C759]"></span>
                  <span>Evaluating as <strong>Guest</strong>. You can assess your device freely without an account.</span>
                </span>
                <button
                  type="button"
                  onClick={() => handleOpenAuth("login")}
                  className="text-[#0071E3] hover:underline font-semibold cursor-pointer"
                >
                  Sign in to save history →
                </button>
              </div>
            </div>
          )}
          {/* Top Page Header */}
          <div className="bg-white border-b border-[#E5E5E7] py-8 px-6 text-center">
              <div className="max-w-3xl mx-auto">
                <h1 className="text-3xl sm:text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">
                  {t("assess.header", "Assess your device")}
                </h1>
                <p className="text-sm sm:text-base text-[#6E6E73] leading-relaxed">
                  {t(
                    "assess.subtitle",
                    "Give ReLoop the evidence it needs to understand your device's current condition and determine its next best life."
                  )}
                </p>
              </div>
            </div>
            {/* In-Progress Assessment Draft Restored Banner */}
            {restoredDraftInfo && currentStep < 5 && (
              <div className="max-w-4xl mx-auto px-6 pt-5 pb-1">
                <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-blue-500/5 border border-[#0071E3]/25 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-[#0071E3] text-white flex items-center justify-center shrink-0 shadow-xs">
                      <RotateCcw size={18} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[#0071E3] bg-[#0071E3]/15 px-2 py-0.5 rounded-full">
                          Draft Restored
                        </span>
                        <span className="text-xs text-[#86868B]">Step {currentStep} of 4</span>
                      </div>
                      <p className="text-xs sm:text-sm font-semibold text-[#1D1D1F] mt-0.5">
                        Resumed assessment for <span className="text-[#0071E3] font-bold">{restoredDraftInfo.name}</span>
                      </p>
                      <p className="text-[11px] text-[#6E6E73]">
                        Your progress was preserved. If you navigated to another menu or refreshed, your data is safe.
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={handleDiscardDraft}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-[#FF3B30] hover:bg-[#FF3B30]/10 border border-[#FF3B30]/30 transition-all cursor-pointer"
                      title="Clear draft and start with a new device"
                    >
                      <Trash2 size={13} />
                      <span>Start Fresh</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Step Progress Header */}
            <StepProgress
              currentStep={currentStep}
              onStepClick={(step) => {
                setCurrentStep(step);
                saveAssessmentDraft({ step });
              }}
            />
            {/* Step Content Router */}
            <div className="pb-20">
              {currentStep > 1 && currentStep < 5 && (
                <div className="max-w-4xl mx-auto px-6 pt-4 pb-2">
                  <button
                    type="button"
                    onClick={handleBackStep}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6E6E73] hover:text-[#0071E3] transition-colors cursor-pointer group"
                  >
                    <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
                    <span>{t("common.backToStep", "Back to Step")} {currentStep - 1}</span>
                  </button>
                </div>
              )}
              {currentStep === 1 && (
                <VisualInspectionStep
                  initialData={visualData}
                  onComplete={handleVisualComplete}
                />
              )}
              {currentStep === 2 && (
                <DiagnosticsStep
                  productId={productId}
                  confirmedModelName={visualData.identifiedProduct.model}
                  manufacturer={visualData.identifiedProduct.manufacturer}
                  initialData={diagnosticsData}
                  onComplete={handleDiagnosticsComplete}
                  onBack={handleBackStep}
                />
              )}
              {currentStep === 3 && (
                <UserSymptomsStep
                  initialData={symptomsData}
                  onComplete={handleSymptomsComplete}
                  onBack={handleBackStep}
                />
              )}
              {currentStep === 4 && (
                <ReviewStep
                  visual={visualData}
                  diagnostics={diagnosticsData}
                  symptoms={symptomsData}
                  onGenerateProfile={handleGenerateProfile}
                  isGenerating={isGenerating}
                  onBack={handleBackStep}
                />
              )}
              {currentStep === 5 && (
                <div>
                  {!user ? (
                    <div className="max-w-3xl mx-auto px-6 mb-8">
                      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/60 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div>
                          <h4 className="font-semibold text-sm text-[#1D1D1F]">Want to save this device to your account?</h4>
                          <p className="text-xs text-[#6E6E73] mt-0.5">Sign in to keep this evaluation in "My Devices" and track lifecycle recommendations over time.</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleOpenAuth("login")}
                          className="px-5 py-2.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold shrink-0 cursor-pointer shadow-sm transition-all"
                        >
                          Sign In & Save Device
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-3xl mx-auto px-6 mb-6 text-center">
                      <a
                        href="/dashboard"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#34C759]/10 text-[#34C759] border border-[#34C759]/20 text-xs font-semibold hover:bg-[#34C759]/20 transition-all cursor-pointer"
                      >
                        <ShieldCheck size={14} />
                        <span>Saved to My Devices — View in Hardware Ledger →</span>
                      </a>
                    </div>
                  )}
                  <ConditionProfileView
                    conditionProfile={conditionProfile}
                    confirmedModelName={visualData.identifiedProduct.model}
                    manufacturer={visualData.identifiedProduct.manufacturer}
                    assessmentId={assessmentId}
                  />
                </div>
              )}
            </div>
          </div>
      </main>
      <Footer />
    </div>
  );
}