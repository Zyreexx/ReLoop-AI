"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import { useLanguage } from "@/context/LanguageContext";
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
  Star,
  Sparkles,
} from "lucide-react";

export default function LocatorPage() {
  const { t } = useLanguage();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [radiusKm, setRadiusKm] = useState<number>(25);
  const [certifiedOnly, setCertifiedOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [totalFound, setTotalFound] = useState(0);
  const [dataSource, setDataSource] = useState<string>("openstreetmap");
  const [googlePlacesConfigured, setGooglePlacesConfigured] = useState<boolean>(false);
  const [resolvedLocation, setResolvedLocation] = useState<string>("");
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

      const res = await fetch(`/backend-api/locator/search?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
        setTotalFound(data.total_results ?? data.total_found ?? (data.results?.length || 0));
        setDataSource(data.data_source || "openstreetmap");
        setGooglePlacesConfigured(Boolean(data.google_places_configured));
        setResolvedLocation(data.query_location || "");
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
              {t("locator.badge", "Circular Infrastructure")}
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#1D1D1F] dark:text-white">
              {t("locator.title", "Repair & Recycler Locator")}
            </h1>
            <p className="mt-2 text-base text-[#86868B] max-w-2xl">
              {t("locator.subtitle", "Locate authorized independent repair technicians and SERI R2v3 / e-Stewards certified e-waste recyclers to safely execute circular device pathways.")}
            </p>
          </div>

          <button
            onClick={() => setCertificationsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-[#D2D2D7] dark:border-[#3A3A3C] text-xs font-semibold text-[#1D1D1F] dark:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4 text-[#34C759]" />
            {t("locator.standardsBtn", "About R2v3 & e-Stewards Standards")}
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
                placeholder={t("locator.searchPlaceholder", "Search by city, address, or postal code (e.g. San Francisco, Bengaluru, London)...")}
                className="w-full pl-11 pr-4 py-3 bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 border border-transparent focus:border-[#0071E3] rounded-2xl text-xs sm:text-sm text-[#1D1D1F] dark:text-white focus:outline-none transition-all"
              />
            </div>
            <button
              type="submit"
              className="w-full md:w-auto px-6 py-3 rounded-2xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs sm:text-sm font-semibold transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4" />
              {t("locator.findBtn", "Find Facilities")}
            </button>
          </form>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#E5E5EA] dark:border-[#2C2C2E]">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-[#86868B] mr-1">{t("locator.facilityType", "Facility Type:")}</span>
              {[
                { id: "all", label: t("locator.allFacilities", "All Facilities") },
                { id: "repair", label: t("locator.repairShops", "Repair Shops"), icon: Wrench },
                { id: "recycler", label: t("locator.recyclers", "Recyclers"), icon: Recycle },
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
                {t("locator.certifiedOnly", "Certified R2v3 / e-Stewards Only")}
              </label>

              <div className="flex items-center gap-2 text-xs font-medium text-[#86868B]">
                <span>{t("locator.radius", "Radius:")}</span>
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

        {/* Results Count & Data Source Badge */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#86868B] mb-4 px-1">
          <div className="flex flex-wrap items-center gap-2">
            <span>
              {t("locator.foundPrefix", "Found")}{" "}
              <strong className="text-[#1D1D1F] dark:text-white">{totalFound}</strong>{" "}
              {t("locator.foundSuffix", "circular facilities")}
              {resolvedLocation && (
                <span className="text-[#86868B] ml-1">
                  near <span className="text-[#1D1D1F] dark:text-white font-medium">{resolvedLocation.split(",").slice(0, 3).join(",")}</span>
                </span>
              )}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/10 text-[10px] font-medium text-[#86868B] flex items-center gap-1">
              <Sparkles className="w-2.5 h-2.5 text-[#34C759]" />
              {dataSource === "google_places" ? "Google Places API" : dataSource === "geoapify" ? "Geoapify Live" : "OpenStreetMap Live"}
            </span>
          </div>
          {loading && <Loader2 className="w-4 h-4 animate-spin text-[#0071E3]" />}
        </div>

        {/* Directory Listing Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((facility: any, idx: number) => {
            const isRepair = (facility.category || "").toLowerCase().includes("repair");
            return (
              <div
                key={facility.id || idx}
                className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] shadow-xs flex flex-col justify-between hover:border-[#0071E3]/50 transition-all"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                          isRepair
                            ? "bg-[#0071E3]/10 text-[#0071E3]"
                            : "bg-[#34C759]/10 text-[#34C759]"
                        }`}
                      >
                        {isRepair ? (
                          <Wrench className="w-4 h-4" />
                        ) : (
                          <Recycle className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#86868B]">
                          {isRepair ? t("locator.repairCenter", "Repair Center") : t("locator.eWasteRecycler", "E-Waste Recycler")}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {facility.distance_km !== null && facility.distance_km !== undefined && (
                        <span className="px-2 py-1 rounded-full bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-[11px] font-semibold text-[#86868B]">
                          {facility.distance_km.toFixed(1)} km
                        </span>
                      )}
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-[#1D1D1F] dark:text-white mb-1.5 leading-snug">
                    {facility.name}
                  </h3>
                  <p className="text-xs text-[#86868B] mb-3 line-clamp-2">
                    {facility.address || `${facility.latitude}, ${facility.longitude}`}
                  </p>

                  {/* Rating & Opening Status if available */}
                  {(facility.rating !== null && facility.rating !== undefined) || (facility.open_now !== null && facility.open_now !== undefined) ? (
                    <div className="flex items-center gap-3 mb-3 text-xs">
                      {facility.rating !== null && facility.rating !== undefined && (
                        <div className="flex items-center gap-1 text-[#FF9500] font-semibold text-[11px]">
                          <Star className="w-3.5 h-3.5 fill-current" />
                          <span>{facility.rating.toFixed(1)}</span>
                          {facility.user_ratings_total && (
                            <span className="text-[#86868B] text-[10px] font-normal">
                              ({facility.user_ratings_total})
                            </span>
                          )}
                        </div>
                      )}
                      {facility.open_now !== null && facility.open_now !== undefined && (
                        <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${facility.open_now ? "text-[#34C759]" : "text-[#86868B]"}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${facility.open_now ? "bg-[#34C759]" : "bg-[#86868B]"}`} />
                          {facility.open_now ? "Open Now" : "Closed"}
                        </span>
                      )}
                    </div>
                  ) : null}

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {facility.is_certified && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#34C759]/15 text-[#34C759] text-[11px] font-bold">
                        <ShieldCheck className="w-3 h-3" />
                        {facility.certification_badge || facility.certifications?.join(" / ") || t("locator.certifiedFacility", "Certified Facility")}
                      </span>
                    )}
                    {(facility.category === "CERTIFIED_RECYCLER" || facility.category === "E_WASTE_COLLECTOR") && !facility.is_certified && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#0071E3]/10 text-[#0071E3] text-[11px] font-semibold">
                        <Recycle className="w-3 h-3" />
                        {t("locator.eWasteRecycler", "E-Waste Recycler")}
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
                      facility.directions_url ||
                      `https://www.google.com/maps/dir/?api=1&destination=${facility.latitude},${facility.longitude}`
                    }
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold transition-colors"
                  >
                    <Navigation className="w-3.5 h-3.5" />
                    {t("locator.directions", "Directions")}
                  </a>
                </div>
              </div>
            );
          })}
        </div>

        {/* Empty state when 0 results found */}
        {results.length === 0 && !loading && (
          <div className="bg-white dark:bg-[#1C1C1E] p-8 sm:p-12 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] text-center max-w-xl mx-auto my-8 shadow-xs">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
              <MapPin className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-[#1D1D1F] dark:text-white mb-2">
              {t("locator.noFacilitiesTitle", "No facilities found within selected radius")}
            </h3>
            <p className="text-xs sm:text-sm text-[#86868B] leading-relaxed mb-6">
              {t("locator.noFacilitiesDesc", "We searched for repair & recycling facilities near")}{" "}
              <strong className="text-[#1D1D1F] dark:text-white">{resolvedLocation || searchQuery || "this location"}</strong>.{" "}
              {t("locator.tryExpanding", "Try expanding the search radius or broadening your query.")}
            </p>

            {dataSource === "openstreetmap" && (
              <div className="p-4 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-left border border-[#D2D2D7]/40 dark:border-[#3A3A3C]">
                <div className="flex items-start gap-3">
                  <Info className="w-4 h-4 text-[#0071E3] shrink-0 mt-0.5" />
                  <div className="text-xs text-[#86868B] space-y-1">
                    <span className="font-semibold text-[#1D1D1F] dark:text-white block">
                      {t("locator.enableFreePlaces", "Want instant live coverage for any pincode?")}
                    </span>
                    <p>
                      {t(
                        "locator.freePlacesHelp",
                        "Get a 100% free API key from Geoapify (3,000 free requests/day, no credit card required) at myprojects.geoapify.com and add GEOAPIFY_API_KEY to your .env file, or add GOOGLE_MAPS_API_KEY."
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
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
                <h3 className="text-lg font-bold text-[#1D1D1F] dark:text-white">{t("locator.standardsTitle", "Accredited Recycler Standards")}</h3>
                <p className="text-xs text-[#86868B]">{t("locator.standardsSubtitle", "Global Chain of Custody & Toxic Waste Prevention")}</p>
              </div>
            </div>

            <div className="space-y-4 text-xs text-[#86868B] leading-relaxed mb-6">
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                <div className="font-bold text-[#1D1D1F] dark:text-white mb-1">{t("locator.modalR2", "SERI R2v3 (Responsible Recycling)")}</div>
                {t("locator.modalR2Desc", "Audited standard governing data sanitization, worker health, downstream accountability, and non-landfill reuse requirements.")}
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                <div className="font-bold text-[#1D1D1F] dark:text-white mb-1">{t("locator.modalEStewards", "e-Stewards Certification")}</div>
                {t("locator.modalEStewardsDesc", "The Basel Action Network gold standard forbidding toxic electronic waste export to developing nations and child labor.")}
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                <div className="font-bold text-[#1D1D1F] dark:text-white mb-1">{t("locator.modalZeroFake", "Zero-Fake Policy")}</div>
                {t("locator.modalZeroFakeDesc", "ReLoop AI never marks an unverified business as certified. Badges are cross-referenced with SERI and e-Stewards registries.")}
              </div>
            </div>

            <button
              onClick={() => setCertificationsModalOpen(false)}
              className="w-full py-2.5 rounded-full bg-[#0071E3] text-white text-xs font-semibold hover:bg-[#0077ED] transition-colors cursor-pointer"
            >
              {t("locator.close", "Close")}
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

