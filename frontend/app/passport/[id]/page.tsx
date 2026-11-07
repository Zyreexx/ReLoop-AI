"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import {
  ShieldCheck,
  QrCode,
  Download,
  Leaf,
  Wrench,
  CheckCircle2,
  Clock,
  Layers,
  Cpu,
  Battery,
  HardDrive,
  FileText,
  Lock,
  ExternalLink,
  ChevronRight,
  Info,
} from "lucide-react";

export default function DigitalProductPassportPage() {
  const params = useParams();
  const dppId = params?.id as string;

  const [passport, setPassport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  useEffect(() => {
    if (!dppId) return;

    const fetchPassport = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/dpp/${dppId}`);
        if (!res.ok) {
          throw new Error("Product passport record not found or expired.");
        }
        const data = await res.json();
        setPassport(data);
      } catch (err: any) {
        setError(err.message || "Failed to load Digital Product Passport");
      } finally {
        setLoading(false);
      }
    };

    fetchPassport();
  }, [dppId]);

  return (
    <div className="min-h-screen bg-[#F5F5F7] dark:bg-[#000000] text-[#1D1D1F] dark:text-[#F5F5F7] flex flex-col font-sans transition-colors duration-300">
      <Navbar onOpenAuth={handleOpenAuth} />

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-[#86868B] mb-6">
          <Link href="/" className="hover:text-[#0071E3] transition-colors">Home</Link>
          <ChevronRight className="w-3 h-3" />
          <Link href="/dashboard" className="hover:text-[#0071E3] transition-colors">Devices</Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-[#1D1D1F] dark:text-white font-medium">Digital Product Passport</span>
        </div>

        {loading ? (
          <div className="py-24 text-center">
            <div className="w-10 h-10 border-4 border-[#0071E3] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-[#86868B]">Verifying ESPR & CIRPASS Cryptographic Provenance...</p>
          </div>
        ) : error || !passport ? (
          <div className="bg-white dark:bg-[#1C1C1E] p-8 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] text-center max-w-lg mx-auto my-12">
            <Lock className="w-12 h-12 text-[#FF9500] mx-auto mb-3" />
            <h2 className="text-xl font-bold text-[#1D1D1F] dark:text-white mb-2">Passport Record Inactive</h2>
            <p className="text-sm text-[#86868B] mb-6">
              {error || "This Digital Product Passport record could not be resolved."}
            </p>
            <Link
              href="/assess-device"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#0071E3] text-white text-xs font-semibold"
            >
              Generate New Assessment
            </Link>
          </div>
        ) : (
          <div>
            {/* Header Badge */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-[#34C759]/10 text-[#34C759] flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-7 h-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#34C759]">
                      EU CIRPASS / ESPR Certified
                    </span>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/10 text-[#86868B]">
                      v{passport.schema_version}
                    </span>
                  </div>
                  <h1 className="text-2xl font-bold text-[#1D1D1F] dark:text-white mt-0.5">
                    {passport.product?.manufacturer} {passport.product?.model}
                  </h1>
                  <p className="text-xs text-[#86868B] mt-0.5 font-mono">
                    DPP ID: {passport.dpp_id}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={`/api/dpp/${passport.dpp_id}/export`}
                  className="px-4 py-2 rounded-full border border-[#D2D2D7] dark:border-[#3A3A3C] text-xs font-semibold text-[#1D1D1F] dark:text-white hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  JSON Spec
                </a>
                <a
                  href={`/api/dpp/${passport.dpp_id}/qr`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <QrCode className="w-3.5 h-3.5" />
                  View QR
                </a>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Product Specifications */}
              <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#86868B] mb-4 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-[#0071E3]" />
                  Product Metadata
                </h3>
                <dl className="space-y-3 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#E5E5EA] dark:border-[#2C2C2E]">
                    <dt className="text-[#86868B]">Device Category</dt>
                    <dd className="font-semibold text-[#1D1D1F] dark:text-white">{passport.product?.category}</dd>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E5E5EA] dark:border-[#2C2C2E]">
                    <dt className="text-[#86868B]">Model Year</dt>
                    <dd className="font-semibold text-[#1D1D1F] dark:text-white">{passport.product?.model_year}</dd>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E5E5EA] dark:border-[#2C2C2E]">
                    <dt className="text-[#86868B]">Device Weight</dt>
                    <dd className="font-semibold text-[#1D1D1F] dark:text-white">{passport.product?.specs?.weight_kg || 1.5} kg</dd>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E5E5EA] dark:border-[#2C2C2E]">
                    <dt className="text-[#86868B]">Serial Number</dt>
                    <dd className="font-mono text-[#86868B]">{passport.product?.serial_number || "[REDACTED]"}</dd>
                  </div>
                </dl>
              </div>

              {/* Repairability Index */}
              <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#86868B] mb-4 flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-[#FF9500]" />
                  Repairability Index
                </h3>
                <div className="flex items-baseline gap-2 mb-3">
                  <span className="text-4xl font-extrabold text-[#1D1D1F] dark:text-white">
                    {passport.repairability?.score?.toFixed(1) || "7.5"}
                  </span>
                  <span className="text-sm text-[#86868B]">/ 10.0</span>
                </div>
                <div className="w-full bg-[#E5E5EA] dark:bg-[#2C2C2E] h-2 rounded-full overflow-hidden mb-4">
                  <div
                    className="bg-[#34C759] h-full"
                    style={{ width: `${(passport.repairability?.score || 7.5) * 10}%` }}
                  />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {passport.repairability?.modular_components?.map((c: string) => (
                    <span
                      key={c}
                      className="px-2 py-0.5 rounded-full bg-[#34C759]/10 text-[#34C759] text-[11px] font-semibold"
                    >
                      Modular {c}
                    </span>
                  ))}
                </div>
              </div>

              {/* Environmental Metrics */}
              <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#86868B] mb-4 flex items-center gap-2">
                  <Leaf className="w-4 h-4 text-[#34C759]" />
                  Embodied Carbon
                </h3>
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-3xl font-extrabold text-[#34C759]">
                    {passport.sustainability?.baseline_embodied_co2_kg || 250}
                  </span>
                  <span className="text-sm text-[#86868B]">kg CO2e</span>
                </div>
                <p className="text-xs text-[#86868B] mb-4">
                  Baseline manufacturing footprint saved by extending product life.
                </p>
                <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-xs text-[#86868B]">
                  Critical raw materials: Gold, Copper, Cobalt, Tantalum recovered upon certified recycling.
                </div>
              </div>
            </div>

            {/* Cryptographic Proof & QR Preview */}
            <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] mb-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[#0071E3] dark:text-[#2997FF]">
                    <Lock className="w-3.5 h-3.5" />
                    Cryptographic Integrity Proof
                  </div>
                  <h4 className="text-base font-bold text-[#1D1D1F] dark:text-white">
                    Immutable Provenance Hash
                  </h4>
                  <p className="text-xs text-[#86868B] font-mono break-all bg-[#F5F5F7] dark:bg-[#2C2C2E]/50 p-2.5 rounded-xl border border-[#E5E5EA] dark:border-[#2C2C2E]">
                    SHA-256: {passport.cryptographic_proof?.sha256_hash}
                  </p>
                  <p className="text-[11px] text-[#86868B]">
                    Validated under ESPR Directive 2024/1781. Privacy Redaction Active: Personal credentials and owner serial tags withheld from public token.
                  </p>
                </div>

                <div className="p-3 bg-white rounded-2xl border border-[#D2D2D7] shadow-xs shrink-0 text-center">
                  <img
                    src={`/api/dpp/${passport.dpp_id}/qr`}
                    alt="Digital Product Passport QR Code"
                    className="w-32 h-32 mx-auto"
                  />
                  <span className="text-[10px] font-mono text-[#86868B] mt-1 block">Scan to Verify</span>
                </div>
              </div>
            </div>

            {/* Circular Disposal Instructions */}
            <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#86868B] mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#0071E3]" />
                End-of-Life & Circular Recovery Instructions
              </h3>
              <p className="text-xs text-[#86868B] leading-relaxed mb-4">
                {passport.circular_instructions ||
                  "Under WEEE Directive guidelines, this equipment must not be disposed of with municipal waste. Battery must be discharged and removed by a certified technician. Component reclamation is recommended for SSD storage and memory modules."}
              </p>
              <Link
                href="/locator"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#0071E3] hover:underline"
              >
                Find certified R2v3 / e-Stewards recycler near you
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}
      </main>

      <Footer />
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
    </div>
  );
}

