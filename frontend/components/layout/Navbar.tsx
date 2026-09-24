"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { RefreshCw, ArrowRight, Menu, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface NavbarProps {
  onOpenAuth: (mode: "login" | "register") => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenAuth }) => {
  const { user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
          scrolled ? "apple-nav-blur py-3 shadow-xs" : "bg-[#F5F5F7]/90 backdrop-blur-md py-4"
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          {/* Brand Logo */}
          <Link
            href="/"
            className="flex items-center gap-2.5 text-[#1D1D1F] hover:opacity-90 transition-opacity"
          >
            <div className="w-8 h-8 rounded-full bg-[#0071E3] flex items-center justify-center text-white shadow-xs">
              <RefreshCw className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-[17px] tracking-tight text-[#1D1D1F]">
                ReLoop <span className="text-[#0071E3] font-bold">AI</span>
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-7 text-[13px] font-medium text-[#6E6E73]">
            <Link href="/" className="hover:text-[#1D1D1F] transition-colors">
              Overview
            </Link>
            <Link href="/pathways" className="hover:text-[#1D1D1F] transition-colors">
              6 Pathways
            </Link>
            <Link href="/how-it-works" className="hover:text-[#1D1D1F] transition-colors">
              How It Works
            </Link>
            <Link href="/engine" className="hover:text-[#1D1D1F] transition-colors">
              Decision Engine
            </Link>
            <Link href="/philosophy" className="hover:text-[#1D1D1F] transition-colors">
              Philosophy
            </Link>
          </nav>

          {/* Actions */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3 pl-2">
                <div className="flex items-center gap-2">
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-7 h-7 rounded-full border border-[#D2D2D7] object-cover"
                    />
                  ) : (
                    <div className="w-7 h-7 rounded-full bg-[#0071E3] text-white flex items-center justify-center text-xs font-bold">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <span className="text-[13px] font-medium text-[#1D1D1F]">
                    {user.name.split(" ")[0]}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="text-[12px] text-[#6E6E73] hover:text-[#FF3B30] px-2 py-1 transition-colors cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => onOpenAuth("login")}
                className="text-[13px] font-medium text-[#1D1D1F] hover:text-[#0071E3] px-3.5 py-1.5 transition-colors cursor-pointer"
              >
                Sign In
              </button>
            )}

            <button
              type="button"
              onClick={() => onOpenAuth("register")}
              className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-white bg-[#0071E3] hover:bg-[#0077ED] px-4 py-2 rounded-full transition-all duration-200 cursor-pointer shadow-xs hover:shadow-sm"
            >
              <span>Assess Device</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
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
              Overview
            </Link>
            <Link
              href="/pathways"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              6 Circular Pathways
            </Link>
            <Link
              href="/how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              How It Works
            </Link>
            <Link
              href="/engine"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              Decision Engine
            </Link>
            <Link
              href="/philosophy"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[15px] font-medium text-[#1D1D1F] py-1.5"
            >
              Philosophy
            </Link>
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
                    Sign Out
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
                  Sign In
                </button>
              )}
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onOpenAuth("register");
                }}
                className="w-full text-center py-2.5 rounded-xl bg-[#0071E3] font-semibold text-sm text-white"
              >
                Assess Device
              </button>
            </div>
          </div>
        )}
      </header>
    </>
  );
};
