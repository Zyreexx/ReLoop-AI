import React from "react";
import { Camera, Activity, MessageSquareText, Shield, CheckCircle2 } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

export const IntakeWorkflowSection: React.FC = () => {
  const { t } = useLanguage();
  const steps = [
    {
      step: "01",
      title: t("intake.step1Title", "Visual Evidence Intake"),
      icon: Camera,
      badge: t("intake.step1Badge", "Multimodal Vision AI"),
      evidencePill: t("provenance.visual", "VISUAL"),
      pillStyle: "bg-purple-50 text-purple-700 border-purple-200",
      description: t(
        "intake.step1Desc",
        "Upload 2–3 photos of the laptop. Vision AI automatically identifies the make, model year, chassis condition, missing keys, and visible port damage."
      ),
      guardrail: t(
        "intake.step1Guardrail",
        "Strict Boundary: Vision never guesses internal silicon health or battery chemistry from an exterior picture."
      ),
      points: [
        t("intake.step1Point1", "Exterior cosmetic condition score"),
        t("intake.step1Point2", "Screen surface crack detection"),
        t("intake.step1Point3", "Port wear & hinge alignment verification"),
      ],
    },
    {
      step: "02",
      title: t("intake.step2Title", "Diagnostic Telemetry"),
      icon: Activity,
      badge: t("intake.step2Badge", "System Telemetry"),
      evidencePill: t("provenance.diagnostic", "DIAGNOSTIC"),
      pillStyle: "bg-blue-50 text-blue-700 border-blue-200",
      description: t(
        "intake.step2Desc",
        "Upload a battery report, SMART storage log, or enter available diagnostic metrics. Normalized against standard hardware manufacturer baselines."
      ),
      guardrail: t(
        "intake.step2Guardrail",
        "Deterministic: Validates that full-charge capacity cannot exceed design capacity and flags thermal throttling limits."
      ),
      points: [
        t("intake.step2Point1", "Battery full-charge capacity & cycle count"),
        t("intake.step2Point2", "NVMe / SATA SMART health & bad sectors"),
        t("intake.step2Point3", "RAM pass/fail flags & peak thermal throttle data"),
      ],
    },
    {
      step: "03",
      title: t("intake.step3Title", "User Symptoms & Goals"),
      icon: MessageSquareText,
      badge: t("intake.step3Badge", "Natural Language Parser"),
      evidencePill: t("provenance.userReported", "USER REPORTED"),
      pillStyle: "bg-amber-50 text-amber-700 border-amber-200",
      description: t(
        "intake.step3Desc",
        "Input user observations and usage goals. ReLoop aligns what the user actually needs (longer battery, school workstation, coding machine) with device realities."
      ),
      guardrail: t(
        "intake.step3Guardrail",
        "Traceable: User statements are strictly labeled as user-reported so they aren't confused with laboratory measurements."
      ),
      points: [
        t("intake.step3Point1", "Reported thermal shutdown or intermittent glitch"),
        t("intake.step3Point2", "Performance lag on modern operating systems"),
        t("intake.step3Point3", "Desired second-life application requirements"),
      ],
    },
  ];

  const provenanceTypes = [
    {
      label: t("provenance.visual", "VISUAL"),
      desc: t("provenance.visualDesc", "Detected from camera inspection"),
      bg: "bg-purple-50 text-purple-700 border-purple-200",
    },
    {
      label: t("provenance.diagnostic", "DIAGNOSTIC"),
      desc: t("provenance.diagnosticDesc", "Measured hardware telemetry"),
      bg: "bg-blue-50 text-blue-700 border-blue-200",
    },
    {
      label: t("provenance.userReported", "USER REPORTED"),
      desc: t("provenance.userReportedDesc", "Direct customer observation"),
      bg: "bg-amber-50 text-amber-700 border-amber-200",
    },
    {
      label: t("provenance.database", "DATABASE"),
      desc: t("provenance.databaseDesc", "OEM spec sheets & part catalog"),
      bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
      label: t("provenance.estimate", "ESTIMATE"),
      desc: t("provenance.estimateDesc", "Mathematical lifecycle model"),
      bg: "bg-slate-100 text-slate-700 border-slate-300",
    },
  ];

  return (
    <section id="how-it-works" className="py-24 md:py-36 bg-[#FBFBFD] border-b border-[#E5E5E7] relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Apple-style Section Header with Index Marker */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#E5E5E7] text-[11px] font-mono font-bold text-[#6E6E73] mb-4 shadow-2xs">
            <span>{t("intake.sectionNum", "SECTION 02")}</span>
            <span>•</span>
            <span className="text-[#0071E3]">{t("intake.badge")}</span>
          </div>
          <h2 className="text-[34px] sm:text-[46px] md:text-[52px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            {t("intake.title")}
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            {t("intake.subtitle")}
          </p>
        </div>

        {/* 3 Step Intake Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="apple-card p-6 sm:p-8 flex flex-col justify-between bg-white"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-mono font-bold text-[#86868B]">
                      {t("intake.stepLabel", "STEP")} {item.step}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border ${item.pillStyle}`}
                    >
                      {item.evidencePill}
                    </span>
                  </div>

                  <div className="w-10 h-10 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] flex items-center justify-center text-[#0071E3] mb-4">
                    <Icon className="w-5 h-5" />
                  </div>

                  <h3 className="text-xl font-bold text-[#1D1D1F] tracking-tight mb-2">
                    {item.title}
                  </h3>

                  <p className="text-xs sm:text-sm text-[#6E6E73] leading-relaxed mb-5">
                    {item.description}
                  </p>

                  <div className="space-y-2 mb-6">
                    {item.points.map((p, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-[#1D1D1F]">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#0071E3] shrink-0" />
                        <span>{p}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#FBFBFD] border border-[#E5E5E7] text-[11px] text-[#86868B] leading-tight">
                  <Shield className="w-3 h-3 text-[#0071E3] inline mr-1" />
                  {item.guardrail}
                </div>
              </div>
            );
          })}
        </div>

        {/* Provenance Pills Showcase */}
        <div className="apple-card p-6 sm:p-8 bg-white max-w-4xl mx-auto">
          <div className="text-center max-w-xl mx-auto mb-6">
            <h4 className="text-base font-bold text-[#1D1D1F] mb-1">
              {t("intake.provenanceTitle", "Zero Guesswork • Verified Provenance Badges")}
            </h4>
            <p className="text-xs text-[#6E6E73]">
              {t(
                "intake.provenanceSubtitle",
                "Every assessment claim carries its proof source so users and IT asset managers always know what was measured vs modeled."
              )}
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {provenanceTypes.map((pt, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-[#E5E5E7] bg-[#FBFBFD] text-center flex flex-col items-center justify-center"
              >
                <span
                  className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-md border mb-2 ${pt.bg}`}
                >
                  {pt.label}
                </span>
                <span className="text-[11px] text-[#6E6E73] leading-snug">
                  {pt.desc}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
