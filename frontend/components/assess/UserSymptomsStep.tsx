"use client";

import React, { useState } from "react";
import { UserObjective, UserSymptomItem, UserSymptomsData } from "@/types/assessment";
import { Check, DollarSign, Clock, Leaf, Zap, ArrowLeft } from "lucide-react";

interface UserSymptomsStepProps {
  initialData: UserSymptomsData;
  onComplete: (data: UserSymptomsData) => void;
  onBack?: () => void;
}

const AVAILABLE_SYMPTOMS = [
  { id: "battery_drain", label: "Battery drains quickly" },
  { id: "overheating", label: "Device overheats" },
  { id: "random_shutdown", label: "Random shutdowns" },
  { id: "slow_performance", label: "Slow performance" },
  { id: "system_crashes", label: "System crashes" },
  { id: "display", label: "Display issues" },
  { id: "keyboard", label: "Keyboard issues" },
  { id: "trackpad", label: "Trackpad issues" },
  { id: "charging", label: "Charging issues" },
  { id: "connectivity", label: "Wi-Fi / Bluetooth issues" },
  { id: "hinge", label: "Hinge / chassis damage" },
  { id: "storage", label: "Storage issues" },
  { id: "fan_noise", label: "Fan noise" },
  { id: "other", label: "Other" },
];

