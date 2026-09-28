"use client";

import React from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

interface ThemeToggleProps {
  className?: string;
  variant?: "navbar" | "mobile";
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = "", variant = "navbar" }) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  if (variant === "mobile") {
    return (
      <button
        type="button"
        onClick={toggleTheme}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border border-[#D2D2D7]/70 bg-white/80 dark:bg-[#1C1C1E] dark:border-[#38383A] text-[#1D1D1F] dark:text-[#F5F5F7] transition-all duration-200 cursor-pointer ${className}`}
        aria-label="Toggle theme"
      >
        <span className="text-[14px] font-medium flex items-center gap-2.5">
          {isDark ? (
            <Moon className="w-4 h-4 text-[#2997FF]" />
          ) : (
            <Sun className="w-4 h-4 text-[#FF9F0A]" />
          )}
          <span>{isDark ? "Dark Mode" : "Light Mode"}</span>
        </span>
        <span className="text-xs px-2 py-0.5 rounded-md bg-[#F5F5F7] dark:bg-[#2C2C2E] text-[#6E6E73] dark:text-[#98989D] font-mono font-medium">
          {isDark ? "Dark" : "Light"}
        </span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`relative p-2 rounded-full border border-[#D2D2D7]/70 dark:border-[#38383A] bg-white/80 dark:bg-[#1C1C1E] text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-white dark:hover:bg-[#2C2C2E] transition-all duration-300 cursor-pointer shadow-2xs hover:shadow-xs focus:outline-hidden backdrop-blur-xs flex items-center justify-center ${className}`}
      title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
      aria-label="Toggle dark/light theme"
    >
      <div className="relative w-4 h-4 flex items-center justify-center">
        <Sun
          className={`w-4 h-4 text-[#FF9F0A] absolute transition-all duration-300 transform ${
            isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
          }`}
        />
        <Moon
          className={`w-4 h-4 text-[#2997FF] absolute transition-all duration-300 transform ${
            isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"
          }`}
        />
      </div>
    </button>
  );
};
