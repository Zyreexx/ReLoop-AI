import React, { useState } from "react";
import { DollarSign, Clock, Leaf, Zap, ShieldAlert, ArrowRight } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

interface DeviceCase {
  id: string;
  name: string;
  year: number;
  specs: string;
  flaws: string[];
  batteryHealth: number;
  motherboardOk: boolean;
  screenOk: boolean;
  upgradeableSlots: boolean;
  costRepair: number;
  costUpgrade: number;
  costRefurbish: number;
  costNewDevice: number;
}

export const InteractiveEngineSection: React.FC<{ onOpenAuth: (mode: "login" | "register") => void }> = ({
  onOpenAuth,
}) => {
  const { t } = useLanguage();
  const [selectedDevice, setSelectedDevice] = useState<string>("dell5420");
  const [objective, setObjective] = useState<"cost" | "life" | "carbon" | "speed">("life");

  const devices: Record<string, DeviceCase> = {
    dell5420: {
      id: "dell5420",
      name: "Dell Latitude 5420",
      year: 2021,
      specs: "Intel i5-1145G7 • 16GB DDR4 • 512GB NVMe",
      flaws: [
        t("engine.dell.flaw1", "Battery drops to 0% in 40 mins (73% health)"),
        t("engine.dell.flaw2", "CPU thermal throttles at 88°C under load"),
        t("engine.dell.flaw3", "2 loose plastic keys"),
      ],
      batteryHealth: 73,
      motherboardOk: true,
      screenOk: true,
      upgradeableSlots: true,
      costRepair: 3800,
      costUpgrade: 6200,
      costRefurbish: 7500,
      costNewDevice: 58000,
    },
    thinkpadT480: {
      id: "thinkpadT480",
      name: "Lenovo ThinkPad T480",
      year: 2018,
      specs: "Intel i5-8250U • 8GB RAM • 256GB SATA",
      flaws: [
        t("engine.thinkpad.flaw1", "Main motherboard power circuit fault"),
        t("engine.thinkpad.flaw2", "Cracked LCD panel"),
        t("engine.thinkpad.flaw3", "Internal bridge battery dead"),
      ],
      batteryHealth: 0,
      motherboardOk: false,
      screenOk: false,
      upgradeableSlots: true,
      costRepair: 24000,
      costUpgrade: 14000,
      costRefurbish: 29000,
      costNewDevice: 45000,
    },
    macbookAir: {
      id: "macbookAir",
      name: "MacBook Air M1",
      year: 2020,
      specs: "Apple M1 • 8GB Unified • 256GB SSD",
      flaws: [
        t("engine.mac.flaw1", "Light scratch on lid"),
        t("engine.mac.flaw2", "User upgraded to M3 MacBook Pro for 4K video editing"),
      ],
      batteryHealth: 85,
      motherboardOk: true,
      screenOk: true,
      upgradeableSlots: false,
      costRepair: 0,
      costUpgrade: 0,
      costRefurbish: 2500,
      costNewDevice: 89000,
    },
  };

  const currentDev = devices[selectedDevice];

  // Deterministic Scoring Calculator according to rules in architecture.md
  // w1*Life + w2*Value + w3*Material + w4*Env - w5*Cost - w6*Logistics
  const calculatePathways = () => {
    if (!currentDev.motherboardOk) {
      // Motherboard dead and screen dead
      return [
        {
          name: t("engine.thinkpad.p1Name", "Component Recovery"),
          eligible: true,
          score: 89,
          lifeExt: t("engine.thinkpad.p1Life", "Harvest 256GB SSD + 8GB RAM"),
          cost: t("engine.thinkpad.p1Cost", "₹0 (Salvation yield: ₹5,400)"),
          co2: t("engine.thinkpad.p1Co2", "62 kg CO₂ avoided"),
          turnaround: "24 hours",
          reason: t(
            "engine.thinkpad.p1Reason",
            "Repairing both motherboard & screen exceeds residual laptop value. Recovering operational SSD & RAM maximizes circular material utility."
          ),
          recommended: true,
        },
        {
          name: t("engine.thinkpad.p2Name", "Recycling (Smelting)"),
          eligible: true,
          score: 58,
          lifeExt: t("engine.thinkpad.p2Life", "Raw Material Only"),
          cost: t("engine.thinkpad.p2Cost", "Free e-waste dropoff"),
          co2: t("engine.thinkpad.p2Co2", "22 kg CO₂ avoided"),
          turnaround: "Instant",
          reason: t(
            "engine.thinkpad.p2Reason",
            "Recycles non-harvestable chassis remnants after components are stripped."
          ),
          recommended: false,
        },
        {
          name: t("engine.thinkpad.p3Name", "Repair & Overhaul"),
          eligible: false,
          score: 18,
          lifeExt: t("engine.thinkpad.p3Life", "+1.5 Years"),
          cost: t("engine.thinkpad.p3Cost", `₹${currentDev.costRepair.toLocaleString()}`),
          co2: t("engine.thinkpad.p3Co2", "85 kg CO₂"),
          turnaround: "7-10 days",
          reason: t(
            "engine.thinkpad.p3Reason",
            "Ineligible: Motherboard replacement cost exceeds 70% of device market value."
          ),
          recommended: false,
        },
      ];
    }

    if (selectedDevice === "macbookAir") {
      return [
        {
          name: t("engine.mac.p1Name", "Reuse / Redeploy"),
          eligible: true,
          score: 94,
          lifeExt: t("engine.mac.p1Life", "+3.5 Years"),
          cost: t("engine.mac.p1Cost", "₹0"),
          co2: t("engine.mac.p1Co2", "185 kg CO₂ avoided"),
          turnaround: "Instant",
          reason: t(
            "engine.mac.p1Reason",
            "Silicon health is 100% and battery is healthy at 85%. Perfect candidate for student or administrative redeployment."
          ),
          recommended: true,
        },
        {
          name: t("engine.mac.p2Name", "Certified Refurbish"),
          eligible: true,
          score: 82,
          lifeExt: t("engine.mac.p2Life", "+3.5 Years"),
          cost: t("engine.mac.p2Cost", "₹2,500 (Sanitize + Box)"),
          co2: t("engine.mac.p2Co2", "180 kg CO₂ avoided"),
          turnaround: "2 days",
          reason: t("engine.mac.p2Reason", "Deep clean and recertify for resale at ₹52,000."),
          recommended: false,
        },
        {
          name: t("engine.mac.p3Name", "Component Recovery"),
          eligible: false,
          score: 12,
          lifeExt: t("engine.mac.p3Life", "Destructive"),
          cost: t("engine.mac.p3Cost", "High loss"),
          co2: t("engine.mac.p3Co2", "Negative"),
          turnaround: "N/A",
          reason: t(
            "engine.mac.p3Reason",
            "Ineligible: Functioning MacBook Air should never be scrapped for parts."
          ),
          recommended: false,
        },
      ];
    }

    // Default Dell 5420
    return [
      {
        name: t("engine.dell.p1Name", "Repair (Battery + Thermal Repaste)"),
        eligible: true,
        score: objective === "cost" ? 95 : 91,
        lifeExt: t("engine.dell.p1Life", "+2.5 Years"),
        cost: t("engine.dell.p1Cost", "₹3,800"),
        co2: t("engine.dell.p1Co2", "145 kg CO₂ avoided"),
        turnaround: "1-2 days",
        reason: t(
          "engine.dell.p1Reason",
          "Eliminates thermal throttling and restores 7-hour battery runtime. Highest ROI pathway."
        ),
        recommended: objective !== "life",
      },
      {
        name: t("engine.dell.p2Name", "Repair + Upgrade (Battery + 32GB RAM)"),
        eligible: true,
        score: objective === "life" ? 96 : 88,
        lifeExt: t("engine.dell.p2Life", "+3.5 Years"),
        cost: t("engine.dell.p2Cost", "₹6,200"),
        co2: t("engine.dell.p2Co2", "158 kg CO₂ avoided"),
        turnaround: "2 days",
        reason: t(
          "engine.dell.p2Reason",
          "Extends performance headroom for modern multitasking alongside fresh battery."
        ),
        recommended: objective === "life",
      },
      {
        name: t("engine.dell.p3Name", "Secondary Reuse / Redeploy"),
        eligible: true,
        score: 74,
        lifeExt: t("engine.dell.p3Life", "+1.5 Years (Plugged-in role)"),
        cost: t("engine.dell.p3Cost", "₹0"),
        co2: t("engine.dell.p3Co2", "135 kg CO₂ avoided"),
        turnaround: "Instant",
        reason: t(
          "engine.dell.p3Reason",
          "Use as desktop replacement with AC adapter plugged in; leaves battery problem unaddressed."
        ),
        recommended: false,
      },
      {
        name: t("engine.dell.p4Name", "Direct Recycling"),
        eligible: false,
        score: 15,
        lifeExt: t("engine.dell.p4Life", "0 Years"),
        cost: t("engine.dell.p4Cost", "₹58,000 New Laptop needed"),
        co2: t("engine.dell.p4Co2", "Heavy Net Emission"),
        turnaround: "Immediate",
        reason: t(
          "engine.dell.p4Reason",
          "Ineligible: Perfectly healthy i5-11th gen motherboard and display must not be shredded."
        ),
        recommended: false,
      },
    ];
  };

  const pathwayResults = calculatePathways();

  return (
    <section id="live-engine" className="py-24 md:py-36 bg-white border-b border-[#E5E5E7] relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Section Header with Index Marker */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F5F5F7] border border-[#E5E5E7] text-[11px] font-mono font-bold text-[#6E6E73] mb-4">
            <span>{t("engine.sectionNum", "SECTION 03")}</span>
            <span>•</span>
            <span className="text-[#0071E3]">{t("engine.badge")}</span>
          </div>
          <h2 className="text-[34px] sm:text-[46px] md:text-[52px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            {t("engine.title")}
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            {t("engine.subtitle")}
          </p>
        </div>

        {/* Simulator Container */}
        <div className="apple-card p-6 sm:p-10 max-w-5xl mx-auto bg-[#FBFBFD] border border-[#E5E5E7]">
          {/* Controls Bar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-8 border-b border-[#E5E5E7]">
            {/* Device Picker */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#6E6E73] mb-2">
                {t("engine.selectHardware", "1. Select Hardware Test Case")}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {Object.values(devices).map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setSelectedDevice(d.id)}
                    className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                      selectedDevice === d.id
                        ? "bg-white border-[#0071E3] shadow-xs"
                        : "bg-[#F5F5F7] border-transparent hover:bg-white text-[#6E6E73]"
                    }`}
                  >
                    <span className="text-xs font-bold text-[#1D1D1F] block truncate">
                      {d.name}
                    </span>
                    <span className="text-[10px] text-[#86868B] block mt-0.5">
                      {d.year}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Objective Picker */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#6E6E73] mb-2">
                {t("engine.setObjective", "2. Set Decision Objective")}
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { key: "life", label: t("hero.objLife", "Max Life"), icon: Clock },
                  { key: "cost", label: t("hero.objCost", "Lowest Cost"), icon: DollarSign },
                  { key: "carbon", label: t("hero.objCarbon", "Eco Impact"), icon: Leaf },
                  { key: "speed", label: t("hero.objFast", "Fastest Turn"), icon: Zap },
                ].map((obj) => {
                  const Icon = obj.icon;
                  const isSelected = objective === obj.key;
                  return (
                    <button
                      key={obj.key}
                      type="button"
                      onClick={() => setObjective(obj.key as any)}
                      className={`p-2.5 rounded-xl border flex flex-col items-center justify-center gap-1 transition-all cursor-pointer ${
                        isSelected
                          ? "bg-[#1D1D1F] text-white border-[#1D1D1F]"
                          : "bg-white text-[#6E6E73] border-[#E5E5E7] hover:border-[#D2D2D7]"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-[11px] font-semibold text-center leading-tight">{obj.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Current Device Symptoms & Diagnostics Banner */}
          <div className="py-6 border-b border-[#E5E5E7]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
              <div>
                <span className="text-sm font-bold text-[#1D1D1F]">{currentDev.name}</span>
                <span className="text-xs text-[#6E6E73] ml-2">({currentDev.specs})</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                  {t("engine.batteryLabel", "Battery")}: {currentDev.batteryHealth}%
                </span>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-md ${
                    currentDev.motherboardOk
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : "bg-rose-50 text-rose-700 border border-rose-200"
                  }`}
                >
                  {t("engine.motherboardLabel", "Motherboard")}: {currentDev.motherboardOk ? t("engine.intact", "Intact") : t("engine.faultDetected", "Fault Detected")}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {currentDev.flaws.map((flaw, i) => (
                <span
                  key={i}
                  className="text-xs px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200/60 flex items-center gap-1"
                >
                  <ShieldAlert className="w-3 h-3 text-amber-600" />
                  {flaw}
                </span>
              ))}
            </div>
          </div>

          {/* Scored Pathways Comparison */}
          <div className="pt-8">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-[#6E6E73]">
                {t("engine.rankingTitle", "Deterministic Ranking & Circular Value Score")}
              </span>
              <span className="text-xs text-[#0071E3] font-semibold">
                {t("engine.objectiveLabel", "Objective")}: {objective.toUpperCase()}
              </span>
            </div>

            <div className="space-y-3">
              {pathwayResults.map((path, idx) => (
                <div
                  key={idx}
                  className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                    path.recommended
                      ? "bg-white border-[#0071E3] shadow-md ring-2 ring-[#0071E3]/20"
                      : path.eligible
                      ? "bg-white/80 border-[#E5E5E7] opacity-90"
                      : "bg-[#F5F5F7] border-[#E5E5E7] opacity-60"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          path.recommended
                            ? "bg-[#0071E3] text-white"
                            : "bg-[#E5E5E7] text-[#6E6E73]"
                        }`}
                      >
                        #{idx + 1}
                      </span>
                      <h4 className="text-base font-bold text-[#1D1D1F]">
                        {path.name}
                      </h4>
                      {path.recommended && (
                        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#0071E3] text-white tracking-wider">
                          {t("engine.optimalBadge", "Optimal Next Life")}
                        </span>
                      )}
                      {!path.eligible && (
                        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#FF3B30]/10 text-[#FF3B30] border border-[#FF3B30]/20">
                          {t("engine.ineligibleBadge", "Ineligible")}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-xs">
                      <div>
                        <span className="text-[#86868B] block text-[10px]">{t("engine.lifeAdded", "Life Added")}</span>
                        <span className="font-semibold text-[#1D1D1F]">{path.lifeExt}</span>
                      </div>
                      <div>
                        <span className="text-[#86868B] block text-[10px]">{t("engine.cost", "Cost")}</span>
                        <span className="font-semibold text-[#1D1D1F]">{path.cost}</span>
                      </div>
                      <div>
                        <span className="text-[#86868B] block text-[10px]">{t("engine.score", "Score")}</span>
                        <span
                          className={`font-bold ${
                            path.recommended ? "text-[#0071E3] text-sm" : "text-[#6E6E73]"
                          }`}
                        >
                          {path.score} / 100
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-[#6E6E73] leading-relaxed mt-2 pl-8">
                    {path.reason}
                  </p>
                </div>
              ))}
            </div>

            {/* Bottom CTA */}
            <div className="mt-8 pt-6 border-t border-[#E5E5E7] flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs text-[#6E6E73] text-center sm:text-left">
                {t("engine.ctaQuestion", "Want to evaluate your own device using real photos and telemetry?")}
              </span>
              <button
                type="button"
                onClick={() => onOpenAuth("register")}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
              >
                <span>{t("engine.ctaBtn", "Launch Device Scanner")}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
