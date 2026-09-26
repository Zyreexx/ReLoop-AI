"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { ComponentConditionRecord } from "@/types/assessment";
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  BatteryCharging,
  HardDrive,
  Cpu,
  Flame,
  Layers,
  Wrench,
  Sparkles,
  Laptop,
  Camera,
  Activity,
  User,
  Check,
} from "lucide-react";

interface ConditionProfileViewProps {
  conditionProfile: ComponentConditionRecord[];
  confirmedModelName: string;
  manufacturer: string;
  assessmentId: string;
}

interface NormalizedSource {
  key: string;
  label: string;
  category: "visual" | "diagnostic" | "user" | "specs";
}

export const ConditionProfileView: React.FC<ConditionProfileViewProps> = ({
  conditionProfile,
  confirmedModelName,
  manufacturer,
  assessmentId,
}) => {
  // Support state fallback if loaded from direct navigation or storage
  const [deviceModel, setDeviceModel] = useState<string>(confirmedModelName || "");
  const [deviceMfr, setDeviceMfr] = useState<string>(manufacturer || "");

  useEffect(() => {
    if (confirmedModelName) setDeviceModel(confirmedModelName);
    if (manufacturer) setDeviceMfr(manufacturer);

    if ((!confirmedModelName || !manufacturer) && typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("current_assessment");
        if (stored) {
          const parsed = JSON.parse(stored);
          if (!confirmedModelName && parsed.visual?.identifiedProduct?.model) {
            setDeviceModel(parsed.visual.identifiedProduct.model);
          }
          if (!manufacturer && parsed.visual?.identifiedProduct?.manufacturer) {
            setDeviceMfr(parsed.visual.identifiedProduct.manufacturer);
          }
        }
      } catch (err) {
        // silent catch
      }
    }
  }, [confirmedModelName, manufacturer]);

  // Format clean unified display name without repetitive prefix (e.g. "HP HP Victus 16" -> "HP Victus 16")
  const fullDeviceName = useMemo(() => {
    const m = (deviceMfr || "").trim();
    const mod = (deviceModel || "").trim();
    if (!m && !mod) return "Assessed Laptop";
    if (!m) return mod;
    if (!mod) return m;
    if (mod.toLowerCase().startsWith(m.toLowerCase())) return mod;
    return `${m} ${mod}`;
  }, [deviceMfr, deviceModel]);

  const getComponentIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case "battery":
        return BatteryCharging;
      case "ssd / storage":
        return HardDrive;
      case "ram memory":
        return Layers;
      case "thermals & cooling":
        return Flame;
      case "display panel":
        return ShieldCheck;
      case "system / motherboard":
        return Cpu;
      default:
        return Wrench;
    }
  };

  // Helper to normalize and deduplicate raw source strings
  const normalizeSource = (src: string): NormalizedSource => {
    const upper = (src || "").toUpperCase();
    if (
      upper.includes("OPTICAL") ||
      upper.includes("VISUAL") ||
      upper.includes("INSPECTION") ||
      upper.includes(".JPG") ||
      upper.includes(".PNG") ||
      upper.includes(".JPEG") ||
      upper.includes(".WEBP")
    ) {
      return { key: "visual", label: "Visual AI", category: "visual" };
    }
    if (
      upper.includes("QUESTIONNAIRE") ||
      upper.includes("USER") ||
      upper.includes("SYMPTOM")
    ) {
      return { key: "user", label: "User Symptoms", category: "user" };
    }
    if (
      upper.includes("CATALOG") ||
      upper.includes("SPECIFICATION") ||
      upper.includes("HARDWARE") && upper.includes("SPEC")
    ) {
      return { key: "specs", label: "OEM Specs", category: "specs" };
    }
    return { key: "diagnostic", label: "Diagnostics", category: "diagnostic" };
  };

  const getDeduplicatedSources = (sourceTypes: string[]): NormalizedSource[] => {
    const map = new Map<string, NormalizedSource>();
    for (const src of sourceTypes || []) {
      const norm = normalizeSource(src);
      if (!map.has(norm.key)) {
        map.set(norm.key, norm);
      }
    }
    return Array.from(map.values());
  };

  // Clean redundant trailing source tags from summary descriptions
  const cleanSummaryText = (text: string): string => {
    if (!text) return "";
    let cleaned = text
      .replace(
        /\s*\((?:Optical Inspection|OS Battery|Storage Controller|UEFI|Hardware Specification|User Diagnostic|MemTest)[^)]*\)\.?$/gi,
        ""
      )
      .trim();
    if (cleaned && !cleaned.endsWith(".") && !cleaned.endsWith("!") && !cleaned.endsWith("?")) {
      cleaned += ".";
    }
    return cleaned;
  };

  // Clean status label so it doesn't duplicate the status pill badge
  const cleanHeadlineLabel = (label: string, fallbackComponent: string): string => {
    if (!label) return fallbackComponent;
    return label
      .replace(/\s*-\s*(?:Service Recommended|Needs Attention|Good|Healthy)/gi, "")
      .trim();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      {/* Prominent Hero Banner with Clearly Visible Laptop Model Name */}
      <div className="bg-white rounded-3xl border border-[#E5E5E7] p-6 sm:p-8 shadow-sm mb-10 transition-all hover:shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start sm:items-center gap-4 sm:gap-5">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-blue-500/10 via-[#0071E3]/10 to-indigo-500/10 border border-[#0071E3]/20 flex items-center justify-center text-[#0071E3] shrink-0 shadow-xs">
              <Laptop className="w-7 h-7 sm:w-8 sm:h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className="text-[10px] font-mono font-bold tracking-wider uppercase px-2.5 py-0.5 rounded-full bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20">
                  Assessed Laptop Model
                </span>
                <span className="text-xs font-semibold text-[#34C759] flex items-center gap-1">
                  <CheckCircle2 size={13} />
                  Condition Profile Active
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#1D1D1F] tracking-tight">
                {fullDeviceName}
              </h1>
              <p className="text-xs sm:text-sm text-[#6E6E73] mt-1.5 max-w-2xl leading-relaxed">
                Component-level health evaluation synthesized from visual inspection, hardware diagnostics, and reported user symptoms.
              </p>
            </div>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 pt-4 sm:pt-0 border-[#F0F0F2] gap-1.5 shrink-0">
            <span className="text-[11px] font-medium text-[#86868B] uppercase tracking-wider">
              Evaluated Components
            </span>
            <div className="text-2xl font-bold text-[#1D1D1F] flex items-baseline gap-1">
              <span>{conditionProfile.length}</span>
              <span className="text-xs font-semibold text-[#86868B]">Subsystems</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid of Component Condition Cards — Spacious & Uncongested */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {conditionProfile.map((record, idx) => {
          const Icon = getComponentIcon(record.component);
          const isGood = record.status === "good";
          const isAttention = record.status === "needs_attention";
          const isService = record.status === "needs_service" || record.status === "fault";

          const deduplicatedSources = getDeduplicatedSources(record.sourceTypes);
          const headline = cleanHeadlineLabel(record.statusLabel, record.component);
          const cleanedSummary = cleanSummaryText(record.summary);

          // Partition evidence between real observations and raw internal IDs
          const descriptiveEvidence = record.evidence.filter(
            (ev) => !ev.text.startsWith("ev_") && ev.text.trim().length > 0
          );
          const rawEvidenceCount = record.evidence.length;

          return (
            <div
              key={idx}
              className="bg-white rounded-2xl border border-[#E5E5E7] p-6 shadow-xs hover:border-[#0071E3]/40 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Header: Icon + Title on left, Status Pill on right */}
                <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-[#F5F5F7]">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] flex items-center justify-center text-[#1D1D1F] shrink-0">
                      <Icon size={18} />
                    </div>
                    <span className="text-base font-bold text-[#1D1D1F] truncate">
                      {record.component}
                    </span>
                  </div>

                  <span
                    className={`text-xs font-semibold px-2.5 py-1 rounded-full flex items-center gap-1.5 shrink-0 ${
                      isGood
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200/80"
                        : isAttention
                        ? "bg-amber-50 text-amber-700 border border-amber-200/80"
                        : "bg-rose-50 text-rose-700 border border-rose-200/80"
                    }`}
                  >
                    {isGood && <CheckCircle2 size={13} />}
                    {isAttention && <AlertTriangle size={13} />}
                    {isService && <AlertTriangle size={13} />}
                    {isGood ? "Good" : isAttention ? "Needs Attention" : "Service Required"}
                  </span>
                </div>

                {/* Metric / Condition Headline */}
                <div className="mb-2">
                  <span className="text-sm font-semibold text-[#1D1D1F]">
                    {headline}
                  </span>
                </div>

                {/* Primary Observation / Summary */}
                <p className="text-[13px] text-[#515154] leading-relaxed mb-4">
                  {cleanedSummary}
                </p>

                {/* Human-readable observations if available */}
                {descriptiveEvidence.length > 0 && (
                  <div className="space-y-1.5 mb-3">
                    {descriptiveEvidence.map((ev, evIdx) => (
                      <div
                        key={evIdx}
                        className="text-xs text-[#6E6E73] flex items-start gap-1.5"
                      >
                        <span className="text-[#0071E3] font-bold mt-0.5">•</span>
                        <span>{ev.text}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Clean Footer: Clean Source Badges + Provenance Indicator */}
              <div className="pt-3.5 mt-2 border-t border-[#F2F2F5] flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {deduplicatedSources.map((st) => (
                    <span
                      key={st.key}
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-md flex items-center gap-1 ${
                        st.category === "diagnostic"
                          ? "bg-blue-50 text-blue-700 border border-blue-200/70"
                          : st.category === "visual"
                          ? "bg-purple-50 text-purple-700 border border-purple-200/70"
                          : st.category === "user"
                          ? "bg-amber-50 text-amber-700 border border-amber-200/70"
                          : "bg-slate-50 text-slate-700 border border-slate-200/70"
                      }`}
                    >
                      {st.category === "visual" && <Camera size={11} />}
                      {st.category === "diagnostic" && <Activity size={11} />}
                      {st.category === "user" && <User size={11} />}
                      {st.category === "specs" && <Wrench size={11} />}
                      <span>{st.label}</span>
                    </span>
                  ))}
                </div>

                <div className="text-[11px] text-[#86868B] flex items-center gap-1">
                  <ShieldCheck size={12} className="text-[#0071E3]" />
                  <span>
                    {rawEvidenceCount} {rawEvidenceCount === 1 ? "data point" : "data points"}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Statement & Optimizer Primary CTA */}
      <div className="apple-card p-8 sm:p-10 bg-white border-2 border-[#0071E3]/30 shadow-lg text-center max-w-3xl mx-auto rounded-3xl">
        <div className="w-12 h-12 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-6 h-6" />
        </div>

        <h3 className="text-2xl font-bold text-[#1D1D1F] tracking-tight mb-2">
          ReLoop has evaluated {fullDeviceName}&apos;s condition.
        </h3>

        <p className="text-sm text-[#6E6E73] max-w-xl mx-auto mb-8 leading-relaxed">
          Your condition profile is saved. Now pass your evidence into ReLoop&apos;s Circular Path Optimizer to calculate repair, upgrade, refurbish, or reuse ROI.
        </p>

        <Link
          href={`/engine?assessment_id=${assessmentId}`}
          className="inline-flex items-center gap-2.5 px-9 py-4 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-base font-semibold transition-all duration-200 shadow-lg hover:shadow-xl cursor-pointer"
        >
          <span>Find my device&apos;s next life</span>
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  );
};
