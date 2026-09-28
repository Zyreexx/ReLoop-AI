"use client";

import React from "react";
import { Trash2, RefreshCw, XCircle, CheckCircle, ArrowRight } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

export const PhilosophySection: React.FC<{ onOpenAuth: (mode: "login" | "register") => void }> = ({
  onOpenAuth,
}) => {
  const { t } = useLanguage();

  return (
    <section id="philosophy" className="py-24 md:py-36 bg-[#F5F5F7] border-b border-[#E5E5E7] relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Section Header with Index Marker */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#E5E5E7] text-[11px] font-mono font-bold text-[#6E6E73] mb-4 shadow-2xs">
            <span>{t("philosophy.sectionNum", "SECTION 04")}</span>
            <span>•</span>
            <span className="text-[#0071E3]">{t("philosophy.badge", "CIRCULAR PRINCIPLE")}</span>
          </div>
          <h2 className="text-[34px] sm:text-[46px] md:text-[52px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            {t("philosophy.headline1", "ReLoop does not manage waste.")}
            <br />
            <span className="text-[#0071E3]">{t("philosophy.headline2", "It manages the life of products.")}</span>
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            {t(
              "philosophy.subtitle",
              "Waste management only starts after a product is thrown away. ReLoop operates upstream — before abandonment — keeping electronics at their highest utility."
            )}
          </p>
        </div>

        {/* High-Contrast Comparison Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto mb-16">
          {/* Legacy E-Waste Mindset */}
          <div className="apple-card p-6 sm:p-8 bg-white border border-[#E5E5E7]">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-red-50 text-[#FF3B30] flex items-center justify-center">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#1D1D1F]">
                  {t("philosophy.tradTitle", "Traditional E-Waste Disposal")}
                </h3>
                <span className="text-xs text-[#86868B]">{t("philosophy.tradSub", "The Linear Downward Spiral")}</span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <XCircle className="w-4 h-4 text-[#FF3B30] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    {t("philosophy.trad1Title", "Premature Whole-Device Replacement")}
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    {t(
                      "philosophy.trad1Desc",
                      "A degraded battery or dried thermal paste triggers replacement of the entire $1,000 laptop."
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <XCircle className="w-4 h-4 text-[#FF3B30] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    {t("philosophy.trad2Title", "Destructive Early Shredding")}
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    {t(
                      "philosophy.trad2Desc",
                      "Recycling melts silicon chips down to trace copper and gold, destroying 85%+ of their embodied energy."
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <XCircle className="w-4 h-4 text-[#FF3B30] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    {t("philosophy.trad3Title", "Black-Box Guesswork")}
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    {t(
                      "philosophy.trad3Desc",
                      "Consumers and IT managers lack objective data on whether a device is repairable, so they default to scrapping."
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* ReLoop Circular Intelligence */}
          <div className="apple-card p-6 sm:p-8 bg-white border-2 border-[#0071E3]/30 shadow-md">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#0071E3] flex items-center justify-center">
                <RefreshCw className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#1D1D1F]">
                  {t("philosophy.reloopTitle", "ReLoop Circular Intelligence")}
                </h3>
                <span className="text-xs text-[#0071E3] font-medium">{t("philosophy.reloopSub", "Upstream Value Retention")}</span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    {t("philosophy.reloop1Title", "Component-Level Diagnostics")}
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    {t(
                      "philosophy.reloop1Desc",
                      "Identifies the exact failed component while isolating and verifying the 90% of components that are perfectly healthy."
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    {t("philosophy.reloop2Title", "Hierarchical Circular Optimizer")}
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    {t(
                      "philosophy.reloop2Desc",
                      "Deterministically prioritizes Repair > Upgrade > Refurbish > Redeploy > Recovery before shredding."
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    {t("philosophy.reloop3Title", "Sub-System Harvesting")}
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    {t(
                      "philosophy.reloop3Desc",
                      "Even dead laptops yield operational high-speed SSDs and DDR4 RAM modules for spare-part ecosystems."
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Banner CTA */}
        <div className="p-8 sm:p-10 rounded-3xl bg-[#1D1D1F] text-white text-center max-w-4xl mx-auto shadow-xl">
          <h3 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3">
            {t("philosophy.bannerTitle", "Ready to find the highest-value next life for your device?")}
          </h3>
          <p className="text-sm text-gray-300 max-w-xl mx-auto mb-6">
            {t(
              "philosophy.bannerDesc",
              "Join users and organizations in reducing electronic waste, extending product lifecycles, and maximizing financial value."
            )}
          </p>
          <button
            type="button"
            onClick={() => onOpenAuth("register")}
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all duration-200 shadow-md cursor-pointer"
          >
            <span>{t("philosophy.bannerBtn", "Start Free Evaluation")}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
};
