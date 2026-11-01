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
} from "@/types/assessment";
import { Lock, ArrowRight, ShieldCheck, ArrowLeft } from "lucide-react";
import {
  createProduct,
  validateDiagnostics,
  parseSymptoms,
  buildAssessment,
  analyzeVision,
} from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
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
  // Guest access is fully allowed - no forced modal
  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };
  const handleVisualComplete = async (data: VisualInspectionData) => {
    setVisualData(data);
    // Create product record in the backend if model identified
    if (data.identifiedProduct?.model) {
      try {
        const product = await createProduct({
          manufacturer: data.identifiedProduct.manufacturer || "Laptop",
          model: data.identifiedProduct.model,
          model_year: 2021, // Default estimate — could be enhanced
          category: "LAPTOP",
          age: 4.5,
        });
        setProductId(product.id);
        console.log("[ReLoop] Product created in backend:", product.id);
        // Record visual damage analysis evidence in backend if photos/observations available
        if (data.rawFiles && data.rawFiles.length > 0) {
          try {
            const notes = data.visibleObservations.map((o) => `${o.component}: ${o.observation}`).join(". ");
            await analyzeVision(product.id, data.rawFiles, notes);
            console.log("[ReLoop] Visual evidence recorded in backend for product:", product.id);
          } catch (vErr: any) {
            console.warn("[ReLoop] Backend vision analysis warning:", vErr.message);
          }
        }
      } catch (err: any) {
        console.warn("[ReLoop] Backend product creation failed, using local flow:", err.message);
      }
    }
    setCurrentStep(2);
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
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const handleBackStep = () => {
    setCurrentStep((prev) => Math.max(1, prev - 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const handleGenerateProfile = async () => {
    if (!user) {
      handleOpenAuth("login");
      return;
    }
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
          // Save to user store or guest store in localStorage
          const isGuest = !user;
          const assessmentRecord = {
            id: backendAssessmentId,
            userId: user?.email ? user.email.toLowerCase() : "guest",
            userEmail: user?.email || undefined,
            isGuest,
            createdAt: new Date().toISOString(),
            visual: visualData,
            diagnostics: diagnosticsData,
            symptoms: symptomsData,
            conditionProfile: condProfile,
            backendProductId: productId,
            overallHealth: profile.overall_hardware_health,
          };
          try {
            localStorage.setItem(`assessment_${backendAssessmentId}`, JSON.stringify(assessmentRecord));
            localStorage.setItem("current_assessment", JSON.stringify(assessmentRecord));
            if (user?.email) {
              const userListKey = `reloop_user_assessments_${user.email.toLowerCase()}`;
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
        const enrichedRecord = {
          ...data.assessment,
          backendProductId: productId || data.assessment.backendProductId || data.assessment.id,
          userId: user?.email ? user.email.toLowerCase() : "guest",
          userEmail: user?.email || undefined,
          isGuest: !user,
        };
        localStorage.setItem(`assessment_${data.assessment.id}`, JSON.stringify(enrichedRecord));
        localStorage.setItem("current_assessment", JSON.stringify(enrichedRecord));
        if (user?.email) {
          const userListKey = `reloop_user_assessments_${user.email.toLowerCase()}`;
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
            {/* Step Progress Header */}
            <StepProgress
              currentStep={currentStep}
              onStepClick={(step) => setCurrentStep(step)}
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