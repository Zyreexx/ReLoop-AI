"use client";

import React from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSelector } from "@/components/ui/LanguageSelector";

export const Footer: React.FC = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-[#F5F5F7] text-[#6E6E73] text-[12px] border-t border-[#D2D2D7] pt-12 pb-16">
      <div className="max-w-6xl mx-auto px-6">
        {/* Apple-style Footnotes / Assumptions Disclosures */}
        <div className="pb-8 border-b border-[#D2D2D7] space-y-2 text-[#86868B] leading-relaxed">
          <p>{t("footer.disclaimer1")}</p>
          <p>{t("footer.disclaimer2")}</p>
          <p>{t("footer.disclaimer3")}</p>
          <p>{t("footer.disclaimer4")}</p>
        </div>

        {/* Directory Links */}
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-8 py-10">
          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              {t("footer.pathways")}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
                  {t("pathways.repair")}
                </Link>
              </li>
              <li>
                <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
                  {t("pathways.upgrade")}
                </Link>
              </li>
              <li>
                <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
                  {t("pathways.refurbish")}
                </Link>
              </li>
              <li>
                <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
                  {t("pathways.reuse")}
                </Link>
              </li>
              <li>
                <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
                  {t("pathways.recovery")}
                </Link>
              </li>
              <li>
                <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
                  {t("pathways.recycle")}
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              {t("footer.evidenceSystem")}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link href="/how-it-works" className="hover:text-[#1D1D1F] transition-colors">
                  {t("intake.step1")}
                </Link>
              </li>
              <li>
                <Link href="/how-it-works" className="hover:text-[#1D1D1F] transition-colors">
                  {t("intake.step2")}
                </Link>
              </li>
              <li>
                <Link href="/engine" className="hover:text-[#1D1D1F] transition-colors">
                  {t("intake.step3")}
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              {t("footer.challengeTitle", "Grand Challenge 2026")}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <span className="text-[#1D1D1F] font-medium">{t("footer.challengeInstitute", "PCCoE International Grand Challenge")}</span>
              </li>
              <li>
                <span>{t("footer.challengeTrack", "Track: Smart Cities, Energy & Circular Economy")}</span>
              </li>
              <li>
                <span>{t("footer.challengeFocus", "Focus: Product Life Extension")}</span>
              </li>
              <li>
                <a
                  href="https://github.com/Zyreexx/ReLoop-AI"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-[#1D1D1F] inline-flex items-center gap-1 text-[#0071E3]"
                >
                  <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  <span>{t("footer.githubRepo", "GitHub Repository")}</span>
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              {t("footer.about")}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link href="/philosophy" className="hover:text-[#1D1D1F] transition-colors">
                  {t("nav.philosophy")}
                </Link>
              </li>
              <li>
                <span>{t("brand.tagline")}</span>
              </li>
              <li>
                <span>{t("footer.targetOptimization", "Target: Laptop Lifecycle Optimization")}</span>
              </li>
              <li>
                <span>{t("footer.scoringEngine", "Deterministic Scoring Engine")}</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Copyright & Brand Bar */}
        <div className="pt-6 border-t border-[#D2D2D7] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-[#1D1D1F] font-semibold text-[13px]">
            <div className="w-5 h-5 rounded-full bg-[#0071E3] flex items-center justify-center text-white">
              <RefreshCw className="w-3 h-3" />
            </div>
            <span>{t("brand.name")}</span>
            <span className="text-[#86868B] font-normal text-xs ml-1">
              • {t("brand.tagline")}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <LanguageSelector variant="footer" />
            <div className="text-xs text-[#86868B] text-center sm:text-right">
              {t("footer.copyright")}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
