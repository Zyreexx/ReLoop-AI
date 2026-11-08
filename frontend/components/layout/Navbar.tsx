"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  RefreshCw,
  ArrowRight,
  Menu,
  X,
  Laptop,
  Home,
  Repeat,
  Workflow,
  Boxes,
  MapPin,
  Info,
} from "lucide-react";
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
  const menuContainerRef = React.useRef<HTMLDivElement>(null);

  const handleAssessDeviceClick = () => {
    router.push("/assess-device");
  };

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuContainerRef.current &&
        !menuContainerRef.current.contains(event.target as Node)
      ) {
        setMobileMenuOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileMenuOpen(false);
      }
    };

    if (mobileMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileMenuOpen]);
  return (
    <>
      <header
        className={`sticky top-0 z-50 w-full max-w-full transition-all duration-300 ${
          scrolled
            ? "apple-nav-blur py-3 shadow-xs"
            : "bg-[#F5F5F7]/90 dark:bg-[#000000]/90 backdrop-blur-md py-4"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-3 xl:gap-6">
          {/* Brand Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 text-[#1D1D1F] dark:text-white hover:opacity-90 transition-opacity shrink-0"
          >
            <div className="w-8 h-8 rounded-full bg-[#0071E3] flex items-center justify-center text-white shadow-xs">
              <RefreshCw className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-[16px] xl:text-[17px] tracking-tight text-[#1D1D1F] dark:text-white">
                ReLoop <span className="text-[#0071E3] font-bold">AI</span>
              </span>
            </div>
          </Link>
          {/* Desktop Navigation Links (Visible on xl: 1280px+) */}
          <nav className="hidden xl:flex items-center justify-center gap-1 xl:gap-2 2xl:gap-3.5 text-[12.5px] xl:text-[13px] font-medium text-[#6E6E73] dark:text-[#A1A1A6] flex-1 max-w-2xl mx-2">
            <Link
              href="/"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              <Home className="w-3.5 h-3.5 shrink-0" />
              <span>{t("nav.home")}</span>
            </Link>
            <Link
              href="/pathways"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/pathways" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              <Repeat className="w-3.5 h-3.5 shrink-0" />
              <span>{t("nav.pathways")}</span>
            </Link>
            <Link
              href="/how-it-works"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/how-it-works" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              <Workflow className="w-3.5 h-3.5 shrink-0" />
              <span>{t("nav.howItWorks")}</span>
            </Link>
            <Link
              href="/batch"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/batch" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              <Boxes className="w-3.5 h-3.5 shrink-0" />
              <span>{t("nav.batch", "Batch Fleet")}</span>
            </Link>
            <Link
              href="/locator"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/locator" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              <MapPin className="w-3.5 h-3.5 shrink-0" />
              <span>{t("nav.locator", "Recyclers")}</span>
            </Link>
            <Link
              href="/about"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/about" || pathname === "/engine" ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5" : ""
              }`}
            >
              <Info className="w-3.5 h-3.5 shrink-0" />
              <span>{t("nav.about", "About")}</span>
            </Link>
            <Link
              href="/dashboard"
              className={`px-2.5 py-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 hover:text-[#1D1D1F] dark:hover:text-white transition-all whitespace-nowrap flex items-center gap-1.5 ${
                pathname === "/dashboard"
                  ? "text-[#0071E3] dark:text-[#0071E3] font-semibold bg-[#0071E3]/5"
                  : "text-[#6E6E73] dark:text-[#A1A1A6]"
              }`}
            >
              <Laptop className="w-3.5 h-3.5 shrink-0" />
              <span>{user ? t("nav.myDevices", "My Devices") : t("nav.history", "History")}</span>
            </Link>
          </nav>
          {/* Actions (Visible on xl: 1280px+) */}
          <div className="hidden xl:flex items-center gap-2 xl:gap-2.5 shrink-0">
            {user ? (
              <div className="flex items-center gap-2">
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
                  <span className="text-[12.5px] font-medium text-[#1D1D1F] dark:text-white group-hover:text-[#0071E3] transition-colors whitespace-nowrap">
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
                className="text-[12.5px] font-medium text-[#1D1D1F] dark:text-white hover:text-[#0071E3] px-2.5 py-1.5 transition-colors whitespace-nowrap cursor-pointer"
              >
                {t("nav.signIn")}
              </button>
            )}
            <button
              type="button"
              onClick={handleAssessDeviceClick}
              className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-white bg-[#0071E3] hover:bg-[#0077ED] px-3.5 py-1.5 rounded-full transition-all duration-200 cursor-pointer shadow-xs hover:shadow-sm whitespace-nowrap shrink-0"
            >
              <span>{t("nav.assessDevice")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            {/* Theme Toggle & Language Selector Dropdown */}
            <div className="flex items-center gap-1 shrink-0">
              <ThemeToggle variant="navbar" />
              <LanguageSelector variant="navbar" className="ml-0.5" />
            </div>
          </div>
          {/* Mobile/Tablet menu wrapper (Visible below xl: < 1280px) */}
          <div className="relative xl:hidden" ref={menuContainerRef}>
            <button
              type="button"
              className="p-2 rounded-xl text-[#1D1D1F] dark:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            {/* Dropdown positioned directly under the 3-dash icon on the right, covering limited space */}
            {mobileMenuOpen && (
              <div
                className="absolute right-0 top-full mt-2 w-72 sm:w-80 max-w-[calc(100vw-2rem)] bg-white/95 dark:bg-[#1C1C1E]/95 backdrop-blur-2xl border border-[#E5E5E7] dark:border-[#38383A] rounded-2xl shadow-2xl p-3 sm:p-4 flex flex-col gap-1 z-50 animate-in fade-in zoom-in-95 duration-150 origin-top-right text-left"
              >
                <div className="flex flex-col gap-0.5">
                  <Link
                    href="/"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5"
                    }`}
                  >
                    <Home className="w-4 h-4 text-[#86868B] dark:text-[#8E8E93] shrink-0" />
                    <span>{t("nav.home")}</span>
                  </Link>
                  <Link
                    href="/pathways"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/pathways"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5"
                    }`}
                  >
                    <Repeat className="w-4 h-4 text-[#86868B] dark:text-[#8E8E93] shrink-0" />
                    <span>{t("nav.pathways")}</span>
                  </Link>
                  <Link
                    href="/how-it-works"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/how-it-works"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5"
                    }`}
                  >
                    <Workflow className="w-4 h-4 text-[#86868B] dark:text-[#8E8E93] shrink-0" />
                    <span>{t("nav.howItWorks")}</span>
                  </Link>
                  <Link
                    href="/batch"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/batch"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5"
                    }`}
                  >
                    <Boxes className="w-4 h-4 text-[#86868B] dark:text-[#8E8E93] shrink-0" />
                    <span>{t("nav.batch", "Batch Fleet")}</span>
                  </Link>
                  <Link
                    href="/locator"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/locator"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5"
                    }`}
                  >
                    <MapPin className="w-4 h-4 text-[#86868B] dark:text-[#8E8E93] shrink-0" />
                    <span>{t("nav.recyclerLocator", "Recycler Locator")}</span>
                  </Link>
                  <Link
                    href="/about"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/about" || pathname === "/engine"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5"
                    }`}
                  >
                    <Info className="w-4 h-4 text-[#86868B] dark:text-[#8E8E93] shrink-0" />
                    <span>{t("nav.about", "About")}</span>
                  </Link>
                  <Link
                    href="/dashboard"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] font-medium transition-all ${
                      pathname === "/dashboard"
                        ? "bg-[#0071E3]/10 text-[#0071E3] font-semibold dark:bg-[#0071E3]/20"
                        : "text-[#0071E3] font-semibold hover:bg-[#0071E3]/5"
                    }`}
                  >
                    <Laptop className="w-4 h-4 shrink-0" />
                    <span>{user ? t("nav.myDevices", "My Devices") : t("nav.history", "History")}</span>
                  </Link>
                </div>

                {/* Appearance: Theme & Language */}
                <div className="pt-2 mt-1 border-t border-[#E5E5E7] dark:border-[#38383A] flex items-center justify-between px-1">
                  <span className="text-[11.5px] font-medium text-[#86868B] dark:text-[#8E8E93]">{t("nav.appearance", "Appearance")}</span>
                  <div className="flex items-center gap-1.5">
                    <ThemeToggle variant="navbar" />
                    <LanguageSelector variant="navbar" />
                  </div>
                </div>

                {/* Assess Button & Auth */}
                <div className="pt-2 mt-1 border-t border-[#E5E5E7] dark:border-[#38383A] flex flex-col gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setMobileMenuOpen(false);
                      handleAssessDeviceClick();
                    }}
                    className="w-full inline-flex items-center justify-center gap-1.5 text-xs font-semibold text-white bg-[#0071E3] hover:bg-[#0077ED] py-2 px-3.5 rounded-xl transition-all shadow-xs cursor-pointer"
                  >
                    <span>{t("nav.assessDevice")}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>

                  {user ? (
                    <div className="flex items-center justify-between px-2 pt-0.5 text-xs">
                      <span className="font-medium text-[#1D1D1F] dark:text-[#F5F5F7] truncate max-w-[130px]">
                        {user.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          logout();
                          setMobileMenuOpen(false);
                        }}
                        className="text-[#FF3B30] hover:underline font-medium cursor-pointer"
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
                      className="w-full text-center py-2 rounded-xl border border-[#D2D2D7] dark:border-[#38383A] font-semibold text-xs text-[#1D1D1F] dark:text-[#F5F5F7] hover:bg-black/5 dark:hover:bg-white/5 cursor-pointer"
                    >
                      {t("nav.signIn")}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
    </>
  );
};