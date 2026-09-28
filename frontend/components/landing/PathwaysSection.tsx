"use client";

import React, { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
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
  ArrowRight,
  Cpu,
} from "lucide-react";

import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";

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

interface PathwaysSectionProps {
  onOpenAuth?: (mode: "login" | "register") => void;
}

const loopBadgeStyles: Record<string, string> = {
  repair: "bg-emerald-50 text-emerald-700 border-emerald-200",
  upgrade: "bg-blue-50 text-[#0071E3] border-blue-200",
  refurbish: "bg-purple-50 text-purple-700 border-purple-200",
  reuse: "bg-indigo-50 text-indigo-700 border-indigo-200",
  recovery: "bg-amber-50 text-amber-700 border-amber-200",
  recycling: "bg-rose-50 text-rose-700 border-rose-200",
};

export const PathwaysSection: React.FC<PathwaysSectionProps> = ({ onOpenAuth }) => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const router = useRouter();
  const [activePathway, setActivePathway] = useState<string>("repair");

  const pathways: PathwayData[] = useMemo(
    () => [
      {
        id: "repair",
        order: 1,
        title: t("pathways.repair.name", "Repair"),
        subtitle: t("pathways.repair.subtitle", "Targeted Component Restoration"),
        badge: t("pathways.repair.badge", "Highest Priority Loop"),
        icon: Wrench,
        description: t(
          "pathways.repairDesc",
          "Replace only degraded modules (battery, display, charging port, keyboard) with zero functional waste."
        ),
        eligibility: [
          t("pathways.repair.crit1", "Motherboard and display are electrically intact"),
          t(
            "pathways.repair.crit2",
            "Failure is isolated to serviceable modules (battery, fans, keyboard, charging port)"
          ),
          t(
            "pathways.repair.crit3",
            "Component replacement cost < 40% of residual device value"
          ),
        ],
        lifeExtension: t("pathways.repair.life", "+2 to +3 Years"),
        valueRetained: t("pathways.repair.val", "85% - 95%"),
        co2Savings: t("pathways.repair.co2", "Up to 160 kg CO₂e"),
        idealFor: t(
          "pathways.repair.ideal",
          "Laptops with degraded batteries, sticky keys, or dried thermal paste."
        ),
        exampleAction: t(
          "pathways.repair.example",
          "Install OEM battery pack + thermal heatsink repaste (Cost: ₹3,200)."
        ),
      },
      {
        id: "upgrade",
        order: 2,
        title: t("pathways.upgrade.name", "Upgrade"),
        subtitle: t("pathways.upgrade.subtitle", "Performance & Capacity Expansion"),
        badge: t("pathways.upgrade.badge", "Second Loop"),
        icon: ArrowUpCircle,
        description: t(
          "pathways.upgradeDesc",
          "Boost RAM, switch to high-speed NVMe SSD, or repaste thermals to restore modern productivity standards."
        ),
        eligibility: [
          t(
            "pathways.upgrade.crit1",
            "Device has upgradeable slots (SO-DIMM RAM, M.2 PCIe NVMe slots)"
          ),
          t(
            "pathways.upgrade.crit2",
            "CPU architecture supports modern security & OS updates"
          ),
          t(
            "pathways.upgrade.crit3",
            "Primary user workload has outgrown original baseline specs"
          ),
        ],
        lifeExtension: t("pathways.upgrade.life", "+2 to +4 Years"),
        valueRetained: t("pathways.upgrade.val", "80% - 90%"),
        co2Savings: t("pathways.upgrade.co2", "Up to 140 kg CO₂e"),
        idealFor: t(
          "pathways.upgrade.ideal",
          "Machines slowed down by 8GB RAM or mechanical 5400 RPM hard drives."
        ),
        exampleAction: t(
          "pathways.upgrade.example",
          "Swap spinning HDD for 1TB NVMe SSD + double RAM to 16GB (Cost: ₹4,500)."
        ),
      },
      {
        id: "refurbish",
        order: 3,
        title: t("pathways.refurbish.name", "Refurbish"),
        subtitle: t("pathways.refurbish.subtitle", "Deep Restoration & Resale Prep"),
        badge: t("pathways.refurbish.badge", "Third Loop"),
        icon: Sparkles,
        description: t(
          "pathways.refurbishDesc",
          "Comprehensive factory overhaul, cosmetic restoration, deep thermal servicing, and certified quality assurance."
        ),
        eligibility: [
          t(
            "pathways.refurbish.crit1",
            "Chassis structural integrity is sound (no broken hinge mounts)"
          ),
          t(
            "pathways.refurbish.crit2",
            "All hardware passes automated 40-point stress benchmarks"
          ),
          t(
            "pathways.refurbish.crit3",
            "Residual resale value after refurbishment costs exceeds break-even threshold"
          ),
        ],
        lifeExtension: t("pathways.refurbish.life", "+3 Years"),
        valueRetained: t("pathways.refurbish.val", "70% - 85%"),
        co2Savings: t("pathways.refurbish.co2", "Up to 180 kg CO₂e"),
        idealFor: t(
          "pathways.refurbish.ideal",
          "Corporate fleet refresh devices or off-lease enterprise laptops."
        ),
        exampleAction: t(
          "pathways.refurbish.example",
          "Clean chassis, reinstall certified OS image, repackage with 6-month warranty."
        ),
      },
      {
        id: "reuse",
        order: 4,
        title: t("pathways.reuse.name", "Reuse / Redeploy"),
        subtitle: t("pathways.reuse.subtitle", "Secondary Life Allocation"),
        badge: t("pathways.reuse.badge", "Fourth Loop"),
        icon: Repeat,
        description: t(
          "pathways.reuseDesc",
          "Redeploy perfectly healthy corporate machines to schools, non-profits, or lighter-workload enterprise roles."
        ),
        eligibility: [
          t(
            "pathways.reuse.crit1",
            "Hardware is functional but obsolete for high-end rendering/development"
          ),
          t(
            "pathways.reuse.crit2",
            "Secondary role requirements match existing hardware capabilities"
          ),
          t(
            "pathways.reuse.crit3",
            "No significant hardware repairs required before reallocation"
          ),
        ],
        lifeExtension: t("pathways.reuse.life", "+2 to +5 Years"),
        valueRetained: t("pathways.reuse.val", "60% - 75%"),
        co2Savings: t("pathways.reuse.co2", "Up to 190 kg CO₂e"),
        idealFor: t(
          "pathways.reuse.ideal",
          "Donation to schools, lightweight home servers, reception POS, or student coding labs."
        ),
        exampleAction: t(
          "pathways.reuse.example",
          "Redeploy an 8GB i5 laptop to an educational Linux learning station."
        ),
      },
      {
        id: "recovery",
        order: 5,
        title: t("pathways.recovery.name", "Component Recovery"),
        subtitle: t("pathways.recovery.subtitle", "Sub-System Harvesting & Salvage"),
        badge: t("pathways.recovery.badge", "Fifth Loop"),
        icon: PackageOpen,
        description: t(
          "pathways.recoveryDesc",
          "Harvest intact working RAM sticks, SSDs, Wi-Fi 6 cards, and displays for spare parts inventory before chassis disposal."
        ),
        eligibility: [
          t(
            "pathways.recovery.crit1",
            "Core board or display panel is irreparably damaged"
          ),
          t(
            "pathways.recovery.crit2",
            "Individual modules (SSD, RAM, Wi-Fi card, camera, screen cable) remain 100% operational"
          ),
          t(
            "pathways.recovery.crit3",
            "Component resale/re-use value exceeds dismantling labor"
          ),
        ],
        lifeExtension: t("pathways.recovery.life", "Modules re-entered into repair pools"),
        valueRetained: t("pathways.recovery.val", "35% - 50%"),
        co2Savings: t("pathways.recovery.co2", "60 - 90 kg CO₂e"),
        idealFor: t(
          "pathways.recovery.ideal",
          "Liquid-damaged or crushed laptops where the NVMe SSD and RAM sticks are undamaged."
        ),
        exampleAction: t(
          "pathways.recovery.example",
          "Harvest 512GB M.2 SSD into an external USB-C enclosure + harvest 16GB SO-DIMM."
        ),
      },
      {
        id: "recycling",
        order: 6,
        title: t("pathways.recycling.name", "Recycling"),
        subtitle: t("pathways.recycling.subtitle", "Responsible Material Smelting"),
        badge: t("pathways.recycling.badge", "Last Resort Loop"),
        icon: Recycle,
        description: t(
          "pathways.recyclingDesc",
          "Only when all economic and functional loops are exhausted: safe chemical hydrometallurgical recovery of gold, copper, and cobalt."
        ),
        eligibility: [
          t(
            "pathways.recycling.crit1",
            "No recoverable or salvageable sub-components remain"
          ),
          t(
            "pathways.recycling.crit2",
            "Repair and refurbishment are technically impossible or hazardous"
          ),
          t(
            "pathways.recycling.crit3",
            "Certified R2 / e-Stewards smelter facility is engaged"
          ),
        ],
        lifeExtension: t("pathways.recycling.life", "Raw materials (Al, Cu, Au, Li) recovered"),
        valueRetained: t("pathways.recycling.val", "5% - 15% (Raw commodity)"),
        co2Savings: t("pathways.recycling.co2", "20 - 45 kg CO₂e"),
        idealFor: t(
          "pathways.recycling.ideal",
          "Severely corroded, burnt, or physically shredded electronic remnants."
        ),
        exampleAction: t(
          "pathways.recycling.example",
          "Transfer to certified hazardous e-waste smelter for precious metal extraction."
        ),
      },
    ],
    [t]
  );

  const current = useMemo(
    () => pathways.find((p) => p.id === activePathway) || pathways[0],
    [pathways, activePathway]
  );

  const handleAssessClick = () => {
    if (user) {
      router.push("/assess-device");
    } else if (onOpenAuth) {
      try {
        localStorage.setItem("reloop_redirect", "/assess-device");
      } catch {}
      onOpenAuth("register");
    } else {
      router.push("/assess-device");
    }
  };

  return (
    <section id="pathways" className="py-24 md:py-36 bg-white border-t border-b border-[#E5E5E7] relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Apple-style Section Header with Index Marker */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F5F5F7] border border-[#E5E5E7] text-[11px] font-mono font-bold text-[#6E6E73] mb-4">
            <span>{t("pathways.sectionNum", "SECTION 01")}</span>
            <span>•</span>
            <span className="text-[#0071E3]">{t("pathways.badge", "Circular Hierarchy")}</span>
          </div>
          <h2 className="text-[34px] sm:text-[46px] md:text-[52px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            {t("pathways.title", "Six Pathways. Zero Needless E-Waste.")}
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            {t(
              "pathways.subtitle",
              "ReLoop prioritizes device retention over raw smelting. Explore each pathway's qualification threshold, life extension, and economic value."
            )}
          </p>
        </div>

        {/* Pathway Pills Selector with WAI-ARIA tab semantics */}
        <div
          role="tablist"
          aria-label={t("pathways.badge", "Circular Hierarchy")}
          className="flex items-center justify-start md:justify-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar"
        >
          {pathways.map((p) => {
            const Icon = p.icon;
            const isSelected = activePathway === p.id;
            return (
              <button
                key={p.id}
                role="tab"
                id={`tab-${p.id}`}
                aria-selected={isSelected}
                aria-controls={`panel-${p.id}`}
                type="button"
                onClick={() => setActivePathway(p.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-xs sm:text-sm font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? "bg-[#1D1D1F] text-white shadow-xs"
                    : "bg-white text-[#6E6E73] border border-[#E5E5E7] hover:border-[#D2D2D7] hover:text-[#1D1D1F]"
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 transition-colors ${
                    isSelected
                      ? "bg-white/20 text-white"
                      : "bg-[#F5F5F7] text-[#1D1D1F] border border-[#E5E5E7]"
                  }`}
                >
                  {p.order}
                </span>
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{p.title}</span>
              </button>
            );
          })}
        </div>

        {/* Active Pathway Detail Card */}
        <div
          id={`panel-${current.id}`}
          role="tabpanel"
          aria-labelledby={`tab-${current.id}`}
          className="apple-card p-6 sm:p-10 max-w-5xl mx-auto bg-white"
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Description & Qualifications */}
            <div className="lg:col-span-7">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[11px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#E8E8ED] text-[#1D1D1F] font-semibold">
                  {t("pathways.loopLabel", "Loop #")}{current.order}
                </span>
                <span
                  className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${
                    loopBadgeStyles[current.id] || "bg-[#F5F5F7] text-[#1D1D1F] border-[#E5E5E7]"
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
                  {t("pathways.qualificationCriteria", "Qualification Criteria")}
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
                  {t("pathways.concreteExample", "Concrete Example")}
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
                  <span>{t("pathways.expectedLife", "Expected Life Extension")}</span>
                </div>
                <span className="text-xl font-bold text-[#1D1D1F]">
                  {current.lifeExtension}
                </span>
                <p className="text-[11px] text-[#86868B] mt-1">
                  {t("pathways.lifeModelNote", "Based on component lifecycle models")}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7]">
                <div className="flex items-center gap-2 text-[#6E6E73] text-xs font-medium mb-1">
                  <Coins className="w-4 h-4 text-[#34C759]" />
                  <span>{t("pathways.productValueRetained", "Product Value Retained")}</span>
                </div>
                <span className="text-xl font-bold text-[#1D1D1F]">
                  {current.valueRetained}
                </span>
                <p className="text-[11px] text-[#86868B] mt-1">
                  {t("pathways.valueModelNote", "Calculated against baseline market replacement cost")}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7]">
                <div className="flex items-center gap-2 text-[#6E6E73] text-xs font-medium mb-1">
                  <Leaf className="w-4 h-4 text-[#34C759]" />
                  <span>{t("pathways.avoidedCarbon", "Avoided Embodied Carbon")}</span>
                </div>
                <span className="text-xl font-bold text-[#1D1D1F]">
                  {current.co2Savings}
                </span>
                <p className="text-[11px] text-[#86868B] mt-1">
                  {t("pathways.carbonModelNote", "Prevents new manufacturing raw material footprint")}
                </p>
              </div>

              <div className="p-4 rounded-xl border border-dashed border-[#D2D2D7] text-center">
                <span className="text-xs text-[#6E6E73] block">
                  {t("pathways.bestSuitedFor", "Best Suited For")}
                </span>
                <p className="text-xs font-semibold text-[#1D1D1F] mt-0.5">
                  {current.idealFor}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Why Recycling is Last Resort Note */}
        <div className="mt-8 text-center max-w-4xl mx-auto">
          <p className="text-xs text-[#86868B]">
            {t(
              "pathways.recyclingDisclaimer",
              "* Note: Recycling recovers basic raw commodities (copper, aluminum, gold) but destroys 85%+ of the embodied manufacturing energy. ReLoop strictly delays recycling until higher loops are exhausted."
            )}
          </p>
        </div>

        {/* Interactive Pathway Bottom CTA Card */}
        <div className="mt-12 p-8 sm:p-10 rounded-3xl bg-[#F5F5F7] border border-[#E5E5E7] max-w-5xl mx-auto text-center">
          <h3 className="text-xl sm:text-2xl font-bold text-[#1D1D1F] mb-3">
            {t("pathways.cta.title", "Ready to determine your device's circular pathway?")}
          </h3>
          <p className="text-sm sm:text-base text-[#6E6E73] max-w-2xl mx-auto mb-6">
            {t(
              "pathways.cta.desc",
              "Run our 5-minute automated diagnostic and algorithmic assessment to uncover the optimal loop."
            )}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              type="button"
              onClick={handleAssessClick}
              className="w-full sm:w-auto px-6 py-3 rounded-full bg-[#0071E3] text-white font-semibold text-sm hover:bg-[#0077ED] transition-colors shadow-xs flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>{t("pathways.cta.assessBtn", "Assess Your Laptop")}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => router.push("/engine")}
              className="w-full sm:w-auto px-6 py-3 rounded-full bg-white text-[#1D1D1F] font-semibold text-sm border border-[#E5E5E7] hover:border-[#D2D2D7] transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>{t("pathways.cta.engineBtn", "Explore Decision Engine")}</span>
              <Cpu className="w-4 h-4 text-[#86868B]" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
