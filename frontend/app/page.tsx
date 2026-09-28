"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import { HeroSection } from "@/components/landing/HeroSection";
import { ArrowRight, Wrench, ShieldCheck, Cpu, RefreshCw } from "lucide-react";

export default function Home() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleAssessClick = () => {
    if (user) {
      router.push("/assess-device");
    } else {
      try {
        localStorage.setItem("reloop_redirect", "/assess-device");
      } catch {}
      handleOpenAuth("register");
    }
  };

  const featurePortals = [
    {
      badge: t("portals.badgePathways", "CIRCULAR HIERARCHY"),
      title: t("portals.pathwaysTitle"),
      desc: t("portals.pathwaysDesc"),
      link: "/pathways",
      linkText: t("portals.pathwaysBtn"),
      icon: Wrench,
      highlight: t("portals.highlightPathways", "Up to 94% Value Retained"),
    },
    {
      badge: t("portals.badgeIntake", "EVIDENCE SYSTEM"),
      title: t("portals.howItWorksTitle"),
      desc: t("portals.howItWorksDesc"),
      link: "/how-it-works",
      linkText: t("portals.howItWorksBtn"),
      icon: ShieldCheck,
      highlight: t("portals.highlightIntake", "Traceable Provenance Badges"),
    },
    {
      badge: t("portals.badgeEngine", "SCORING ALGORITHM"),
      title: t("portals.engineTitle"),
      desc: t("portals.engineDesc"),
      link: "/engine",
      linkText: t("portals.engineBtn"),
      icon: Cpu,
      highlight: t("portals.highlightEngine", "Mathematical Scoring Model"),
    },
    {
      badge: t("portals.badgePhilosophy", "CIRCULAR PRINCIPLE"),
      title: t("portals.philosophyTitle"),
      desc: t("portals.philosophyDesc"),
      link: "/philosophy",
      linkText: t("portals.philosophyBtn"),
      icon: RefreshCw,
      highlight: t("portals.highlightPhilosophy", "Preventing Embodied Carbon Loss"),
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F5F7] text-[#1D1D1F]">
      {/* Sliding Auth Modal Component (from user screenshots) */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />

      {/* Navigation */}
      <Navbar onOpenAuth={handleOpenAuth} />

      {/* Main Content */}
      <main className="flex-1">
        {/* Hero Section with Floating Background Laptops */}
        <HeroSection onOpenAuth={handleOpenAuth} />

        {/* Feature Overview Portal Cards (Links to Dedicated Separate Pages) */}
        <section className="py-24 md:py-32 bg-white border-t border-b border-[#E5E5E7]">
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#0071E3] block mb-2">
                {t("portals.tagline")}
              </span>
              <h2 className="text-[34px] sm:text-[46px] font-bold text-[#1D1D1F] tracking-tight leading-tight mb-4">
                {t("portals.title")}
              </h2>
              <p className="text-[17px] text-[#6E6E73] leading-relaxed">
                {t("portals.subtitle")}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {featurePortals.map((feat, idx) => {
                const Icon = feat.icon;
                return (
                  <div
                    key={idx}
                    className="apple-card p-8 sm:p-10 bg-[#FBFBFD] hover:bg-white border border-[#E5E5E7] flex flex-col justify-between transition-all duration-300 group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-5">
                        <span className="text-[11px] font-mono font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-[#E8E8ED] text-[#1D1D1F]">
                          {feat.badge}
                        </span>
                        <div className="w-10 h-10 rounded-xl bg-white border border-[#E5E5E7] flex items-center justify-center text-[#0071E3] group-hover:scale-105 transition-transform shadow-2xs">
                          <Icon className="w-5 h-5" />
                        </div>
                      </div>

                      <h3 className="text-2xl font-bold text-[#1D1D1F] tracking-tight mb-3">
                        {feat.title}
                      </h3>

                      <p className="text-sm sm:text-[15px] text-[#6E6E73] leading-relaxed mb-6">
                        {feat.desc}
                      </p>
                    </div>

                    <div className="pt-5 border-t border-[#E5E5E7] flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#0071E3]">
                        {feat.highlight}
                      </span>
                      <Link
                        href={feat.link}
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors"
                      >
                        <span>{feat.linkText}</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Call to Action Banner */}
        <section className="py-20 bg-[#F5F5F7]">
          <div className="max-w-4xl mx-auto px-6">
            <div className="p-8 sm:p-12 rounded-3xl bg-[#1D1D1F] text-white text-center shadow-xl">
              <h3 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3">
                {t("portals.ctaTitle", "Ready to assess your hardware?")}
              </h3>
              <p className="text-sm text-gray-300 max-w-xl mx-auto mb-6">
                {t(
                  "portals.ctaSubtitle",
                  "Calculate the highest-value next life for your device in seconds."
                )}
              </p>
              <button
                type="button"
                onClick={handleAssessClick}
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all duration-200 shadow-md cursor-pointer"
              >
                <span>{t("portals.ctaBtn", "Assess Your Laptop")}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
