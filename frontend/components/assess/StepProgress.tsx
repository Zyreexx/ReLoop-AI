"use client";

import React from "react";
import { Check } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

interface StepProgressProps {
  currentStep: number;
  onStepClick: (step: number) => void;
}

export const StepProgress: React.FC<StepProgressProps> = ({ currentStep, onStepClick }) => {
  const { t } = useLanguage();
  const steps = [
    { num: 1, label: t("assess.stepVisualName", "Visual Inspection"), tag: "VISUAL" },
    { num: 2, label: t("assess.stepDiagName", "Diagnostics"), tag: "DIAGNOSTIC" },
    { num: 3, label: t("assess.stepSymptomsName", "User Symptoms"), tag: "USER REPORTED" },
    { num: 4, label: t("assess.stepReviewName", "Review"), tag: "SUMMARY" },
    { num: 5, label: t("assess.stepProfileName", "Condition Profile"), tag: "PROFILE" },
  ];

  const currentStepObj = steps.find((s) => s.num === currentStep) || steps[0];

  return (
    <div className="w-full bg-white dark:bg-[#1C1C1E] border-b border-[#E5E5E7] dark:border-[#38383A] py-2.5 sm:py-4 px-3 sm:px-6 sticky top-[60px] sm:top-[65px] z-40 shadow-xs max-w-full overflow-hidden">
      {/* Mobile view (< 640px): Native Segmented Bar */}
      <div className="sm:hidden flex flex-col gap-1.5 max-w-full">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-[#0071E3] font-bold">
            Step {currentStep} of {steps.length}
          </span>
          <span className="text-[#1D1D1F] dark:text-[#F5F5F7] truncate max-w-[190px]">
            {currentStepObj.label}
          </span>
        </div>
        <div className="flex items-center gap-1.5 w-full">
          {steps.map((s) => {
            const isDone = currentStep > s.num;
            const isActive = currentStep === s.num;
            const isClickable = s.num < currentStep;
            return (
              <button
                key={s.num}
                type="button"
                disabled={!isClickable && !isActive}
                onClick={() => isClickable && onStepClick(s.num)}
                aria-label={`Step ${s.num}: ${s.label}`}
                className={`flex-1 h-2 rounded-full transition-all ${
                  isActive
                    ? "bg-[#0071E3] ring-2 ring-[#0071E3]/30"
                    : isDone
                    ? "bg-[#1D1D1F] dark:bg-white hover:opacity-80 cursor-pointer"
                    : "bg-[#E5E5E7] dark:bg-[#38383A] cursor-not-allowed"
                }`}
              />
            );
          })}
        </div>
      </div>

      {/* Tablet & Desktop view (>= 640px): Numbered Stepper */}
      <div className="hidden sm:flex max-w-5xl mx-auto items-center justify-center gap-2 sm:gap-3 overflow-x-auto no-scrollbar max-w-full">
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
                className={`flex items-center gap-2 py-1.5 px-3 rounded-full text-xs font-semibold transition-all shrink-0 ${
                  isActive
                    ? "bg-[#0071E3] text-white shadow-xs"
                    : isDone
                    ? "bg-[#E8E8ED] dark:bg-[#2C2C2E] text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-[#D2D2D7] dark:hover:bg-[#38383A] cursor-pointer"
                    : "bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-[#86868B] dark:text-[#8E8E93] cursor-not-allowed"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] sm:text-[11px] font-bold shrink-0 ${
                    isActive
                      ? "bg-white text-[#0071E3]"
                      : isDone
                      ? "bg-[#1D1D1F] dark:bg-white text-white dark:text-[#1D1D1F]"
                      : "bg-[#D2D2D7] dark:bg-[#38383A] text-white"
                  }`}
                >
                  {isDone ? <Check size={12} /> : `0${s.num}`}
                </div>

                <span>{s.label}</span>
              </button>

              {idx < steps.length - 1 && (
                <div
                  className={`h-[2px] w-4 sm:w-6 md:w-10 rounded-full shrink-0 transition-colors ${
                    currentStep > s.num ? "bg-[#1D1D1F] dark:bg-white" : "bg-[#E5E5E7] dark:bg-[#38383A]"
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
