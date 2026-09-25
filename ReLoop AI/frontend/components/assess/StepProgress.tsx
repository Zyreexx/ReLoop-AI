"use client";

import React from "react";
import { Check } from "lucide-react";

interface StepProgressProps {
  currentStep: number;
  onStepClick: (step: number) => void;
}

export const StepProgress: React.FC<StepProgressProps> = ({ currentStep, onStepClick }) => {
  const steps = [
    { num: 1, label: "Visual Inspection", tag: "VISUAL" },
    { num: 2, label: "Diagnostics", tag: "DIAGNOSTIC" },
    { num: 3, label: "User Symptoms", tag: "USER REPORTED" },
    { num: 4, label: "Review", tag: "SUMMARY" },
    { num: 5, label: "Condition Profile", tag: "PROFILE" },
  ];

  return (
    <div className="w-full bg-white border-b border-[#E5E5E7] py-4 px-6 sticky top-[65px] z-40 shadow-xs">
      <div className="max-w-5xl mx-auto flex items-center justify-between overflow-x-auto no-scrollbar gap-3">
        {steps.map((s, idx) => {
          const isDone = currentStep > s.num;
          const isActive = currentStep === s.num;
          const isClickable = s.num < currentStep;

          return (
            <React.Fragment key={s.num}>
              <button
                type="button"
                disabled={!isClickable && !isActive}
                onClick={() => isClickable && onStepClick(s.num)}
                className={`flex items-center gap-2.5 py-1.5 px-3 rounded-full text-xs font-semibold transition-all shrink-0 ${
                  isActive
                    ? "bg-[#0071E3] text-white shadow-xs"
                    : isDone
                    ? "bg-[#E8E8ED] text-[#1D1D1F] hover:bg-[#D2D2D7] cursor-pointer"
                    : "bg-[#F5F5F7] text-[#86868B] cursor-not-allowed"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
                    isActive
                      ? "bg-white text-[#0071E3]"
                      : isDone
                      ? "bg-[#1D1D1F] text-white"
                      : "bg-[#D2D2D7] text-white"
                  }`}
                >
                  {isDone ? <Check size={12} /> : `0${s.num}`}
                </div>

                <span>{s.label}</span>
              </button>

              {idx < steps.length - 1 && (
                <div
                  className={`h-[2px] w-6 sm:w-10 rounded-full shrink-0 transition-colors ${
                    currentStep > s.num ? "bg-[#1D1D1F]" : "bg-[#E5E5E7]"
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
