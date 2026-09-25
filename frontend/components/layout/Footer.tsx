"use client";

import React from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#F5F5F7] text-[#6E6E73] text-[12px] border-t border-[#D2D2D7] pt-12 pb-16">
      <div className="max-w-6xl mx-auto px-6">
        {/* Apple-style Footnotes / Assumptions Disclosures */}
        <div className="pb-8 border-b border-[#D2D2D7] space-y-2 text-[#86868B] leading-relaxed">
          <p>
            1. <strong>Lifecycle Extensions:</strong> Expected life extension figures are calculated using component reliability models, assumes compatible OEM replacement parts are available, thermal issues are serviceable, and no latent catastrophic motherboard faults exist.
          </p>
          <p>
            2. <strong>Evidence Integrity:</strong> Photographs provide visible cosmetic and structural observations only. In accordance with ReLoop AI engineering rules, exterior photos are never claimed to prove internal electronic health (e.g. battery chemistry, SSD SMART status, or silicon stability).
          </p>
          <p>
            3. <strong>Avoided Embodied Carbon:</strong> Carbon savings are estimated against average life-cycle assessment (LCA) data for new laptop manufacturing (~180–260 kg CO₂e per typical business laptop).
          </p>
          <p>
            4. <strong>Deterministic Scoring:</strong> ReLoop pathway recommendations are scored via deterministic algorithms in Python. Multimodal AI is utilized for product identification, visible defect detection, and narrative explanations, not for final decision arbitration.
          </p>
        </div>

        {/* Directory Links */}
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-8 py-10">
          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              Circular Pathways
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a href="#pathways" className="hover:text-[#1D1D1F] transition-colors">
                  1. Targeted Repair
                </a>
              </li>
              <li>
                <a href="#pathways" className="hover:text-[#1D1D1F] transition-colors">
                  2. Component Upgrade
                </a>
              </li>
              <li>
                <a href="#pathways" className="hover:text-[#1D1D1F] transition-colors">
                  3. Full Refurbishment
                </a>
              </li>
              <li>
                <a href="#pathways" className="hover:text-[#1D1D1F] transition-colors">
                  4. Secondary Redeployment
                </a>
              </li>
              <li>
                <a href="#pathways" className="hover:text-[#1D1D1F] transition-colors">
                  5. Component Recovery
                </a>
              </li>
              <li>
                <a href="#pathways" className="hover:text-[#1D1D1F] transition-colors">
                  6. Material Recycling
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              Evidence System
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a href="#how-it-works" className="hover:text-[#1D1D1F] transition-colors">
                  Vision AI Intake
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-[#1D1D1F] transition-colors">
                  Diagnostic Telemetry
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-[#1D1D1F] transition-colors">
                  Symptom Parsing
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-[#1D1D1F] transition-colors">
                  Evidence Provenance Badges
                </a>
              </li>
              <li>
                <a href="#live-engine" className="hover:text-[#1D1D1F] transition-colors">
                  Deterministic Optimizer
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              Grand Challenge 2026
            </h4>
            <ul className="space-y-2.5">
              <li>
                <span className="text-[#1D1D1F] font-medium">PCCoE International Grand Challenge</span>
              </li>
              <li>
                <span>Track: Smart Cities, Energy & Circular Economy</span>
              </li>
              <li>
                <span>Focus: Product Life Extension</span>
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
                  <span>GitHub Repository</span>
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-[#1D1D1F] text-[13px] mb-3">
              About ReLoop
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a href="#philosophy" className="hover:text-[#1D1D1F] transition-colors">
                  Core Philosophy
                </a>
              </li>
              <li>
                <span>Positioning: The Next-Life Engine</span>
              </li>
              <li>
                <span>Target MVP: Laptop Lifecycle</span>
              </li>
              <li>
                <span>Frontend: Next.js + React + Tailwind</span>
              </li>
              <li>
                <span>Backend: FastAPI + Python Optimizer</span>
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
            <span>ReLoop AI</span>
            <span className="text-[#86868B] font-normal text-xs ml-1">
              • The Next-Life Engine for Products
            </span>
          </div>

          <div className="text-xs text-[#86868B]">
            Copyright © 2026 ReLoop AI Team. PCCoE International Grand Challenge. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};
