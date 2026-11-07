"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import {
  MapPin,
  Search,
  Wrench,
  Recycle,
  ShieldCheck,
  Phone,
  Globe,
  Navigation,
  ExternalLink,
  Filter,
  CheckCircle2,
  Info,
  ChevronRight,
  Loader2,
} from "lucide-react";

export default function LocatorPage() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [radiusKm, setRadiusKm] = useState<number>(25);
  const [certifiedOnly, setCertifiedOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [totalFound, setTotalFound] = useState(0);
  const [certificationsModalOpen, setCertificationsModalOpen] = useState(false);

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const fetchLocations = async (query = searchQuery, cat = category, rad = radiusKm, cert = certifiedOnly) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (query) params.append("query", query);
      if (cat !== "all") params.append("category", cat);
      params.append("radius_km", rad.toString());
      if (cert) params.append("certified_only", "true");

      const res = await fetch(`/api/locator/search?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
        setTotalFound(data.total_found || 0);
      }
    } catch (e) {
      console.error("Locator search error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLocations();
  }, [category, radiusKm, certifiedOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLocations();
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] dark:bg-[#000000] text-[#1D1D1F] dark:text-[#F5F5F7] flex flex-col font-sans transition-colors duration-300">
      <Navbar onOpenAuth={handleOpenAuth} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#34C759]/10 text-[#34C759] text-xs font-semibold uppercase tracking-wider mb-2">
              <MapPin className="w-3.5 h-3.5" />
              Circular Infrastructure
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#1D1D1F] dark:text-white">
              Repair & Recycler Locator
            </h1>
            <p className="mt-2 text-base text-[#86868B] max-w-2xl">
              Locate authorized independent repair technicians and SERI R2v3 / e-Stewards certified e-waste recyclers to safely execute circular device pathways.
            </p>
          </div>

          <button
            onClick={() => setCertificationsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-[#D2D2D7] dark:border-[#3A3A3C] text-xs font-semibold text-[#1D1D1F] dark:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4 text-[#34C759]" />
            About R2v3 & e-Stewards Standards
          </button>
        </div>

        {/* Filter and Search Controls */}
        <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] shadow-xs mb-8">
          <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-4 items-center mb-6">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#86868B]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by city, address, or postal code (e.g. San Francisco, Bengaluru, London)..."
                className="w-full pl-11 pr-4 py-3 bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 border border-transparent focus:border-[#0071E3] rounded-2xl text-xs sm:text-sm text-[#1D1D1F] dark:text-white focus:outline-none transition-all"
              />
            </div>
            <button
              type="submit"
              className="w-full md:w-auto px-6 py-3 rounded-2xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs sm:text-sm font-semibold transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4" />
              Find Facilities
            </button>
          </form>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#E5E5EA] dark:border-[#2C2C2E]">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-[#86868B] mr-1">Facility Type:</span>
              {[
                { id: "all", label: "All Facilities" },
                { id: "repair", label: "Repair Shops", icon: Wrench },
                { id: "recycler", label: "Recyclers", icon: Recycle },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setCategory(tab.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer flex items-center gap-1.5 ${
                    category === tab.id
                      ? "bg-[#0071E3] text-white"
                      : "bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-[#1D1D1F] dark:text-[#A1A1A6] hover:bg-black/5 dark:hover:bg-white/10"
                  }`}
                >
                  {tab.icon && <tab.icon className="w-3.5 h-3.5" />}
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <label className="flex items-center gap-2 text-xs font-medium text-[#1D1D1F] dark:text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={certifiedOnly}
                  onChange={(e) => setCertifiedOnly(e.target.checked)}
                  className="rounded border-[#D2D2D7] text-[#34C759] focus:ring-[#34C759]"
                />
                <ShieldCheck className="w-3.5 h-3.5 text-[#34C759]" />
                Certified R2v3 / e-Stewards Only
              </label>

              <div className="flex items-center gap-2 text-xs font-medium text-[#86868B]">
                <span>Radius:</span>
                <select
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Number(e.target.value))}
                  className="bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 border border-[#D2D2D7] dark:border-[#3A3A3C] rounded-lg px-2 py-1 text-xs text-[#1D1D1F] dark:text-white focus:outline-none"
                >
                  <option value={5}>5 km</option>
                  <option value={10}>10 km</option>
                  <option value={25}>25 km</option>
                  <option value={50}>50 km</option>
                  <option value={100}>100 km</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Results Count */}
        <div className="flex items-center justify-between text-xs text-[#86868B] mb-4 px-1">
          <span>Found {totalFound} circular facilities</span>
          {loading && <Loader2 className="w-4 h-4 animate-spin text-[#0071E3]" />}
        </div>

        {/* Directory Listing Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((facility: any, idx: number) => (
            <div
              key={idx}
              className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] shadow-xs flex flex-col justify-between hover:border-[#0071E3]/50 transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                        facility.category === "repair"
                          ? "bg-[#0071E3]/10 text-[#0071E3]"
                          : "bg-[#34C759]/10 text-[#34C759]"
                      }`}
                    >
                      {facility.category === "repair" ? (
                        <Wrench className="w-4 h-4" />
                      ) : (
                        <Recycle className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#86868B]">
                        {facility.category === "repair" ? "Repair Center" : "E-Waste Recycler"}
                      </span>
                    </div>
                  </div>

                  {facility.distance_km !== null && facility.distance_km !== undefined && (
                    <span className="px-2 py-1 rounded-full bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-[11px] font-semibold text-[#86868B]">
                      {facility.distance_km.toFixed(1)} km
                    </span>
                  )}
                </div>

                <h3 className="text-base font-bold text-[#1D1D1F] dark:text-white mb-1.5 leading-snug">
                  {facility.name}
                </h3>
                <p className="text-xs text-[#86868B] mb-4 line-clamp-2">
                  {facility.address || `${facility.latitude}, ${facility.longitude}`}
                </p>

                {/* Badges */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {facility.is_certified && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#34C759]/15 text-[#34C759] text-[11px] font-bold">
                      <ShieldCheck className="w-3 h-3" />
                      {facility.certifications?.join(" / ") || "Certified Facility"}
                    </span>
                  )}
                  {facility.accepts_batteries && (
                    <span className="px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/10 text-[11px] font-medium text-[#86868B]">
                      Battery Drop-off
                    </span>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-[#E5E5EA] dark:border-[#2C2C2E] flex items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  {facility.phone && (
                    <a
                      href={`tel:${facility.phone}`}
                      title={facility.phone}
                      className="p-2 rounded-xl text-[#86868B] hover:text-[#0071E3] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                    >
                      <Phone className="w-4 h-4" />
                    </a>
                  )}
                  {facility.website && (
                    <a
                      href={facility.website}
                      target="_blank"
                      rel="noreferrer"
                      title="Visit Website"
                      className="p-2 rounded-xl text-[#86868B] hover:text-[#0071E3] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                    >
                      <Globe className="w-4 h-4" />
                    </a>
                  )}
                </div>

                <a
                  href={
                    facility.google_maps_url ||
                    `https://www.google.com/maps/dir/?api=1&destination=${facility.latitude},${facility.longitude}`
                  }
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold transition-colors"
                >
                  <Navigation className="w-3.5 h-3.5" />
                  Directions
                </a>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Certifications Modal */}
      {certificationsModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="bg-white dark:bg-[#1C1C1E] p-6 sm:p-8 rounded-3xl max-w-lg w-full border border-[#D2D2D7] dark:border-[#2C2C2E] shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-2xl bg-[#34C759]/10 text-[#34C759] flex items-center justify-center">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#1D1D1F] dark:text-white">Accredited Recycler Standards</h3>
                <p className="text-xs text-[#86868B]">Global Chain of Custody & Toxic Waste Prevention</p>
              </div>
            </div>

            <div className="space-y-4 text-xs text-[#86868B] leading-relaxed mb-6">
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                <div className="font-bold text-[#1D1D1F] dark:text-white mb-1">SERI R2v3 (Responsible Recycling)</div>
                Audited standard governing data sanitization, worker health, downstream accountability, and non-landfill reuse requirements.
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                <div className="font-bold text-[#1D1D1F] dark:text-white mb-1">e-Stewards Certification</div>
                The Basel Action Network gold standard forbidding toxic electronic waste export to developing nations and child labor.
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                <div className="font-bold text-[#1D1D1F] dark:text-white mb-1">Zero-Fake Policy</div>
                ReLoop AI never marks an unverified business as certified. Badges are cross-referenced with SERI and e-Stewards registries.
              </div>
            </div>

            <button
              onClick={() => setCertificationsModalOpen(false)}
              className="w-full py-2.5 rounded-full bg-[#0071E3] text-white text-xs font-semibold hover:bg-[#0077ED] transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      )}

      <Footer />
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
    </div>
  );
}

