"use client";

import React, { useState } from "react";
import { DiagnosticData, UserSymptomsData, VisualInspectionData } from "@/types/assessment";
import { Sparkles, RefreshCw, CheckCircle2, ShieldCheck, AlertCircle, ArrowLeft } from "lucide-react";

interface ReviewStepProps {
  visual: VisualInspectionData;
  diagnostics: DiagnosticData;
  symptoms: UserSymptomsData;
  onGenerateProfile: () => void;
  isGenerating: boolean;
  onBack?: () => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  visual,
  diagnostics,
  symptoms,
  onGenerateProfile,
  isGenerating,
  onBack,
}) => {
  const objectiveTitles: Record<string, string> = {
    lowest_cost: "Lowest cost",
    max_life: "Maximum remaining life",
    environmental: "Best environmental outcome",
    fastest_recovery: "Fastest way to get usable",
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-[#1D1D1F] text-white mb-2 inline-block">
          EVIDENCE AUDIT
        </span>
        <h2 className="text-3xl font-bold text-[#1D1D1F] tracking-tight">
          Review your assessment
        </h2>
        <p className="text-[#6E6E73] text-sm sm:text-base mt-1">
          Verify evidence provenance before generating the component-level condition profile.
        </p>
      </div>

      <div className="space-y-6">
        {/* 1. VISUAL INSPECTION REVIEW */}
        <div className="apple-card p-6 bg-white border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#E5E5E7]">
            <h3 className="text-base font-bold text-[#1D1D1F] flex items-center gap-2">
              <span>VISUAL INSPECTION</span>
            </h3>
            <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded bg-purple-50 text-purple-700 font-bold border border-purple-200">
              VISUAL
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div className="p-3 rounded-xl bg-[#F5F5F7]">
              <span className="text-[11px] text-[#86868B] block font-medium">Device Photos Uploaded</span>
              <span className="text-sm font-bold text-[#1D1D1F]">
                {visual.images.length} Photo{visual.images.length > 1 ? "s" : ""} Attached
              </span>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F5F7]">
              <span className="text-[11px] text-[#86868B] block font-medium">Confirmed Model</span>
              <span className="text-sm font-bold text-[#1D1D1F]">
                {visual.identifiedProduct.manufacturer} {visual.identifiedProduct.model}
              </span>
            </div>
          </div>

          <div>
            <span className="text-xs font-bold text-[#6E6E73] uppercase tracking-wider block mb-2">
              Visible Observations Detected:
            </span>
            <div className="space-y-2">
              {visual.visibleObservations.map((obs) => (
                <div
                  key={obs.id}
                  className="p-3 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-bold capitalize text-[#1D1D1F] mr-2">{obs.component}:</span>
                    <span className="text-[#6E6E73]">{obs.observation}</span>
                  </div>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-50 text-purple-700 font-bold shrink-0">
                    VISUAL
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 2. DIAGNOSTICS REVIEW */}
        <div className="apple-card p-6 bg-white border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#E5E5E7]">
            <h3 className="text-base font-bold text-[#1D1D1F]">DIAGNOSTICS</h3>
            <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded bg-blue-50 text-blue-700 font-bold border border-blue-200">
              DIAGNOSTIC
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Battery */}
            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] block">Battery Capacity</span>
                <span className="text-xs text-[#6E6E73]">
                  {diagnostics.battery.notProvided
                    ? "Not provided"
                    : `${diagnostics.battery.healthPercentage}% health (${diagnostics.battery.fullChargeCapacity} / ${diagnostics.battery.designCapacity} ${diagnostics.battery.unit})`}
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold">
                DIAGNOSTIC
              </span>
            </div>

            {/* SSD */}
            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] block">SSD / Storage</span>
                <span className="text-xs text-[#6E6E73]">
                  {diagnostics.ssd.notProvided
                    ? "Not provided"
                    : `${diagnostics.ssd.healthPercentage}% Health (SMART: ${diagnostics.ssd.smartStatus})`}
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold">
                DIAGNOSTIC
              </span>
            </div>

            {/* RAM */}
            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] block">RAM Memory</span>
                <span className="text-xs text-[#6E6E73]">
                  {diagnostics.ram.capacityGB} GB (Stress Test: {diagnostics.ram.testResult})
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold">
                DIAGNOSTIC
              </span>
            </div>

            {/* Thermals */}
            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] block">Thermals</span>
                <span className="text-xs text-[#6E6E73]">
                  {diagnostics.thermals.cpuTempC}°C (Throttling: {diagnostics.thermals.thermalThrottling})
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold">
                DIAGNOSTIC
              </span>
            </div>

            {/* System */}
            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between sm:col-span-2">
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] block">System Hardware Diagnostics</span>
                <span className="text-xs text-[#6E6E73]">
                  Hardware Result: {diagnostics.system.hardwareResult} • Faults: {diagnostics.system.criticalFaults}
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold">
                DIAGNOSTIC
              </span>
            </div>
          </div>
        </div>

        {/* 3. USER SYMPTOMS REVIEW */}
        <div className="apple-card p-6 bg-white border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#E5E5E7]">
            <h3 className="text-base font-bold text-[#1D1D1F]">USER SYMPTOMS & OBJECTIVE</h3>
            <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded bg-amber-50 text-amber-700 font-bold border border-amber-200">
              USER REPORTED
            </span>
          </div>

          <div className="space-y-3 mb-4">
            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7]">
              <span className="text-xs font-bold text-[#1D1D1F] block mb-1">Selected Symptoms:</span>
              {symptoms.selectedSymptoms.length === 0 ? (
                <span className="text-xs text-[#6E6E73]">No known symptoms reported</span>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {symptoms.selectedSymptoms.map((sym) => (
                    <span
                      key={sym.symptomId}
                      className="px-2.5 py-1 rounded-md bg-white border border-[#D2D2D7] text-xs text-[#1D1D1F] font-medium"
                    >
                      {sym.label} ({sym.frequency})
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="p-3.5 rounded-xl bg-[#FBFBFD] border border-[#E5E5E7] flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] block">Optimization Objective</span>
                <span className="text-xs text-[#0071E3] font-semibold">
                  {objectiveTitles[symptoms.userObjective] || symptoms.userObjective}
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-bold">
                USER REPORTED
              </span>
            </div>
          </div>
        </div>

        {/* Generate Condition Profile Button */}
        <div className="p-6 rounded-3xl bg-[#1D1D1F] text-white flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
          <div>
            <h4 className="text-lg font-bold">Ready to generate profile</h4>
            <p className="text-xs text-gray-300">
              Build normalized component-level condition profile with traceable evidence.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                disabled={isGenerating}
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm font-semibold transition-all cursor-pointer disabled:opacity-50"
              >
                <ArrowLeft size={16} />
                <span>Back</span>
              </button>
            )}
            <button
              type="button"
              disabled={isGenerating}
              onClick={onGenerateProfile}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer shrink-0"
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Evidence...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Condition Profile</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
