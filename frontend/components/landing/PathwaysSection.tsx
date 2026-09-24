"use client";

import React, { useState } from "react";
import {
  Wrench,
  ArrowUpCircle,
  Sparkles,
  Repeat,
  PackageOpen,
  Recycle,
  CheckCircle2,
  Clock,
  Coins,
  Leaf,
  ChevronRight,
} from "lucide-react";

interface PathwayData {
  id: string;
  order: number;
  title: string;
  subtitle: string;
  badge: string;
  icon: React.ElementType;
  description: string;
  eligibility: string[];
  lifeExtension: string;
  valueRetained: string;
  co2Savings: string;
  idealFor: string;
  exampleAction: string;
}

export const PathwaysSection: React.FC = () => {
  const [activePathway, setActivePathway] = useState<string>("repair");

  const pathways: PathwayData[] = [
    {
      id: "repair",
      order: 1,
      title: "Repair",
      subtitle: "Targeted Component Restoration",
      badge: "Highest Priority Loop",
      icon: Wrench,
      description:
        "Address isolated component failures without discarding or replacing functioning sub-systems. Keeps original machine identity intact.",
      eligibility: [
        "Motherboard and display are electrically intact",
        "Failure is isolated to serviceable modules (battery, fans, keyboard, charging port)",
        "Component replacement cost < 40% of residual device value",
      ],
      lifeExtension: "+2 to +3 Years",
      valueRetained: "85% - 95%",
      co2Savings: "Up to 160 kg CO₂e",
      idealFor: "Laptops with degraded batteries, sticky keys, or dried thermal paste.",
      exampleAction: "Install OEM battery pack + thermal heatsink repaste (Cost: ₹3,200).",
    },
    {
      id: "upgrade",
      order: 2,
      title: "Upgrade",
      subtitle: "Performance & Capacity Expansion",
      badge: "Second Loop",
      icon: ArrowUpCircle,
      description:
        "Modernize compute bottleneck components so modern operating systems and heavy modern web apps run smoothly without replacing the chassis.",
      eligibility: [
        "Device has upgradeable slots (SO-DIMM RAM, M.2 PCIe NVMe slots)",
        "CPU architecture supports modern security & OS updates",
        "Primary user workload has outgrown original baseline specs",
      ],
      lifeExtension: "+2 to +4 Years",
      valueRetained: "80% - 90%",
      co2Savings: "Up to 140 kg CO₂e",
      idealFor: "Machines slowed down by 8GB RAM or mechanical 5400 RPM hard drives.",
      exampleAction: "Swap spinning HDD for 1TB NVMe SSD + double RAM to 16GB (Cost: ₹4,500).",
    },
    {
      id: "refurbish",
      order: 3,
      title: "Refurbish",
      subtitle: "Deep Restoration & Resale Prep",
      badge: "Third Loop",
      icon: Sparkles,
      description:
        "Multi-point diagnostic testing, cosmetic ultrasonic cleaning, firmware updates, fresh OS provisioning, and warranty-grade recertification.",
      eligibility: [
        "Chassis structural integrity is sound (no broken hinge mounts)",
        "All hardware passes automated 40-point stress benchmarks",
        "Residual resale value after refurbishment costs exceeds break-even threshold",
      ],
      lifeExtension: "+3 Years",
      valueRetained: "70% - 85%",
      co2Savings: "Up to 180 kg CO₂e",
      idealFor: "Corporate fleet refresh devices or off-lease enterprise laptops.",
      exampleAction: "Clean chassis, reinstall certified OS image, repackage with 6-month warranty.",
    },
    {
      id: "reuse",
      order: 4,
      title: "Reuse / Redeploy",
      subtitle: "Secondary Life Allocation",
      badge: "Fourth Loop",
      icon: Repeat,
      description:
        "Match devices that no longer meet demanding primary requirements to secondary roles where their specifications excel.",
      eligibility: [
        "Hardware is functional but obsolete for high-end rendering/development",
        "Secondary role requirements match existing hardware capabilities",
        "No significant hardware repairs required before reallocation",
      ],
      lifeExtension: "+2 to +5 Years",
      valueRetained: "60% - 75%",
      co2Savings: "Up to 190 kg CO₂e",
      idealFor: "Donation to schools, lightweight home servers, reception POS, or student coding labs.",
      exampleAction: "Redeploy an 8GB i5 laptop to an educational Linux learning station.",
    },
    {
      id: "recovery",
      order: 5,
      title: "Component Recovery",
      subtitle: "Sub-System Harvesting & Salvage",
      badge: "Fifth Loop",
      icon: PackageOpen,
      description:
        "When whole-device repair is economically or technically non-viable, systematically harvest functioning sub-components for spare parts inventories.",
      eligibility: [
        "Core board or display panel is irreparably damaged",
        "Individual modules (SSD, RAM, Wi-Fi card, camera, screen cable) remain 100% operational",
        "Component resale/re-use value exceeds dismantling labor",
      ],
      lifeExtension: "Modules re-entered into repair pools",
      valueRetained: "35% - 50%",
      co2Savings: "60 - 90 kg CO₂e",
      idealFor: "Liquid-damaged or crushed laptops where the NVMe SSD and RAM sticks are undamaged.",
      exampleAction: "Harvest 512GB M.2 SSD into an external USB-C enclosure + harvest 16GB SO-DIMM.",
    },
    {
      id: "recycling",
      order: 6,
      title: "Recycling",
      subtitle: "Responsible Material Smelting",
      badge: "Last Resort Loop",
      icon: Recycle,
      description:
        "Material segregation and certified e-waste recovery activated strictly when all 5 higher-value circular loops are exhausted or impossible.",
      eligibility: [
        "No recoverable or salvageable sub-components remain",
        "Repair and refurbishment are technically impossible or hazardous",
        "Certified R2 / e-Stewards smelter facility is engaged",
      ],
      lifeExtension: "Raw materials (Al, Cu, Au, Li) recovered",
      valueRetained: "5% - 15% (Raw commodity)",
      co2Savings: "20 - 45 kg CO₂e",
      idealFor: "Severely corroded, burnt, or physically shredded electronic remnants.",
      exampleAction: "Transfer to certified hazardous e-waste smelter for precious metal extraction.",
    },
  ];

  const current = pathways.find((p) => p.id === activePathway) || pathways[0];

  return (
    <section id="pathways" className="py-24 md:py-36 bg-white border-t border-b border-[#E5E5E7] relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Apple-style Section Header with Index Marker */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F5F5F7] border border-[#E5E5E7] text-[11px] font-mono font-bold text-[#6E6E73] mb-4">
            <span>SECTION 01</span>
            <span>•</span>
            <span className="text-[#0071E3]">CIRCULAR HIERARCHY</span>
          </div>
          <h2 className="text-[34px] sm:text-[46px] md:text-[52px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            Six pathways. One optimal next life.
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            Existing e-waste systems default straight to shredding and recycling.
            ReLoop prioritizes value retention by evaluating loops from highest to lowest utility.
          </p>
        </div>

        {/* Pathway Pills Selector */}
        <div className="flex items-center justify-start md:justify-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          {pathways.map((p) => {
            const Icon = p.icon;
            const isSelected = activePathway === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setActivePathway(p.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-xs sm:text-sm font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? "bg-[#1D1D1F] text-white shadow-xs"
                    : "bg-white text-[#6E6E73] border border-[#E5E5E7] hover:border-[#D2D2D7] hover:text-[#1D1D1F]"
                }`}
              >
                <span className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center text-[10px]">
                  {p.order}
                </span>
                <Icon className="w-3.5 h-3.5" />
                <span>{p.title}</span>
              </button>
            );
          })}
        </div>

        {/* Active Pathway Detail Card */}
        <div className="apple-card p-6 sm:p-10 max-w-5xl mx-auto bg-white">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Description & Qualifications */}
            <div className="lg:col-span-7">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[11px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#E8E8ED] text-[#1D1D1F] font-semibold">
                  Loop #{current.order}
                </span>
                <span
                  className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                    current.id === "recycling"
                      ? "bg-red-50 text-red-700 border border-red-200"
                      : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  }`}
                >
                  {current.badge}
                </span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-bold text-[#1D1D1F] tracking-tight mb-2">
                {current.title}
              </h3>
              <p className="text-sm font-medium text-[#0071E3] mb-4">
                {current.subtitle}
              </p>

              <p className="text-sm sm:text-[15px] text-[#6E6E73] leading-relaxed mb-6">
                {current.description}
              </p>

              {/* Eligibility Criteria */}
              <div className="mb-6">
                <span className="text-xs font-bold uppercase tracking-wider text-[#1D1D1F] block mb-2.5">
                  Qualification Criteria
                </span>
                <div className="space-y-2">
                  {current.eligibility.map((crit, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-xs text-[#6E6E73]">
                      <CheckCircle2 className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                      <span>{crit}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Real World Action */}
              <div className="p-4 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#6E6E73] block mb-1">
                  Concrete Example
                </span>
                <p className="text-xs font-semibold text-[#1D1D1F]">
                  {current.exampleAction}
                </p>
              </div>
            </div>

            {/* Right Column: Key Metric Tiles */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <div className="p-5 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7]">
                <div className="flex items-center gap-2 text-[#6E6E73] text-xs font-medium mb-1">
                  <Clock className="w-4 h-4 text-[#0071E3]" />
                  <span>Expected Life Extension</span>
                </div>
                <span className="text-xl font-bold text-[#1D1D1F]">
                  {current.lifeExtension}
                </span>
                <p className="text-[11px] text-[#86868B] mt-1">
                  Based on component lifecycle models
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7]">
                <div className="flex items-center gap-2 text-[#6E6E73] text-xs font-medium mb-1">
                  <Coins className="w-4 h-4 text-[#34C759]" />
                  <span>Product Value Retained</span>
                </div>
                <span className="text-xl font-bold text-[#1D1D1F]">
                  {current.valueRetained}
                </span>
                <p className="text-[11px] text-[#86868B] mt-1">
                  Calculated against baseline market replacement cost
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7]">
                <div className="flex items-center gap-2 text-[#6E6E73] text-xs font-medium mb-1">
                  <Leaf className="w-4 h-4 text-[#34C759]" />
                  <span>Avoided Embodied Carbon</span>
                </div>
                <span className="text-xl font-bold text-[#1D1D1F]">
                  {current.co2Savings}
                </span>
                <p className="text-[11px] text-[#86868B] mt-1">
                  Prevents new manufacturing raw material footprint
                </p>
              </div>

              <div className="p-4 rounded-xl border border-dashed border-[#D2D2D7] text-center">
                <span className="text-xs text-[#6E6E73] block">
                  Best Suited For
                </span>
                <p className="text-xs font-semibold text-[#1D1D1F] mt-0.5">
                  {current.idealFor}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Why Recycling is Last Resort Note */}
        <div className="mt-8 text-center">
          <p className="text-xs text-[#86868B]">
            * Note: Recycling recovers basic raw commodities (copper, aluminum, gold) but destroys 85%+ of the embodied manufacturing energy.
            ReLoop strictly delays recycling until higher loops are exhausted.
          </p>
        </div>
      </div>
    </section>
  );
};
