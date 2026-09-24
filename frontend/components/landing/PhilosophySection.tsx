"use client";

import React from "react";
import { Trash2, RefreshCw, XCircle, CheckCircle, ArrowRight } from "lucide-react";

export const PhilosophySection: React.FC<{ onOpenAuth: (mode: "login" | "register") => void }> = ({
  onOpenAuth,
}) => {
  return (
    <section id="philosophy" className="py-20 md:py-28 bg-[#F5F5F7] border-t border-[#E5E5E7]">
      <div className="max-w-6xl mx-auto px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#0071E3] block mb-2">
            The Circular Principle
          </span>
          <h2 className="text-[32px] sm:text-[44px] md:text-[50px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
            ReLoop does not manage waste.
            <br />
            <span className="text-[#0071E3]">It manages the life of products.</span>
          </h2>
          <p className="text-[17px] text-[#6E6E73] leading-relaxed">
            Waste management only starts after a product is thrown away. ReLoop operates upstream — before abandonment — keeping electronics at their highest utility.
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
                  Traditional E-Waste Disposal
                </h3>
                <span className="text-xs text-[#86868B]">The Linear Downward Spiral</span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <XCircle className="w-4 h-4 text-[#FF3B30] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    Premature Whole-Device Replacement
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    A degraded battery or dried thermal paste triggers replacement of the entire $1,000 laptop.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <XCircle className="w-4 h-4 text-[#FF3B30] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    Destructive Early Shredding
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    Recycling melts silicon chips down to trace copper and gold, destroying 85%+ of their embodied energy.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <XCircle className="w-4 h-4 text-[#FF3B30] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    Black-Box Guesswork
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    Consumers and IT managers lack objective data on whether a device is repairable, so they default to scrapping.
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
                  ReLoop Circular Intelligence
                </h3>
                <span className="text-xs text-[#0071E3] font-medium">Upstream Value Retention</span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    Component-Level Diagnostics
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    Identifies the exact failed component while isolating and verifying the 90% of components that are perfectly healthy.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    Hierarchical Circular Optimizer
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    Deterministically prioritizes Repair &gt; Upgrade &gt; Refurbish &gt; Redeploy &gt; Recovery before shredding.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-[#34C759] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#1D1D1F] block">
                    Sub-System Harvesting
                  </span>
                  <p className="text-xs text-[#6E6E73] mt-0.5">
                    Even dead laptops yield operational high-speed SSDs and DDR4 RAM modules for spare-part ecosystems.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Banner CTA */}
        <div className="p-8 sm:p-10 rounded-3xl bg-[#1D1D1F] text-white text-center max-w-4xl mx-auto shadow-xl">
          <h3 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3">
            Ready to find the highest-value next life for your device?
          </h3>
          <p className="text-sm text-gray-300 max-w-xl mx-auto mb-6">
            Join users and organizations in reducing electronic waste, extending product lifecycles, and maximizing financial value.
          </p>
          <button
            type="button"
            onClick={() => onOpenAuth("register")}
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all duration-200 shadow-md cursor-pointer"
          >
            <span>Start Free Evaluation</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
};
