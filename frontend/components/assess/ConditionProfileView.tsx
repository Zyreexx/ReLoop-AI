"use client";

import React from "react";
import Link from "next/link";
import { ComponentConditionRecord } from "@/types/assessment";
import { CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, BatteryCharging, HardDrive, Cpu, Flame, Layers, Wrench, Sparkles } from "lucide-react";

interface ConditionProfileViewProps {
  conditionProfile: ComponentConditionRecord[];
  confirmedModelName: string;
  manufacturer: string;
  assessmentId: string;
}

export const ConditionProfileView: React.FC<ConditionProfileViewProps> = ({
  conditionProfile,
  confirmedModelName,
  manufacturer,
  assessmentId,
}) => {
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

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Top Banner */}
      <div className="mb-8 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#34C759]/10 text-[#34C759] border border-[#34C759]/20 text-xs font-bold mb-3">
          <CheckCircle2 size={14} />
          <span>CONDITION PROFILE GENERATED</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-[#1D1D1F] tracking-tight">
          Your device condition profile
        </h2>
        <p className="text-[#6E6E73] text-sm sm:text-base mt-2">
          Component-level health evaluation synthesized from visual, diagnostic, and user-reported evidence for <strong>{manufacturer} {confirmedModelName}</strong>.
        </p>
      </div>

      {/* Grid of Component Condition Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        {conditionProfile.map((record, idx) => {
          const Icon = getComponentIcon(record.component);
          const isGood = record.status === "good";
          const isAttention = record.status === "needs_attention";
          const isService = record.status === "needs_service" || record.status === "fault";

          return (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-white border border-[#E5E5E7] shadow-2xs hover:border-[#D2D2D7] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] flex items-center justify-center text-[#1D1D1F]">
                      <Icon size={16} />
                    </div>
                    <span className="text-sm font-bold text-[#1D1D1F]">
                      {record.component}
                    </span>
                  </div>

                  <div className="flex gap-1">
                    {record.sourceTypes.map((st, sidx) => (
                      <span
                        key={sidx}
                        className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded ${
                          st === "DIAGNOSTIC"
                            ? "bg-blue-50 text-blue-700 border border-blue-200"
                            : st === "VISUAL"
                            ? "bg-purple-50 text-purple-700 border border-purple-200"
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}
                      >
                        {st}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-sm font-bold text-[#1D1D1F]">
                    {record.statusLabel}
                  </span>
                  <span
                    className={`text-xs font-semibold flex items-center gap-1 ${
                      isGood
                        ? "text-[#34C759]"
                        : isAttention
                        ? "text-[#FF9F0A]"
                        : "text-[#FF3B30]"
                    }`}
                  >
                    {isGood && <CheckCircle2 size={13} />}
                    {isAttention && <AlertTriangle size={13} />}
                    {isService && <AlertTriangle size={13} />}
                    {isGood ? "Good" : isAttention ? "Needs Attention" : "Needs Service"}
                  </span>
                </div>

                <p className="text-xs text-[#6E6E73] leading-relaxed mb-3">
                  {record.summary}
                </p>
              </div>

              {/* Evidence details bullet point */}
              <div className="pt-3 border-t border-[#F0F0F2]">
                {record.evidence.map((ev, evIdx) => (
                  <div key={evIdx} className="text-[11px] text-[#86868B] flex items-start gap-1.5">
                    <span className="text-[#0071E3] font-bold">•</span>
                    <span>{ev.text}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Statement & Optimizer Primary CTA */}
      <div className="apple-card p-8 bg-white border-2 border-[#0071E3]/30 shadow-lg text-center max-w-3xl mx-auto">
        <div className="w-12 h-12 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-6 h-6" />
        </div>

        <h3 className="text-2xl font-bold text-[#1D1D1F] tracking-tight mb-2">
          ReLoop has enough evidence to evaluate your device&apos;s next-life pathways.
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
