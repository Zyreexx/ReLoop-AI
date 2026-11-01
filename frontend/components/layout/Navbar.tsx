"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { RefreshCw, ArrowRight, Menu, X, Laptop } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSelector } from "@/components/ui/LanguageSelector";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
interface NavbarProps {
  onOpenAuth: (mode: "login" | "register") => void;
}
export const Navbar: React.FC<NavbarProps> = ({ onOpenAuth }) => {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const handleAssessDeviceClick = () => {
    router.push("/assess-device");
  };
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);
  return (
    <>
      <header
        className={`sticky top-0 z-50 transition-all duration-300 ${
          scrolled
            ? "apple-nav-blur py-3 shadow-xs"
            : "bg-[#F5F5F7]/90 backdrop-blur-md py-4"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-6">
          {/* Brand Logo */}
          <Link
            href="/"
            className="flex items-center gap-2.5 text-[#1D1D1F] dark:text-white hover:opacity-90 transition-opacity shrink-0"
          >
            <div className="w-8 h-8 rounded-full bg-[#0071E3] flex items-center justify-center text-white shadow-xs">
              <RefreshCw className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-[17px] tracking-tight text-[#1D1D1F] dark:text-white">
                ReLoop <span className="text-[#0071E3] font-bold">AI</span>
              </span>
            </div>
          </Link>
          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center justify-center gap-6 lg:gap-8 text-[13.5px] font-medium text-[#6E6E73] dark:text-[#A1A1A6] flex-1 max-w-2xl mx-4">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap ${
                pathname === "/" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              {t("nav.home")}
            </Link>
            <Link
              href="/pathways"
              className={`px-3 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap ${
                pathname === "/pathways" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              {t("nav.pathways")}
            </Link>
            <Link
              href="/how-it-works"
              className={`px-3 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap ${
                pathname === "/how-it-works" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              {t("nav.howItWorks")}
            </Link>
            <Link
              href="/about"
              className={`px-3 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap ${
                pathname === "/about" || pathname === "/engine" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              {t("nav.about", "About")}
            </Link>
            {user && (
              <Link
                href="/dashboard"
                className={`px-3 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  pathname === "/dashboard"
                    ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5"
                    : "text-[#6E6E73] dark:text-[#A1A1A6]"
                }`}
              >
                <Laptop className="w-3.5 h-3.5" />
                <span>{t("nav.myDevices", "My Devices")}</span>
              </Link>
            )}
          </nav>
          {/* Actions */}
          <div className="hidden md:flex items-center gap-3 sm:gap-3.5 shrink-0">
            {user ? (
              <div className="flex items-center gap-2.5">
                <Link
                  href="/dashboard"
                  title="View My Devices Dashboard"
                  className="flex items-center gap-2 px-2.5 py-1 -my-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-7 h-7 rounded-full border border-[#D2D2D7] dark:border-[#3A3A3C] object-cover group-hover:ring-2 group-hover:ring-[#0071E3]/40 transition-all shrink-0"
                    />
                  ) : (
                    <div className="w-7 h-7 rounded-full bg-[#0071E3] text-white flex items-center justify-center text-xs font-bold shrink-0 group-hover:ring-2 group-hover:ring-[#0071E3]/40 transition-all">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <span className="text-[13px] font-medium text-[#1D1D1F] dark:text-white group-hover:text-[#0071E3] transition-colors whitespace-nowrap">
                    {user.name.split(" ")[0]}
                  </span>
                </Link>
                <span className="w-px h-3.5 bg-[#D2D2D7] dark:bg-[#3A3A3C]" />
                <button
                  type="button"
                  onClick={logout}
                  className="text-[12px] text-[#86868B] hover:text-[#FF3B30] px-1 py-1 transition-colors whitespace-nowrap cursor-pointer"
                >
                  {t("nav.signOut")}
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => onOpenAuth("login")}
                className="text-[13px] font-medium text-[#1D1D1F] dark:text-white hover:text-[#0071E3] px-3.5 py-1.5 transition-colors whitespace-nowrap cursor-pointer"
              >
                {t("nav.signIn")}
              </button>
            )}
            <button
              type="button"
              onClick={handleAssessDeviceClick}
              className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-white bg-[#0071E3] hover:bg-[#0077ED] px-4 py-2 rounded-full transition-all duration-200 cursor-pointer shadow-xs hover:shadow-sm whitespace-nowrap shrink-0"
            >
              <span>{t("nav.assessDevice")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            {/* Theme Toggle & Language Selector Dropdown */}
            <div className="flex items-center gap-1.5 shrink-0 ml-1">
              <ThemeToggle variant="navbar" />
              <LanguageSelector variant="navbar" className="ml-0.5" />
            </div>
          </div>
          {/* Mobile hamburger */}
          <button
            type="button"
            className="md:hidden p-1.5 rounded-lg text-[#1D1D1F] hover:bg-black/5"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        {/* Mobile dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white/95 backdrop-blur-xl border-b border-[#E5E5E7] px-6 py-4 flex flex-col gap-3 shadow-lg">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              {t("nav.home")}
            </Link>
            <Link
              href="/pathways"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              {t("nav.pathways")}
            </Link>
            <Link
              href="/how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              {t("nav.howItWorks")}
            </Link>
            <Link
              href="/about"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              {t("nav.about", "About")}
            </Link>
            {user && (
              <Link
                href="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="text-[15px] font-semibold text-[#0071E3] py-1.5 flex items-center gap-2"
              >
                <Laptop className="w-4 h-4" />
                <span>{t("nav.myDevices", "My Devices")}</span>
              </Link>
            )}
            {/* Mobile Theme Toggle & Language Selector */}
            <div className="pt-2 border-t border-[#E5E5E7] flex flex-col gap-2.5">
              <ThemeToggle variant="mobile" />
              <LanguageSelector variant="mobile" />
            </div>
            <div className="pt-3 border-t border-[#E5E5E7] flex flex-col gap-2">
              {user ? (
                <div className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-2">
                    {user.picture ? (
                      <img
                        src={user.picture}
                        alt={user.name}
                        className="w-7 h-7 rounded-full"
                      />
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-[#0071E3] text-white flex items-center justify-center text-xs font-bold">
                        {user.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <span className="text-sm font-semibold text-[#1D1D1F]">
                      {user.name}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    className="text-xs text-[#FF3B30] font-medium"
                  >
                    {t("nav.signOut")}
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenAuth("login");
                  }}
                  className="w-full text-center py-2.5 rounded-xl border border-[#D2D2D7] font-semibold text-sm text-[#1D1D1F]"
                >
                  {t("nav.signIn")}
                </button>
              )}
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  handleAssessDeviceClick();
                }}
                className="w-full text-center py-2.5 rounded-xl bg-[#0071E3] font-semibold text-sm text-white"
              >
                {t("nav.assessDevice")}
              </button>
            </div>
          </div>
        )}
      </header>
    </>
  );
};