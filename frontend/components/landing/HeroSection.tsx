"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  BatteryCharging,
  Cpu,
  HardDrive,
  Flame,
  CheckCircle,
  AlertTriangle,
  Sparkles,
  Layers,
  Wrench,
  ShieldCheck,
  Laptop,
  Repeat,
  PackageOpen,
} from "lucide-react";

interface HeroSectionProps {
  onOpenAuth: (mode: "login" | "register") => void;
}

interface MarqueeLaptop {
  id: string;
  brand: string;
  model: string;
  specs: string;
  condition: string;
  conditionType: "good" | "warning" | "bad";
  pathway: string;
  pathwayColor: string;
  impact: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onOpenAuth }) => {
  const [activeTab, setActiveTab] = useState<"dell" | "mac" | "thinkpad">("dell");

  // Line 1 Laptops (Moving Left)
  const line1Laptops: MarqueeLaptop[] = [
    {
      id: "mbp16",
      brand: "Apple",
      model: "MacBook Pro 16\" (M1 Max)",
      specs: "32GB Unified • 1TB SSD",
      condition: "Battery: 81% • Normal Service",
      conditionType: "good",
      pathway: "REUSE / REDEPLOY",
      pathwayColor: "bg-blue-50 text-blue-700 border-blue-200",
      impact: "+3.5 Yrs Life • 94% Value",
    },
    {
      id: "xps15",
      brand: "Dell",
      model: "XPS 15 (9500)",
      specs: "Intel i7-10750H • 16GB • 512GB",
      condition: "Battery: 68% • Thermal Repaste Needed",
      conditionType: "warning",
      pathway: "REPAIR + UPGRADE",
      pathwayColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      impact: "+2.5 Yrs Life • 85% Savings",
    },
    {
      id: "x1c",
      brand: "Lenovo",
      model: "ThinkPad X1 Carbon Gen 9",
      specs: "Intel i5-1135G7 • 16GB LPDDR4x",
      condition: "Flawless Board • Minor Lid Scuff",
      conditionType: "good",
      pathway: "CERTIFIED REFURB",
      pathwayColor: "bg-purple-50 text-purple-700 border-purple-200",
      impact: "+3.0 Yrs Life • 88% Value",
    },
    {
      id: "framework13",
      brand: "Framework",
      model: "Laptop 13 Modular",
      specs: "AMD Ryzen 5 7640U • 32GB DDR5",
      condition: "Mainboard Upgradeable • 96% Health",
      conditionType: "good",
      pathway: "MODULAR UPGRADE",
      pathwayColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      impact: "+4.0 Yrs Life • 95% Savings",
    },
    {
      id: "spectre14",
      brand: "HP",
      model: "Spectre x360 14",
      specs: "Intel i7-1165G7 • OLED Touch",
      condition: "Hinge Loose • Battery Degraded",
      conditionType: "warning",
      pathway: "REPAIR (HINGE + CELL)",
      pathwayColor: "bg-amber-50 text-amber-700 border-amber-200",
      impact: "+2.0 Yrs Life • 78% Savings",
    },
    {
      id: "zephyrus14",
      brand: "ASUS",
      model: "ROG Zephyrus G14",
      specs: "AMD Ryzen 9 • RTX 3060",
      condition: "GPU Blown • Screen & 1TB NVMe 100%",
      conditionType: "bad",
      pathway: "COMPONENT RECOVERY",
      pathwayColor: "bg-rose-50 text-rose-700 border-rose-200",
      impact: "Harvest NVMe + 32GB RAM",
    },
  ];

  // Line 2 Laptops (Moving Right - OPPOSITE DIRECTION!)
  const line2Laptops: MarqueeLaptop[] = [
    {
      id: "mba_m2",
      brand: "Apple",
      model: "MacBook Air M2 (2022)",
      specs: "8-Core GPU • 16GB • 512GB",
      condition: "Battery: 89% • 100% Operational",
      conditionType: "good",
      pathway: "REDEPLOY TO LAB",
      pathwayColor: "bg-blue-50 text-blue-700 border-blue-200",
      impact: "+4.0 Yrs Life • 91% Value",
    },
    {
      id: "dell5420",
      brand: "Dell",
      model: "Latitude 5420 Enterprise",
      specs: "Intel i5-1145G7 • 16GB DDR4",
      condition: "Battery: 73% • Thermal Throttling",
      conditionType: "warning",
      pathway: "REPAIR + REPASTE",
      pathwayColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      impact: "+2.8 Yrs Life • 86% Savings",
    },
    {
      id: "t480",
      brand: "Lenovo",
      model: "ThinkPad T480 Dual-Battery",
      specs: "Intel i5-8250U • 32GB DDR4",
      condition: "External Cell 0% • Internal Cell 82%",
      conditionType: "warning",
      pathway: "REPAIR (HOT-SWAP CELL)",
      pathwayColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      impact: "+3.0 Yrs Life • 80% Savings",
    },
    {
      id: "surface5",
      brand: "Microsoft",
      model: "Surface Laptop 5",
      specs: "Intel i7-1255U • 16GB • Alcantara",
      condition: "Diagnostics Pass • Cleaned Chassis",
      conditionType: "good",
      pathway: "CERTIFIED REFURB",
      pathwayColor: "bg-purple-50 text-purple-700 border-purple-200",
      impact: "+3.0 Yrs Life • 85% Value",
    },
    {
      id: "elitebook840",
      brand: "HP",
      model: "EliteBook 840 G8",
      specs: "Intel i5-1135G7 • 16GB • 256GB",
      condition: "RAM Upgrade to 32GB + 1TB SSD",
      conditionType: "good",
      pathway: "CAPACITY UPGRADE",
      pathwayColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      impact: "+3.5 Yrs Life • 89% Savings",
    },
    {
      id: "legion5",
      brand: "Lenovo",
      model: "Legion 5 Pro Gaming",
      specs: "Ryzen 7 5800H • Cracked Screen",
      condition: "Liquid Damage • 1TB SSD & RAM Safe",
      conditionType: "bad",
      pathway: "COMPONENT HARVEST",
      pathwayColor: "bg-rose-50 text-rose-700 border-rose-200",
      impact: "Recovered ₹9,200 Parts",
    },
  ];

  // Deep-dive showcase devices
  const devices = {
    dell: {
      name: "Dell Latitude 5420",
      age: "4.5 years old",
      status: "Repair & Upgrade Recommended",
      lifeExtension: "+2.8 Years Useful Life",
      savings: "86% Cost Savings vs New",
      co2Saved: "142 kg CO₂ avoided",
      components: [
        { name: "Battery Health", value: "73% capacity", state: "warning", source: "DIAGNOSTIC", icon: BatteryCharging, note: "Degraded, replacement recommended" },
        { name: "NVMe SSD", value: "91% life remaining", state: "good", source: "DIAGNOSTIC", icon: HardDrive, note: "SMART verified healthy" },
        { name: "Memory (RAM)", value: "16 GB DDR4", state: "good", source: "DIAGNOSTIC", icon: Cpu, note: "Passed memory stress test" },
        { name: "Thermals", value: "88°C under load", state: "warning", source: "DIAGNOSTIC", icon: Flame, note: "Thermal throttling; repaste needed" },
        { name: "Keyboard / Keys", value: "2 loose keys", state: "warning", source: "USER REPORTED", icon: Layers, note: "Key mechanism replacement" },
        { name: "Display Panel", value: "FHD IPS (Flawless)", state: "good", source: "VISUAL", icon: ShieldCheck, note: "Zero dead pixels, no cracks" },
      ],
      pathway: "REPAIR + UPGRADE",
      reason: "Healthy motherboard, display, and memory make whole-system replacement wasteful. Replacing battery and servicing thermal paste restores 100% daily capability.",
    },
    mac: {
      name: "MacBook Air M1 (2020)",
      age: "3.5 years old",
      status: "Reuse / Redeploy Recommended",
      lifeExtension: "+3.5 Years Useful Life",
      savings: "92% Value Retained",
      co2Saved: "185 kg CO₂ avoided",
      components: [
        { name: "Battery Health", value: "84% (412 cycles)", state: "good", source: "DIAGNOSTIC", icon: BatteryCharging, note: "Normal service condition" },
        { name: "SSD Health", value: "96% TBW written", state: "good", source: "DIAGNOSTIC", icon: HardDrive, note: "Apple SMART passed" },
        { name: "Apple M1 SoC", value: "100% functional", state: "good", source: "DIAGNOSTIC", icon: Cpu, note: "Stress benchmark passed" },
        { name: "Chassis", value: "Minor corner scuff", state: "good", source: "VISUAL", icon: ShieldCheck, note: "Exterior cosmetic only" },
        { name: "Thermals", value: "Silent / 42°C", state: "good", source: "DIAGNOSTIC", icon: Flame, note: "Fanless architecture healthy" },
        { name: "Retina Display", value: "TrueTone Active", state: "good", source: "VISUAL", icon: ShieldCheck, note: "No coating delamination" },
      ],
      pathway: "REUSE / REDEPLOY",
      reason: "Hardware integrity is exceptionally high. Optimal next-life is redeployment to students or secondary light-office workflows without hardware changes.",
    },
    thinkpad: {
      name: "Lenovo ThinkPad T480",
      age: "6.2 years old",
      status: "Component Recovery Recommended",
      lifeExtension: "Sub-components Reused",
      savings: "₹8,400 Salvage Value",
      co2Saved: "68 kg CO₂ recovered",
      components: [
        { name: "Motherboard", value: "Power rail fault", state: "bad", source: "DIAGNOSTIC", icon: Cpu, note: "Critical board-level short" },
        { name: "Display Panel", value: "Cracked matrix", state: "bad", source: "VISUAL", icon: ShieldCheck, note: "Physical impact crack" },
        { name: "NVMe 512GB SSD", value: "98% health", state: "good", source: "DIAGNOSTIC", icon: HardDrive, note: "Fully salvageable for external drive" },
        { name: "DDR4 16GB SO-DIMM", value: "PASS", state: "good", source: "DIAGNOSTIC", icon: Layers, note: "Directly reusable in other laptops" },
        { name: "Battery (Bridge)", value: "Dead internal cell", state: "bad", source: "DIAGNOSTIC", icon: BatteryCharging, note: "0Wh held; recycle cell" },
        { name: "Chassis Magnesium", value: "Intact bottom plate", state: "good", source: "VISUAL", icon: Wrench, note: "Salvageable structural parts" },
      ],
      pathway: "COMPONENT RECOVERY",
      reason: "Repairing both motherboard and display exceeds fair market value. Harvesting healthy SSD, RAM, and structural magnesium prevents premature shredding.",
    },
  };

  const current = devices[activeTab];

  // Helper card renderer for marquee ticker
  const renderLaptopTickerCard = (laptop: MarqueeLaptop, keyPrefix: string, index: number) => (
    <div
      key={`${keyPrefix}-${laptop.id}-${index}`}
      className="w-[280px] sm:w-[320px] bg-white rounded-2xl p-4 sm:p-5 border border-[#E5E5E7] shadow-sm hover:shadow-md transition-all duration-300 shrink-0 mx-2.5 sm:mx-3 text-left"
    >
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#F5F5F7] border border-[#E5E5E7] flex items-center justify-center text-[#1D1D1F]">
            <Laptop className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#86868B] block leading-none">
              {laptop.brand}
            </span>
            <span className="text-xs font-bold text-[#1D1D1F] block truncate max-w-[170px]">
              {laptop.model}
            </span>
          </div>
        </div>

        <span
          className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded-full border ${laptop.pathwayColor}`}
        >
          {laptop.pathway}
        </span>
      </div>

      <div className="text-[11px] text-[#6E6E73] truncate mb-2">
        {laptop.specs}
      </div>

      <div className="pt-2 border-t border-[#F0F0F2] flex items-center justify-between text-[11px]">
        <span
          className={`font-medium flex items-center gap-1 ${
            laptop.conditionType === "good"
              ? "text-[#34C759]"
              : laptop.conditionType === "warning"
              ? "text-[#FF9F0A]"
              : "text-[#FF3B30]"
          }`}
        >
          {laptop.conditionType === "good" && <CheckCircle className="w-3 h-3 shrink-0" />}
          {laptop.conditionType === "warning" && <AlertTriangle className="w-3 h-3 shrink-0" />}
          {laptop.conditionType === "bad" && <AlertTriangle className="w-3 h-3 shrink-0" />}
          <span className="truncate max-w-[130px]">{laptop.condition}</span>
        </span>

        <span className="text-[#0071E3] font-semibold text-[10px] shrink-0">
          {laptop.impact}
        </span>
      </div>
    </div>
  );

  return (
    <section id="overview" className="pt-16 pb-24 md:pt-24 md:pb-32 overflow-hidden bg-[#F5F5F7]">
      <div className="max-w-6xl mx-auto px-6">
        {/* Eyebrow badge */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E8E8ED] text-[#1D1D1F] text-[12px] font-medium tracking-wide shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#34C759] animate-pulse" />
            <span>PCCoE International Grand Challenge 2026</span>
            <span className="text-[#86868B]">•</span>
            <span className="text-[#0071E3] font-semibold">Circular Economy</span>
          </div>
        </div>

        {/* Hero Headline */}
        <div className="text-center max-w-4xl mx-auto mb-8">
          <h1 className="text-[40px] sm:text-[54px] md:text-[68px] font-bold text-[#1D1D1F] tracking-tight leading-[1.06] mb-6">
            Don&apos;t replace the whole machine.
            <br />
            <span className="text-[#0071E3]">Give it a next life.</span>
          </h1>
          <p className="text-[18px] sm:text-[21px] text-[#6E6E73] font-normal max-w-2xl mx-auto leading-relaxed">
            Laptops are routinely discarded when just one component slows down.
            ReLoop AI blends photos, hardware diagnostics, and reported symptoms
            to calculate the highest-value circular pathway.
          </p>
        </div>

        {/* CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
          <button
            type="button"
            onClick={() => onOpenAuth("register")}
            className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-[15px] font-semibold transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer"
          >
            <span>Assess Your Laptop</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <a
            href="#live-engine"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full bg-white hover:bg-[#FBFBFD] text-[#1D1D1F] border border-[#D2D2D7] text-[15px] font-medium transition-all duration-200 cursor-pointer shadow-2xs"
          >
            <span>Test Decision Engine</span>
          </a>

          <a
            href="#pathways"
            className="inline-flex items-center gap-1.5 text-[14px] font-medium text-[#0071E3] hover:underline px-3 py-2"
          >
            <span>See the 6 pathways</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          DUAL INCLINED LINES OF PASSING LAPTOPS (OPPOSITE DIRECTIONS)
          ───────────────────────────────────────────────────────────── */}
      <div className="relative w-full my-12 py-10 overflow-hidden">
        {/* Subtle gradient fades on left and right for seamless edge appearance */}
        <div className="pointer-events-none absolute inset-y-0 left-0 w-24 sm:w-48 bg-gradient-to-r from-[#F5F5F7] via-[#F5F5F7]/80 to-transparent z-20" />
        <div className="pointer-events-none absolute inset-y-0 right-0 w-24 sm:w-48 bg-gradient-to-l from-[#F5F5F7] via-[#F5F5F7]/80 to-transparent z-20" />

        {/* Inclined Tilted Container (tilted -2.5 degrees) */}
        <div className="transform -rotate-2 scale-105 origin-center">
          {/* Top Line: Moving LEFT continuously */}
          <div className="flex mb-5 overflow-hidden select-none">
            <div className="animate-marquee-left">
              {/* Duplicate array for seamless infinite looping */}
              {[...line1Laptops, ...line1Laptops].map((laptop, idx) =>
                renderLaptopTickerCard(laptop, "line1", idx)
              )}
            </div>
          </div>

          {/* Bottom Line: Moving RIGHT in the OPPOSITE DIRECTION! */}
          <div className="flex overflow-hidden select-none">
            <div className="animate-marquee-right">
              {/* Duplicate array for seamless infinite looping */}
              {[...line2Laptops, ...line2Laptops].map((laptop, idx) =>
                renderLaptopTickerCard(laptop, "line2", idx)
              )}
            </div>
          </div>
        </div>

        {/* Small Ticker Subtext */}
        <div className="text-center mt-6 text-xs text-[#86868B] font-medium">
          Passing models actively evaluated: Dell • Apple • Lenovo • Framework • HP • ASUS • Microsoft
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          DETAILED DEVICE CONDITION BENCHMARK (INTERACTIVE DASHBOARD)
          ───────────────────────────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6 mt-12">
        {/* Device Switcher Pills */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <span className="text-xs font-semibold text-[#86868B] uppercase tracking-wider mr-2">
            Detailed Inspection Demo:
          </span>
          {(["dell", "mac", "thinkpad"] as const).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                activeTab === key
                  ? "bg-[#1D1D1F] text-white shadow-xs"
                  : "bg-white text-[#6E6E73] border border-[#E5E5E7] hover:border-[#D2D2D7]"
              }`}
            >
              {devices[key].name}
            </button>
          ))}
        </div>

        {/* Live Condition Profile Preview Showcase */}
        <div className="apple-card p-6 sm:p-8 md:p-10 max-w-5xl mx-auto bg-white">
          {/* Header of the Card */}
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-[#E5E5E7] gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-2xl font-bold text-[#1D1D1F] tracking-tight">
                  {current.name}
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#F5F5F7] text-[#6E6E73] font-medium">
                  {current.age}
                </span>
              </div>
              <p className="text-sm text-[#6E6E73] mt-1">
                Deterministic Next-Life Condition Profile & Evidence Provenance
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                {current.pathway}
              </span>
              <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-[#34C759]/10 text-[#34C759] border border-[#34C759]/20 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" />
                {current.lifeExtension}
              </span>
            </div>
          </div>

          {/* Component Health Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 my-8">
            {current.components.map((comp, idx) => {
              const Icon = comp.icon;
              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-[#E5E5E7] bg-[#FBFBFD] hover:bg-white hover:border-[#D2D2D7] transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-white border border-[#E5E5E7] flex items-center justify-center text-[#1D1D1F]">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-semibold text-[#1D1D1F]">
                        {comp.name}
                      </span>
                    </div>
                    {/* Provenance Pill */}
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-md ${
                        comp.source === "DIAGNOSTIC"
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : comp.source === "VISUAL"
                          ? "bg-purple-50 text-purple-700 border border-purple-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {comp.source}
                    </span>
                  </div>

                  <div className="flex items-baseline justify-between mt-3">
                    <span className="text-sm font-bold text-[#1D1D1F]">
                      {comp.value}
                    </span>
                    <span
                      className={`text-xs font-medium flex items-center gap-1 ${
                        comp.state === "good"
                          ? "text-[#34C759]"
                          : comp.state === "warning"
                          ? "text-[#FF9F0A]"
                          : "text-[#FF3B30]"
                      }`}
                    >
                      {comp.state === "good" && <CheckCircle className="w-3 h-3" />}
                      {comp.state === "warning" && <AlertTriangle className="w-3 h-3" />}
                      {comp.state === "bad" && <AlertTriangle className="w-3 h-3" />}
                      {comp.state === "good" ? "Operational" : comp.state === "warning" ? "Attention" : "Fault"}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#86868B] mt-1 truncate">
                    {comp.note}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Engine Decision Summary Footer */}
          <div className="p-4 sm:p-5 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="max-w-xl">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#6E6E73] block mb-1">
                Deterministic Decision Rationale
              </span>
              <p className="text-xs sm:text-sm text-[#1D1D1F] leading-relaxed">
                {current.reason}
              </p>
            </div>
            <div className="flex items-center gap-4 border-t sm:border-t-0 sm:border-l border-[#D2D2D7] pt-3 sm:pt-0 sm:pl-6 w-full sm:w-auto shrink-0">
              <div>
                <span className="text-[11px] text-[#86868B] block">Estimated Impact</span>
                <span className="text-sm font-bold text-[#1D1D1F]">{current.savings}</span>
                <span className="text-[11px] text-[#34C759] block font-medium">{current.co2Saved}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
