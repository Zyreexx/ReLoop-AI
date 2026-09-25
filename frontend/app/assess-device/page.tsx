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

export default function AssessDevicePage() {
  const { user } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [assessmentId, setAssessmentId] = useState<string>("");

  // Step 1 data: Visual
  const [visualData, setVisualData] = useState<VisualInspectionData>({
    images: [],
    identifiedProduct: {
      manufacturer: "Dell",
      model: "Latitude 5420",
      confidence: 0.91,
      confirmed: false,
    },
    visibleObservations: [
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
        observation: "No visible crack detected on display glass",
        confidence: 0.94,
      },
      {
        id: "vis-keyboard-1",
        component: "keyboard",
        condition: "minor_wear",
        observation: "Keycaps present; 2 loose keys reported",
        confidence: 0.85,
      },
    ],
  });

  // Step 2 data: Diagnostics
  const [diagnosticsData, setDiagnosticsData] = useState<DiagnosticData>({
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
  });

  // Step 3 data: User symptoms
  const [symptomsData, setSymptomsData] = useState<UserSymptomsData>({
    selectedSymptoms: [
      { symptomId: "battery_drain", label: "Battery drains quickly", frequency: "frequently" },
      { symptomId: "overheating", label: "Device overheats", frequency: "occasionally" },
    ],
    userDescription:
      "The laptop works normally when plugged in, but shuts down after about 30 minutes on battery.",
    userObjective: "max_life",
  });

  // Generated Condition Profile
  const [conditionProfile, setConditionProfile] = useState<ComponentConditionRecord[]>([]);

  // Automatically open auth modal if accessing /assess-device unauthenticated
  useEffect(() => {
    if (!user) {
      setAuthModalOpen(true);
    }
  }, [user]);

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleVisualComplete = (data: VisualInspectionData) => {
    setVisualData(data);
    setCurrentStep(2);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDiagnosticsComplete = (data: DiagnosticData) => {
    setDiagnosticsData(data);
    setCurrentStep(3);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSymptomsComplete = (data: UserSymptomsData) => {
    setSymptomsData(data);
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
      const res = await fetch("/api/assessments/generate-condition-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visual: visualData,
          diagnostics: diagnosticsData,
          symptoms: symptomsData,
          userId: user.email,
          userEmail: user.email,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Failed to generate profile.");
      }

      setConditionProfile(data.assessment.conditionProfile);
      setAssessmentId(data.assessment.id);
      try {
        localStorage.setItem(`assessment_${data.assessment.id}`, JSON.stringify(data.assessment));
        localStorage.setItem("current_assessment", JSON.stringify(data.assessment));
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
        {!user ? (
          /* AUTHENTICATION GUARD CARD */
          <div className="max-w-xl mx-auto px-6 py-24 text-center">
            <div className="apple-card p-8 sm:p-12 bg-white shadow-xl">
              <div className="w-14 h-14 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center mx-auto mb-5">
                <Lock className="w-7 h-7" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[#1D1D1F] tracking-tight mb-3">
                Sign in required
              </h2>
              <p className="text-sm text-[#6E6E73] leading-relaxed mb-8">
                Sign in to assess your device and save its condition report.
              </p>

              <button
                type="button"
                onClick={() => handleOpenAuth("login")}
                className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-6 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white font-semibold text-sm transition-all shadow-md cursor-pointer"
              >
                <span>Sign In / Create Account</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        ) : (
          /* AUTHENTICATED ASSESSMENT WORKFLOW */
          <div>
            {/* Top Page Header */}
            <div className="bg-white border-b border-[#E5E5E7] py-8 px-6 text-center">
              <div className="max-w-3xl mx-auto">
                <h1 className="text-3xl sm:text-4xl font-bold text-[#1D1D1F] tracking-tight mb-2">
                  Assess your device
                </h1>
                <p className="text-sm sm:text-base text-[#6E6E73] leading-relaxed">
                  Give ReLoop the evidence it needs to understand your device&apos;s current condition and determine its next best life.
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
                    <span>Back to Step {currentStep - 1}</span>
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
                <ConditionProfileView
                  conditionProfile={conditionProfile}
                  confirmedModelName={visualData.identifiedProduct.model}
                  manufacturer={visualData.identifiedProduct.manufacturer}
                  assessmentId={assessmentId}
                />
              )}
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
