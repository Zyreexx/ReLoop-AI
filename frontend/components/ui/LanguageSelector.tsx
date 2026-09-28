"use client";

import React, { useState, useRef, useEffect } from "react";
import { Globe, ChevronDown, Check } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";
import { Language } from "@/lib/translations";

interface LanguageSelectorProps {
  variant?: "navbar" | "footer" | "mobile";
  className?: string;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  variant = "navbar",
  className = "",
}) => {
  const { language, setLanguage, languages } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentOption = languages.find((l) => l.code === language) || languages[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = (code: Language) => {
    setLanguage(code);
    setIsOpen(false);
  };

  if (variant === "mobile") {
    return (
      <div className={`pt-2 ${className}`}>
        <div className="text-[11px] font-semibold uppercase tracking-wider text-[#86868B] mb-2 px-1 flex items-center gap-1.5">
          <Globe className="w-3.5 h-3.5 text-[#0071E3]" />
          <span>Language / ભાષા / भाषा</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {languages.map((l) => {
            const isActive = l.code === language;
            return (
              <button
                key={l.code}
                type="button"
                onClick={() => setLanguage(l.code)}
                className={`flex flex-col items-center justify-center p-2 rounded-xl text-[12px] font-medium transition-all ${
                  isActive
                    ? "bg-[#0071E3] text-white shadow-xs"
                    : "bg-white/80 text-[#1D1D1F] border border-[#D2D2D7]/60 hover:bg-white"
                }`}
              >
                <span className="text-base leading-none mb-1">{l.flag}</span>
                <span className="font-semibold">{l.nativeName}</span>
                <span
                  className={`text-[10px] ${
                    isActive ? "text-white/80" : "text-[#86868B]"
                  }`}
                >
                  {l.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  const isFooter = variant === "footer";

  return (
    <div ref={containerRef} className={`relative inline-block text-left ${className}`}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-label="Select language"
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[12px] font-medium transition-all duration-200 cursor-pointer ${
          isFooter
            ? "bg-[#E5E5E7]/70 hover:bg-[#D2D2D7] text-[#1D1D1F] border border-[#D2D2D7]/80"
            : "bg-white/80 hover:bg-white text-[#1D1D1F] border border-[#D2D2D7]/70 shadow-2xs hover:shadow-xs backdrop-blur-xs"
        }`}
      >
        <Globe className="w-3.5 h-3.5 text-[#0071E3]" />
        <span className="text-sm leading-none">{currentOption.flag}</span>
        <span className="font-semibold">{currentOption.nativeName}</span>
        <ChevronDown
          className={`w-3 h-3 text-[#86868B] transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={`absolute z-50 w-52 rounded-2xl bg-white/95 backdrop-blur-xl border border-[#D2D2D7]/80 shadow-lg py-2 transition-all duration-150 animate-in fade-in zoom-in-95 ${
            isFooter ? "bottom-full mb-2 left-0 sm:left-auto sm:right-0" : "top-full mt-2 right-0"
          }`}
        >
          <div className="px-3.5 py-1.5 border-b border-[#F0F0F2] mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#86868B]">
              Select Language / ભાષા
            </span>
          </div>

          <div className="space-y-0.5 px-1.5">
            {languages.map((l) => {
              const isSelected = l.code === language;
              return (
                <button
                  key={l.code}
                  type="button"
                  onClick={() => handleSelect(l.code)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-[13px] transition-colors cursor-pointer ${
                    isSelected
                      ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold"
                      : "text-[#1D1D1F] hover:bg-[#F5F5F7]"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-base leading-none">{l.flag}</span>
                    <div>
                      <div className="font-medium text-[#1D1D1F]">{l.nativeName}</div>
                      <div className="text-[11px] text-[#86868B] leading-none mt-0.5">
                        {l.label}
                      </div>
                    </div>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-[#0071E3]" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