export const UserSymptomsStep: React.FC<UserSymptomsStepProps> = ({
  initialData,
  onComplete,
  onBack,
}) => {
  const [selectedMap, setSelectedMap] = useState<
    Record<string, "never" | "occasionally" | "frequently" | "almost_always">
  >(() => {
    const map: Record<string, any> = {};
    if (initialData?.selectedSymptoms) {
      for (const item of initialData.selectedSymptoms) {
        map[item.symptomId] = item.frequency;
      }
    } else {
      // Default sample pre-checked items for smooth testing experience
      map["battery_drain"] = "frequently";
      map["overheating"] = "occasionally";
    }
    return map;
  });

  const [description, setDescription] = useState<string>(
    initialData.userDescription ||
      "The laptop works normally when plugged in, but battery drops rapidly after 30 minutes. Noticeable heat near the hinge under multi-tab browsing."
  );

  const [objective, setObjective] = useState<UserObjective>(
    initialData.userObjective || "max_life"
  );

  const toggleSymptom = (symptomId: string) => {
    setSelectedMap((prev) => {
      const updated = { ...prev };
      if (updated[symptomId]) {
        delete updated[symptomId];
      } else {
        updated[symptomId] = "frequently";
      }
      return updated;
    });
  };

  const updateFrequency = (
    symptomId: string,
    freq: "never" | "occasionally" | "frequently" | "almost_always"
  ) => {
    setSelectedMap((prev) => ({
      ...prev,
      [symptomId]: freq,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const selectedSymptomsList: UserSymptomItem[] = Object.keys(selectedMap).map((id) => {
      const found = AVAILABLE_SYMPTOMS.find((s) => s.id === id);
      return {
        symptomId: id,
        label: found ? found.label : id,
        frequency: selectedMap[id],
      };
    });

    onComplete({
      selectedSymptoms: selectedSymptomsList,
      userDescription: description,
      userObjective: objective,
    });
  };

  const objectiveOptions = [
    {
      id: "lowest_cost",
      title: "Lowest cost",
      desc: "Minimize direct repair & upgrade expenditure",
      icon: DollarSign,
    },
    {
      id: "max_life",
      title: "Maximum remaining life",
      desc: "Extend device operational life as long as possible",
      icon: Clock,
    },
    {
      id: "environmental",
      title: "Best environmental outcome",
      desc: "Maximize material retention and CO₂ reduction",
      icon: Leaf,
    },
    {
      id: "fastest_recovery",
      title: "Fastest way to get usable",
      desc: "Minimize downtime to resume productivity immediately",
      icon: Zap,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-200 mb-2 inline-block">
          USER REPORTED EVIDENCE
        </span>
        <h2 className="text-3xl font-bold text-[#1D1D1F] tracking-tight">3. User Symptoms</h2>
        <p className="text-[#6E6E73] text-sm sm:text-base mt-1">
          Tell us what you&apos;ve noticed while using the device.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* 8A Checkboxes */}
        <div className="apple-card p-6 bg-white">
          <h3 className="text-base font-bold text-[#1D1D1F] mb-1">
            Symptoms & Behaviors Observed
          </h3>
          <p className="text-xs text-[#6E6E73] mb-6">
            Select all issues that apply to your device experience.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            {AVAILABLE_SYMPTOMS.map((sym) => {
              const isSelected = Boolean(selectedMap[sym.id]);
              return (
                <div
                  key={sym.id}
                  className={`p-3.5 rounded-xl border transition-all ${
                    isSelected
                      ? "border-[#0071E3] bg-[#0071E3]/5"
                      : "border-[#E5E5E7] bg-[#FBFBFD] hover:bg-white"
                  }`}
                >
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSymptom(sym.id)}
                      className="w-4 h-4 rounded text-[#0071E3]"
                    />
                    <span className="text-xs font-bold text-[#1D1D1F] flex-1">
                      {sym.label}
                    </span>
                  </label>

                  {/* 8B Frequency Selector if selected */}
                  {isSelected && (
                    <div className="mt-3 pt-2 border-t border-[#E5E5E7] flex items-center justify-between gap-1">
                      <span className="text-[10px] font-semibold text-[#86868B]">Frequency:</span>
                      <div className="flex gap-1">
                        {(["occasionally", "frequently", "almost_always"] as const).map((freq) => (
                          <button
                            key={freq}
                            type="button"
                            onClick={() => updateFrequency(sym.id, freq)}
                            className={`px-2 py-0.5 rounded text-[10px] font-medium transition-all ${
                              selectedMap[sym.id] === freq
                                ? "bg-[#1D1D1F] text-white"
                                : "bg-white text-[#6E6E73] border border-[#D2D2D7]"
                            }`}
                          >
                            {freq === "occasionally" ? "Occasional" : freq === "frequently" ? "Frequent" : "Constant"}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 8C Free Text Description */}
        <div className="apple-card p-6 bg-white">
          <h3 className="text-base font-bold text-[#1D1D1F] mb-1">
            Additional User Description
          </h3>
          <p className="text-xs text-[#6E6E73] mb-3">
            Describe anything else you&apos;ve noticed about performance, battery, or physical state.
          </p>

          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Example: The laptop works normally when plugged in but shuts down after about 30 minutes on battery."
            className="w-full p-3 rounded-xl border border-[#D2D2D7] text-sm text-[#1D1D1F] focus:outline-none focus:border-[#0071E3]"
          />
        </div>

        {/* 8D User Objective */}
        <div className="apple-card p-6 bg-white">
          <h3 className="text-base font-bold text-[#1D1D1F] mb-1">
            What matters most to you?
          </h3>
          <p className="text-xs text-[#6E6E73] mb-6">
            This objective feeds into ReLoop&apos;s Circular Path Optimizer stage.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {objectiveOptions.map((opt) => {
              const Icon = opt.icon;
              const isSelected = objective === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setObjective(opt.id as UserObjective)}
                  className={`p-4 rounded-2xl border text-left transition-all cursor-pointer flex items-start gap-3.5 ${
                    isSelected
                      ? "border-[#0071E3] bg-[#0071E3]/5 ring-2 ring-[#0071E3]/20 shadow-xs"
                      : "border-[#E5E5E7] bg-[#FBFBFD] hover:bg-white"
                  }`}
                >
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                      isSelected ? "bg-[#0071E3] text-white" : "bg-white border border-[#E5E5E7] text-[#6E6E73]"
                    }`}
                  >
                    <Icon size={18} />
                  </div>
                  <div>
                    <span className="text-sm font-bold text-[#1D1D1F] block mb-0.5">
                      {opt.title}
                    </span>
                    <span className="text-xs text-[#6E6E73] leading-relaxed block">
                      {opt.desc}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Submit Step */}
        <div className="flex items-center justify-between pt-4 gap-4">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full border border-[#D2D2D7] bg-white hover:bg-[#F5F5F7] text-[#1D1D1F] text-sm font-semibold transition-all shadow-xs cursor-pointer"
            >
              <ArrowLeft size={16} />
              <span>Back to Diagnostics</span>
            </button>
          ) : <div />}
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer ml-auto"
          >
            <span>Review Assessment →</span>
          </button>
        </div>
      </form>
    </div>
  );
};
