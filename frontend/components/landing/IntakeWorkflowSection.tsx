"use client";

import React from "react";
import { Camera, Activity, MessageSquareText, Shield, Database, Cpu, CheckCircle2 } from "lucide-react";

export const IntakeWorkflowSection: React.FC = () => {
  const steps = [
    {
      step: "01",
      title: "Visual Evidence Intake",
      icon: Camera,
      badge: "Multimodal Vision AI",
      evidencePill: "VISUAL",
      pillStyle: "bg-purple-50 text-purple-700 border-purple-200",
      description:
        "Upload 2–3 photos of the laptop. Vision AI automatically identifies the make, model year, chassis condition, missing keys, and visible port damage.",
      guardrail: "Strict Boundary: Vision never guesses internal silicon health or battery chemistry from an exterior picture.",
      points: [
        "Exterior cosmetic condition score",
        "Screen surface crack detection",
        "Port wear & hinge alignment verification",
      ],
    },
    {
      step: "02",
      title: "Diagnostic Telemetry",
      icon: Activity,
      badge: "System Telemetry",
      evidencePill: "DIAGNOSTIC",
      pillStyle: "bg-blue-50 text-blue-700 border-blue-200",
      description:
        "Upload a battery report, SMART storage log, or enter available diagnostic metrics. Normalized against standard hardware manufacturer baselines.",
      guardrail: "Deterministic: Validates that full-charge capacity cannot exceed design capacity and flags thermal throttling limits.",
      points: [
        "Battery full-charge capacity & cycle count",
        "NVMe / SATA SMART health & bad sectors",
        "RAM pass/fail flags & peak thermal throttle data",
      ],
    },
    {
      step: "03",
      title: "User Symptoms & Goals",
      icon: MessageSquareText,
      badge: "Natural Language Parser",
      evidencePill: "USER REPORTED",
      pillStyle: "bg-amber-50 text-amber-700 border-amber-200",
      description:
        "Input user observations and usage goals. ReLoop aligns what the user actually needs (longer battery, school workstation, coding machine) with device realities.",
      guardrail: "Traceable: User statements are strictly labeled as user-reported so they aren't confused with laboratory measurements.",
      points: [
        "Reported thermal shutdown or intermittent glitch",
        "Performance lag on modern operating systems",
        "Desired second-life application requirements",
      ],
    },
  ];

  const provenanceTypes = [
    { label: "VISUAL", desc: "Detected from camera inspection", bg: "bg-purple-50 text-purple-700 border-purple-200" },
    { label: "DIAGNOSTIC", desc: "Measured hardware telemetry", bg: "bg-blue-50 text-blue-700 border-blue-200" },
    { label: "USER REPORTED", desc: "Direct customer observation", bg: "bg-amber-50 text-amber-700 border-amber-200" },
    { label: "DATABASE", desc: "OEM spec sheets & part catalog", bg: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    { label: "ESTIMATE", desc: "Mathematical lifecycle model", bg: "bg-slate-100 text-slate-700 border-slate-300" },
  ];

  return (
    <section id="how-it-works" className="py-24 md:py-36 bg-[#FBFBFD] border-b border-[#E5E5E7] relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Apple-style Section Header with Index Marker */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#E5E5E7] text-[11px] font-mono font-bold text-[#6E6E73] mb-4 shadow-2xs">
            <span>SECTION 02</span>
            <span>•</span>
            <span className="text-[#0071E3]">EVIDENCE INTAKE & PROVENANCE</span>
          </div>
          <h2 className="text-[34px] sm:text-[46px] md:text-[52px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            How ReLoop builds the ground truth.
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            Other tools guess. ReLoop enforces evidence integrity. Every recommendation is backed by verifiable, traceable data points.
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
                      STEP {item.step}
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
              Zero Guesswork • Verified Provenance Badges
            </h4>
            <p className="text-xs text-[#6E6E73]">
              Every assessment claim carries its proof source so users and IT asset managers always know what was measured vs modeled.
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
