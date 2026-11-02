"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import { exportAssessmentPDF, exportAssessmentExcel } from "@/lib/reportExport";
import { useAuth, migrateGuestAssessmentsToUser } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import {
  Laptop,
  ShieldCheck,
  Wrench,
  RefreshCw,
  Sparkles,
  Plus,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  ArrowRight,
  Activity,
  BatteryCharging,
  Cpu,
  HardDrive,
  Flame,
  Eye,
  Lock,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Leaf,
  Layers,
  X,
  FileText,
  FileSpreadsheet,
  User,
  Download,
  RotateCcw,
} from "lucide-react";

interface ComponentMini {
  component: string;
  status: string;
  statusLabel?: string;
  summary?: string;
  confidence?: string;
  sourceTypes?: string[];
  evidence?: { text: string; source: string }[];
}

interface SavedAssessment {
  id: string;
  userId?: string;
  userEmail?: string;
  userName?: string;
  createdAt: string;
  backendProductId?: string;
  overallHealth: "GOOD" | "FAIR" | "DEGRADED" | "CRITICAL" | string;
  laptop?: {
    manufacturer?: string;
    model?: string;
    fullName?: string;
    category?: string;
    ageYears?: number;
  };
  report?: any;
  visual?: {
    identifiedProduct?: {
      manufacturer: string;
      model: string;
      confidence?: number;
      confirmed?: boolean;
    };
    visibleObservations?: string[];
  };
  diagnostics?: {
    deviceAgeYears?: number;
    battery?: {
      healthPercentage: number;
      cycleCount: number;
      designCapacity: number;
      fullChargeCapacity: number;
      unit: string;
      notProvided?: boolean;
    };
    ssd?: {
      healthPercentage: number;
      powerOnHours: number;
      smartStatus: string;
      notProvided?: boolean;
    };
    ram?: {
      capacityGB: number;
      testResult: string;
    };
    thermals?: {
      cpuTempC: number;
      gpuTempC: number;
      thermalThrottling: string;
      overheatingSymptoms?: boolean;
    };
    system?: {
      hardwareResult: string;
      criticalFaults: string;
    };
  };
  symptoms?: {
    selectedSymptoms?: { symptomId: string; label: string; frequency?: string }[];
    userDescription?: string;
    userObjective?: string;
  };
  conditionProfile?: ComponentMini[];
  topPathway?: {
    pathway: string;
    title: string;
    action: string;
    lifeExtensionYears: number;
    avoidedCo2Kg: number;
    estimatedCostUsd: number;
    turnaroundDays: number;
  };
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();

  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [assessments, setAssessments] = useState<SavedAssessment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<"all" | "good" | "attention" | "service">("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "health">("newest");
  const [selectedDeviceForModal, setSelectedDeviceForModal] = useState<SavedAssessment | null>(null);
  const [downloadModalDevice, setDownloadModalDevice] = useState<SavedAssessment | null>(null);
  const [activeDraft, setActiveDraft] = useState<any>(null);
  const [viewTab, setViewTab] = useState<"history" | "analytics">("history");

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  // Discard draft from localStorage
  const handleDiscardDraft = () => {
    if (confirm("Are you sure you want to discard this in-progress assessment?")) {
      localStorage.removeItem("reloop_active_assessment_draft");
      setActiveDraft(null);
    }
  };

  // Open download report options modal (PDF or Excel)
  const handleOpenDownloadModal = (dev: SavedAssessment, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setDownloadModalDevice(dev);
  };

  // Load user assessments from API & localStorage, supporting both guests and authenticated accounts
  const loadAssessments = async () => {
    setLoading(true);

    // Check for active in-progress assessment draft
    try {
      const draftStr = localStorage.getItem("reloop_active_assessment_draft");
      if (draftStr) {
        const draft = JSON.parse(draftStr);
        const hasData =
          (draft.currentStep && draft.currentStep > 1) ||
          Boolean(draft.visualData?.identifiedProduct?.model) ||
          Boolean(draft.productId);
        if (hasData) {
          setActiveDraft(draft);
        } else {
          setActiveDraft(null);
        }
      } else {
        setActiveDraft(null);
      }
    } catch {
      setActiveDraft(null);
    }

    if (user?.email) {
      const userEmail = user.email.toLowerCase().trim();
      const userListKey = `reloop_user_assessments_${userEmail}`;

      // Automatically migrate any pending guest evaluations into this user account
      try {
        await migrateGuestAssessmentsToUser(userEmail);
      } catch (e) {
        console.warn("Failed migrating guest assessments:", e);
      }

      let combinedList: SavedAssessment[] = [];

      // 1. Read from localStorage
      try {
        const localData = localStorage.getItem(userListKey);
        if (localData) {
          const parsed = JSON.parse(localData);
          if (Array.isArray(parsed)) combinedList = parsed;
        }
      } catch (e) {
        console.warn("Could not read localStorage user assessments:", e);
      }

      // 2. Fetch from Next.js server API
      try {
        const res = await fetch(`/api/assessments?userId=${encodeURIComponent(userEmail)}`);
        if (res.ok) {
          const data = await res.json();
          if (data.assessments && Array.isArray(data.assessments)) {
            const map = new Map<string, SavedAssessment>();
            for (const item of combinedList) map.set(item.id, item);
            for (const item of data.assessments) map.set(item.id, item);
            combinedList = Array.from(map.values());
          }
        }
      } catch (e) {
        console.warn("Could not fetch API user assessments:", e);
      }

      setAssessments(combinedList);
    } else {
      // Guest mode: load any guest evaluations
      try {
        const guestData = localStorage.getItem("reloop_guest_assessments");
        let list: SavedAssessment[] = [];
        if (guestData) {
          const parsed = JSON.parse(guestData);
          if (Array.isArray(parsed)) list = parsed;
        }
        if (list.length === 0) {
          const current = localStorage.getItem("current_assessment");
          if (current) {
            try {
              const parsed = JSON.parse(current);
              if (parsed && parsed.id) list = [parsed];
            } catch {}
          }
        }
        setAssessments(list);
      } catch (e) {
        console.warn("Could not read guest assessments:", e);
      }
    }

    setLoading(false);
  };

  useEffect(() => {
    loadAssessments();
  }, [user]);


  // Delete an assessment
  const handleDeleteAssessment = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to remove this device assessment?")) return;

    // Update state
    const nextList = assessments.filter((a) => a.id !== id);
    setAssessments(nextList);

    if (user?.email) {
      const userEmail = user.email.toLowerCase().trim();
      const userListKey = `reloop_user_assessments_${userEmail}`;
      try {
        localStorage.setItem(userListKey, JSON.stringify(nextList));
        localStorage.removeItem(`assessment_${id}`);
      } catch {}

      try {
        await fetch(`/api/assessments?id=${encodeURIComponent(id)}`, { method: "DELETE" });
      } catch (e) {
        console.warn("Failed to delete assessment from API:", e);
      }
    } else {
      try {
        localStorage.setItem("reloop_guest_assessments", JSON.stringify(nextList));
        localStorage.removeItem(`assessment_${id}`);
        const current = localStorage.getItem("current_assessment");
        if (current) {
          const parsed = JSON.parse(current);
          if (parsed?.id === id) localStorage.removeItem("current_assessment");
        }
      } catch {}
    }
  };

  // Filter and sort assessments
  const filteredAssessments = useMemo(() => {
    return assessments
      .filter((item) => {
        const mfr = item.visual?.identifiedProduct?.manufacturer || "";
        const model = item.visual?.identifiedProduct?.model || "";
        const query = searchQuery.trim().toLowerCase();

        // Search check
        if (query) {
          const matched =
            mfr.toLowerCase().includes(query) ||
            model.toLowerCase().includes(query) ||
            item.id.toLowerCase().includes(query);
          if (!matched) return false;
        }

        // Status check
        if (statusFilter === "good") {
          return item.overallHealth?.toUpperCase() === "GOOD";
        }
        if (statusFilter === "attention") {
          return item.overallHealth?.toUpperCase() === "FAIR";
        }
        if (statusFilter === "service") {
          return (
            item.overallHealth?.toUpperCase() === "DEGRADED" ||
            item.overallHealth?.toUpperCase() === "CRITICAL"
          );
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === "newest") {
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        }
        if (sortBy === "oldest") {
          return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
        }
        if (sortBy === "health") {
          const rank = (h: string) =>
            h === "GOOD" ? 3 : h === "FAIR" ? 2 : h === "DEGRADED" ? 1 : 0;
          return rank(b.overallHealth) - rank(a.overallHealth);
        }
        return 0;
      });
  }, [assessments, searchQuery, statusFilter, sortBy]);

  // Aggregate KPI stats
  const stats = useMemo(() => {
    const total = assessments.length;
    let totalAvoidedCo2 = 0;
    let healthyCount = 0;
    const pathwayCount: Record<string, number> = {};

    for (const a of assessments) {
      if (a.topPathway?.avoidedCo2Kg) {
        totalAvoidedCo2 += a.topPathway.avoidedCo2Kg;
      } else {
        totalAvoidedCo2 += 180; // default benchmark
      }

      if (a.overallHealth === "GOOD") healthyCount++;

      const pw = a.topPathway?.pathway || "REPAIR";
      pathwayCount[pw] = (pathwayCount[pw] || 0) + 1;
    }

    const avgHealthPct = total > 0 ? Math.round((healthyCount / total) * 100) : 0;

    // Top pathway
    let topPw = "Repair";
    let maxCount = 0;
    for (const [k, v] of Object.entries(pathwayCount)) {
      if (v > maxCount) {
        maxCount = v;
        topPw = k;
      }
    }

    return {
      total,
      totalAvoidedCo2,
      avgHealthPct,
      topPw,
    };
  }, [assessments]);

  const getStatusBadge = (health: string) => {
    const norm = (health || "").toUpperCase();
    if (norm === "GOOD") {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#34C759]/10 text-[#34C759] border border-[#34C759]/20">
          <CheckCircle2 size={13} />
          <span>Good Condition</span>
        </span>
      );
    }
    if (norm === "FAIR") {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FF9F0A]/10 text-[#FF9F0A] border border-[#FF9F0A]/20">
          <AlertTriangle size={13} />
          <span>Needs Attention</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FF3B30]/10 text-[#FF3B30] border border-[#FF3B30]/20">
        <Wrench size={13} />
        <span>Service Required</span>
      </span>
    );
  };

  const getComponentStatusDot = (status: string) => {
    const s = (status || "").toLowerCase();
    if (s.includes("good") || s === "pass") return "bg-[#34C759]";
    if (s.includes("attention") || s.includes("degraded") || s === "fair") return "bg-[#FF9F0A]";
    if (s.includes("service") || s.includes("fail") || s.includes("replace")) return "bg-[#FF3B30]";
    return "bg-[#8E8E93]";
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F5F7] dark:bg-[#000000] text-[#1D1D1F] dark:text-[#F5F5F7] transition-colors">
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
      <Navbar onOpenAuth={handleOpenAuth} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-10 sm:py-14">
        {!user && assessments.length === 0 ? (
          /* EMPTY GUEST WELCOME CARD */
          <div className="max-w-xl mx-auto py-16 text-center">
            <div className="apple-card p-8 sm:p-12 bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] shadow-xl rounded-3xl">
              <div className="w-14 h-14 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center mx-auto mb-5">
                <Laptop className="w-7 h-7" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[#1D1D1F] dark:text-white tracking-tight mb-3">
                Hardware Ledger & Inventory
              </h2>
              <p className="text-sm text-[#6E6E73] dark:text-[#A1A1A6] leading-relaxed mb-8">
                Assess your laptop freely without an account to see component health and circular pathways, or sign in to load your saved account devices.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <Link
                  href="/assess-device"
                  className="inline-flex items-center justify-center gap-2 w-full sm:w-auto py-3 px-6 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white font-semibold text-sm transition-all shadow-md cursor-pointer"
                >
                  <Plus size={16} />
                  <span>Assess a Device</span>
                </Link>
                <button
                  type="button"
                  onClick={() => handleOpenAuth("login")}
                  className="inline-flex items-center justify-center gap-2 w-full sm:w-auto py-3 px-6 rounded-full border border-[#D2D2D7] dark:border-[#3A3A3C] text-[#1D1D1F] dark:text-white font-semibold text-sm hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E] transition-all cursor-pointer"
                >
                  <span>Sign In / Create Account</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* HARDWARE DASHBOARD (AVAILABLE BOTH FOR GUESTS WITH RECENT EVALUATION AND AUTHENTICATED USERS) */
          <div className="space-y-8">
            {/* Active In-Progress Assessment Draft Alert Card */}
            {activeDraft && (
              <div className="p-5 rounded-3xl bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-blue-500/5 border border-[#0071E3]/30 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-2xl bg-[#0071E3] text-white flex items-center justify-center shrink-0 shadow-xs">
                    <RotateCcw size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#0071E3] bg-[#0071E3]/15 px-2 py-0.5 rounded-full">
                        In-Progress Assessment
                      </span>
                      <span className="text-xs text-[#86868B]">Step {activeDraft.currentStep || 1} of 4</span>
                    </div>
                    <p className="text-sm font-bold text-[#1D1D1F] dark:text-white mt-0.5">
                      {activeDraft.visualData?.identifiedProduct?.manufacturer || "Laptop"}{" "}
                      {activeDraft.visualData?.identifiedProduct?.model || "Assessment in progress"}
                    </p>
                    <p className="text-xs text-[#6E6E73] dark:text-[#A1A1A6]">
                      You navigated away while assessing this device. All scanned diagnostics and telemetry remain intact.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={handleDiscardDraft}
                    className="px-3.5 py-2 rounded-full text-xs font-medium text-[#FF3B30] hover:bg-[#FF3B30]/10 border border-[#FF3B30]/25 transition-all cursor-pointer"
                  >
                    Discard Draft
                  </button>
                  <Link
                    href="/assess-device"
                    className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold shadow-xs hover:shadow-sm transition-all cursor-pointer"
                  >
                    <span>Resume Assessment</span>
                    <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            )}

            {/* Guest Banner if not signed in */}
            {!user && (
              <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 text-[#1D1D1F] dark:text-white flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
                    <Sparkles size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">Guest Assessment Ledger</p>
                    <p className="text-xs text-[#6E6E73] dark:text-[#A1A1A6]">
                      Showing hardware evaluated in this browser. Sign in or create an account to permanently sync and save your history.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleOpenAuth("login")}
                  className="px-5 py-2 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold shrink-0 shadow-xs cursor-pointer"
                >
                  Sign In to Save
                </button>
              </div>
            )}

            {/* Top Page Header & Primary Actions */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#E5E5E7] dark:border-[#2C2C2E]">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0071E3]/10 text-[#0071E3] text-xs font-semibold tracking-wide uppercase mb-3">
                  <Laptop size={13} />
                  <span>Assessment History & Hardware Ledger</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-bold text-[#1D1D1F] dark:text-white tracking-tight mb-2">
                  Assessment History
                </h1>
                <p className="text-sm sm:text-base text-[#6E6E73] dark:text-[#A1A1A6] max-w-2xl leading-relaxed">
                  {user ? (
                    <>
                      Assessed laptops for <span className="font-semibold text-[#1D1D1F] dark:text-white">{user.name}</span> ({user.email}). Inspect comprehensive component profiles, download engineering reports, or launch circular optimization.
                    </>
                  ) : (
                    "Manage your evaluated hardware, inspect component condition profiles, download assessment reports, and review circular disposition pathways."
                  )}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Link
                  href="/assess-device"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs sm:text-sm font-semibold transition-all shadow-md cursor-pointer"
                >
                  <Plus size={16} />
                  <span>Assess New Device</span>
                </Link>
              </div>
            </div>

            {/* KPI Summary Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {/* Card 1: Registered Devices */}
              <div className="apple-card p-6 bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] rounded-3xl shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6] uppercase tracking-wider">
                    Total Devices
                  </span>
                  <div className="w-8 h-8 rounded-full bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
                    <Laptop size={16} />
                  </div>
                </div>
                <div className="text-3xl font-bold text-[#1D1D1F] dark:text-white tracking-tight">
                  {stats.total}
                </div>
                <div className="text-xs text-[#6E6E73] dark:text-[#A1A1A6] mt-1">
                  Active in condition ledger
                </div>
              </div>

              {/* Card 2: Carbon Avoided */}
              <div className="apple-card p-6 bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] rounded-3xl shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6] uppercase tracking-wider">
                    Avoided CO₂e
                  </span>
                  <div className="w-8 h-8 rounded-full bg-[#34C759]/10 text-[#34C759] flex items-center justify-center">
                    <Leaf size={16} />
                  </div>
                </div>
                <div className="text-3xl font-bold text-[#1D1D1F] dark:text-white tracking-tight">
                  ~{stats.totalAvoidedCo2} <span className="text-sm font-normal text-[#6E6E73] dark:text-[#A1A1A6]">kg</span>
                </div>
                <div className="text-xs text-[#34C759] mt-1 font-medium">
                  Embodied carbon abated
                </div>
              </div>

              {/* Card 3: Healthy Ratio */}
              <div className="apple-card p-6 bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] rounded-3xl shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6] uppercase tracking-wider">
                    Condition Ratio
                  </span>
                  <div className="w-8 h-8 rounded-full bg-[#FF9F0A]/10 text-[#FF9F0A] flex items-center justify-center">
                    <Activity size={16} />
                  </div>
                </div>
                <div className="text-3xl font-bold text-[#1D1D1F] dark:text-white tracking-tight">
                  {stats.avgHealthPct}%
                </div>
                <div className="text-xs text-[#6E6E73] dark:text-[#A1A1A6] mt-1">
                  Good operating condition
                </div>
              </div>

              {/* Card 4: Top Circular Pathway */}
              <div className="apple-card p-6 bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] rounded-3xl shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6] uppercase tracking-wider">
                    Primary Pathway
                  </span>
                  <div className="w-8 h-8 rounded-full bg-[#AF52DE]/10 text-[#AF52DE] flex items-center justify-center">
                    <Sparkles size={16} />
                  </div>
                </div>
                <div className="text-2xl font-bold text-[#1D1D1F] dark:text-white tracking-tight uppercase">
                  {stats.topPw}
                </div>
                <div className="text-xs text-[#6E6E73] dark:text-[#A1A1A6] mt-1">
                  Highest economic yield
                </div>
              </div>
            </div>

            {/* View Mode Toggle: History vs Fleet Analytics */}
            <div className="flex items-center gap-2 border-b border-[#E5E5E7] dark:border-[#2C2C2E] pb-3">
              <button
                type="button"
                onClick={() => setViewTab("history")}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                  viewTab === "history"
                    ? "bg-[#0071E3] text-white shadow-xs"
                    : "text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-black/5 dark:hover:bg-white/5"
                }`}
              >
                <FileText size={15} />
                <span>Assessed Laptops History ({assessments.length})</span>
              </button>
              <button
                type="button"
                onClick={() => setViewTab("analytics")}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                  viewTab === "analytics"
                    ? "bg-[#0071E3] text-white shadow-xs"
                    : "text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-black/5 dark:hover:bg-white/5"
                }`}
              >
                <Activity size={15} />
                <span>Fleet & Impact Analytics</span>
              </button>
            </div>

            {/* Filter & Search Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] shadow-xs">
              {/* Search Box */}
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#86868B]" />
                <input
                  type="text"
                  placeholder="Filter by manufacturer or model (e.g. Dell, ThinkPad)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-xs sm:text-sm rounded-xl bg-[#F5F5F7] dark:bg-[#2C2C2E] border border-transparent focus:border-[#0071E3] focus:outline-hidden transition-all text-[#1D1D1F] dark:text-white"
                />
              </div>

              {/* Status Filter Tabs */}
              <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
                <button
                  type="button"
                  onClick={() => setStatusFilter("all")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    statusFilter === "all"
                      ? "bg-[#0071E3] text-white shadow-xs"
                      : "text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E]"
                  }`}
                >
                  All ({assessments.length})
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("good")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    statusFilter === "good"
                      ? "bg-[#34C759] text-white shadow-xs"
                      : "text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E]"
                  }`}
                >
                  Good
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("attention")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    statusFilter === "attention"
                      ? "bg-[#FF9F0A] text-white shadow-xs"
                      : "text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E]"
                  }`}
                >
                  Attention
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("service")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    statusFilter === "service"
                      ? "bg-[#FF3B30] text-white shadow-xs"
                      : "text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E]"
                  }`}
                >
                  Degraded
                </button>
              </div>

              {/* Sort Dropdown */}
              <div className="flex items-center gap-2">
                <select
                  value={sortBy}
                  onChange={(e: any) => setSortBy(e.target.value)}
                  className="px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] dark:bg-[#2C2C2E] border border-transparent text-[#1D1D1F] dark:text-white font-medium focus:outline-hidden cursor-pointer"
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="health">Health Score</option>
                </select>
              </div>
            </div>

            {/* Device Cards Grid */}
            {loading ? (
              <div className="py-20 text-center">
                <div className="w-10 h-10 rounded-full border-4 border-[#0071E3] border-t-transparent animate-spin mx-auto mb-3" />
                <p className="text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6]">
                  Loading your device assessments...
                </p>
              </div>
            ) : filteredAssessments.length === 0 ? (
              /* EMPTY STATE */
              <div className="apple-card p-12 bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] rounded-3xl text-center max-w-xl mx-auto shadow-sm">
                <div className="w-16 h-16 rounded-3xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center mx-auto mb-5 shadow-xs">
                  <Laptop className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-[#1D1D1F] dark:text-white tracking-tight mb-2">
                  No devices found
                </h3>
                <p className="text-sm text-[#6E6E73] dark:text-[#A1A1A6] leading-relaxed mb-8">
                  {searchQuery || statusFilter !== "all"
                    ? "No assessed devices match your active search and filter criteria."
                    : "You haven't assessed any hardware yet. Run our 5-step intake to analyze physical components, synthesize a condition profile, and receive deterministic circular recommendations."}
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <Link
                    href="/assess-device"
                    className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md w-full sm:w-auto cursor-pointer"
                  >
                    <span>Assess Your First Device</span>
                    <ArrowRight size={16} />
                  </Link>

                </div>
              </div>
            ) : (
              /* CARDS GRID */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredAssessments.map((dev) => {
                  const mfr = dev.visual?.identifiedProduct?.manufacturer || "Laptop";
                  const model = dev.visual?.identifiedProduct?.model || "Standard Model";
                  const dateStr = dev.createdAt
                    ? new Date(dev.createdAt).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    : "Recently";

                  const age = dev.diagnostics?.deviceAgeYears || 4;
                  const components = dev.conditionProfile || [];
                  const pw = dev.topPathway?.pathway || "REPAIR";

                  return (
                    <div
                      key={dev.id}
                      className="apple-card group bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] hover:border-[#0071E3]/50 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                    >
                      {/* Card Top: Brand Badge & Status */}
                      <div>
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div>
                            <span className="text-[11px] font-semibold text-[#86868B] uppercase tracking-wider">
                              {mfr}
                            </span>
                            <h3 className="text-lg font-bold text-[#1D1D1F] dark:text-white tracking-tight line-clamp-1 group-hover:text-[#0071E3] transition-colors">
                              {model}
                            </h3>
                            <div className="text-xs text-[#86868B] flex items-center gap-2 mt-0.5">
                              <span>{age} yrs old</span>
                              <span>•</span>
                              <span>{dateStr}</span>
                            </div>
                          </div>
                          <div>{getStatusBadge(dev.overallHealth)}</div>
                        </div>

                        {/* Assessed User Attribution Pill */}
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-[#F5F5F7] dark:bg-[#2C2C2E] text-[11px] text-[#6E6E73] dark:text-[#A1A1A6] mb-3">
                          <User size={12} className="text-[#0071E3] shrink-0" />
                          <span className="truncate">
                            Assessed for: <strong className="text-[#1D1D1F] dark:text-white font-medium">{dev.userName || dev.userEmail || (user?.name || "Guest User")}</strong>
                            {dev.userEmail && <span className="opacity-75 ml-1">({dev.userEmail})</span>}
                          </span>
                        </div>

                        {/* 8-Component Mini Dots Grid */}
                        <div className="bg-[#F5F5F7] dark:bg-[#2C2C2E] p-3.5 rounded-2xl mb-4">
                          <div className="flex items-center justify-between text-[11px] font-semibold text-[#86868B] mb-2 uppercase tracking-wider">
                            <span>Component Integrity (8)</span>
                            <ShieldCheck size={13} className="text-[#0071E3]" />
                          </div>

                          <div className="grid grid-cols-4 gap-2">
                            {components.slice(0, 8).map((comp, idx) => (
                              <div
                                key={idx}
                                title={`${comp.component}: ${comp.statusLabel || comp.status}`}
                                className="flex items-center gap-1.5 p-1 rounded-md bg-white dark:bg-[#1C1C1E] text-[10px] text-[#1D1D1F] dark:text-white border border-[#E5E5E7]/50 dark:border-[#3A3A3C]"
                              >
                                <span
                                  className={`w-2 h-2 rounded-full shrink-0 ${getComponentStatusDot(
                                    comp.status
                                  )}`}
                                />
                                <span className="truncate font-medium">{comp.component.split(" ")[0]}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Recommended Pathway Strip */}
                        <div className="p-3.5 rounded-2xl bg-[#0071E3]/5 dark:bg-[#0071E3]/10 border border-[#0071E3]/15 mb-4">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] font-bold text-[#0071E3] uppercase tracking-wider">
                              Optimal Circular Route
                            </span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#0071E3] text-white">
                              {pw}
                            </span>
                          </div>
                          <p className="text-xs font-semibold text-[#1D1D1F] dark:text-white line-clamp-1">
                            {dev.topPathway?.title || "Modular Repair & Thermal Servicing"}
                          </p>

                          <div className="flex items-center gap-3 mt-2 text-[11px] text-[#6E6E73] dark:text-[#A1A1A6]">
                            <span className="flex items-center gap-1">
                              <Leaf size={11} className="text-[#34C759]" />
                              <span>{dev.topPathway?.avoidedCo2Kg || 215} kg CO₂e</span>
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock size={11} className="text-[#0071E3]" />
                              <span>+{dev.topPathway?.lifeExtensionYears || 3.5} Yrs Life</span>
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Card Actions Footer */}
                      <div className="pt-3 border-t border-[#E5E5E7] dark:border-[#2C2C2E] flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => setSelectedDeviceForModal(dev)}
                            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6E6E73] dark:text-[#A1A1A6] hover:text-[#0071E3] transition-colors py-1.5 px-2.5 rounded-lg hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E] cursor-pointer"
                            title="Inspect component condition details"
                          >
                            <Eye size={14} />
                            <span>Inspect</span>
                          </button>

                          <button
                            type="button"
                            onClick={(e) => handleOpenDownloadModal(dev, e)}
                            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#0071E3] hover:text-[#0077ED] transition-colors py-1.5 px-2.5 rounded-lg hover:bg-[#0071E3]/10 cursor-pointer"
                            title="Download Assessment Report (PDF or Excel)"
                          >
                            <Download size={13} />
                            <span>Report</span>
                          </button>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={(e) => handleDeleteAssessment(dev.id, e)}
                            title="Remove from saved history"
                            className="p-1.5 rounded-lg text-[#86868B] hover:text-[#FF3B30] hover:bg-[#FF3B30]/10 transition-colors cursor-pointer"
                          >
                            <Trash2 size={15} />
                          </button>

                          <Link
                            href={`/engine?assessment_id=${dev.id}`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold transition-all shadow-xs cursor-pointer"
                          >
                            <span>Optimizer</span>
                            <ArrowRight size={13} />
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>

      {/* QUICK-VIEW INSPECTION MODAL */}
      {selectedDeviceForModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/50 backdrop-blur-xs animate-fade-in">
          <div className="apple-card bg-white dark:bg-[#1C1C1E] border border-[#E5E5E7] dark:border-[#2C2C2E] rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 sm:p-8 relative">
            {/* Modal Close Button */}
            <button
              type="button"
              onClick={() => setSelectedDeviceForModal(null)}
              className="absolute top-5 right-5 p-2 rounded-full text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E] transition-colors cursor-pointer"
            >
              <X size={18} />
            </button>

            {/* Modal Header */}
            <div className="mb-6">
              <span className="text-xs font-semibold text-[#0071E3] uppercase tracking-wider">
                Evidence & Condition Assessment Report
              </span>
              <h2 className="text-2xl font-bold text-[#1D1D1F] dark:text-white tracking-tight mt-0.5">
                {selectedDeviceForModal.laptop?.fullName || `${selectedDeviceForModal.visual?.identifiedProduct?.manufacturer || "Laptop"} ${selectedDeviceForModal.visual?.identifiedProduct?.model || "Standard Model"}`}
              </h2>
              <div className="flex items-center gap-1.5 text-xs text-[#6E6E73] dark:text-[#A1A1A6] mt-1.5">
                <User size={13} className="text-[#0071E3] shrink-0" />
                <span>
                  Assessed for: <strong className="text-[#1D1D1F] dark:text-white">{selectedDeviceForModal.userName || selectedDeviceForModal.userEmail || (user?.name || "Guest User")}</strong>
                  {selectedDeviceForModal.userEmail && <span className="opacity-75 ml-1">({selectedDeviceForModal.userEmail})</span>}
                </span>
              </div>
              <div className="text-xs text-[#86868B] mt-1 flex flex-wrap items-center gap-3">
                <span>Assessment ID: {selectedDeviceForModal.id}</span>
                <span>•</span>
                <span>Overall Condition: <strong className="text-[#1D1D1F] dark:text-white">{selectedDeviceForModal.overallHealth}</strong></span>
                <span>•</span>
                <span>{new Date(selectedDeviceForModal.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
              </div>
            </div>

            {/* Circular Disposition Recommendation Banner */}
            {selectedDeviceForModal.topPathway && (
              <div className="p-4 rounded-2xl bg-[#0071E3]/5 dark:bg-[#0071E3]/10 border border-[#0071E3]/20 mb-6">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-[#0071E3] uppercase tracking-wider">
                    Recommended Circular Strategy
                  </span>
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#0071E3] text-white">
                    {selectedDeviceForModal.topPathway.pathway}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-[#1D1D1F] dark:text-white">
                  {selectedDeviceForModal.topPathway.title}
                </h4>
                <div className="flex flex-wrap items-center gap-4 mt-2.5 text-xs text-[#6E6E73] dark:text-[#A1A1A6]">
                  <span className="flex items-center gap-1">
                    <Leaf size={13} className="text-[#34C759]" />
                    <span>Avoided CO₂e: <strong className="text-[#1D1D1F] dark:text-white">{selectedDeviceForModal.topPathway.avoidedCo2Kg} kg</strong></span>
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock size={13} className="text-[#0071E3]" />
                    <span>Life Extension: <strong className="text-[#1D1D1F] dark:text-white">+{selectedDeviceForModal.topPathway.lifeExtensionYears} Years</strong></span>
                  </span>
                  <span>•</span>
                  <span>Est. Servicing Cost: <strong className="text-[#1D1D1F] dark:text-white">${selectedDeviceForModal.topPathway.estimatedCostUsd}</strong></span>
                </div>
              </div>
            )}

            {/* Diagnostics Quick Snapshot */}
            {selectedDeviceForModal.diagnostics && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E] text-center">
                  <div className="text-[11px] text-[#86868B]">Battery Health</div>
                  <div className="text-base font-bold text-[#1D1D1F] dark:text-white mt-0.5">
                    {selectedDeviceForModal.diagnostics.battery?.healthPercentage || "--"}%
                  </div>
                  <div className="text-[10px] text-[#86868B]">
                    {selectedDeviceForModal.diagnostics.battery?.cycleCount || 0} cycles
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E] text-center">
                  <div className="text-[11px] text-[#86868B]">SSD Endurance</div>
                  <div className="text-base font-bold text-[#1D1D1F] dark:text-white mt-0.5">
                    {selectedDeviceForModal.diagnostics.ssd?.healthPercentage || "--"}%
                  </div>
                  <div className="text-[10px] text-[#34C759]">
                    {selectedDeviceForModal.diagnostics.ssd?.smartStatus || "PASS"}
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E] text-center">
                  <div className="text-[11px] text-[#86868B]">RAM Tested</div>
                  <div className="text-base font-bold text-[#1D1D1F] dark:text-white mt-0.5">
                    {selectedDeviceForModal.diagnostics.ram?.capacityGB || 16} GB
                  </div>
                  <div className="text-[10px] text-[#34C759]">
                    {selectedDeviceForModal.diagnostics.ram?.testResult || "PASS"}
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E] text-center">
                  <div className="text-[11px] text-[#86868B]">CPU Temp</div>
                  <div className="text-base font-bold text-[#1D1D1F] dark:text-white mt-0.5">
                    {selectedDeviceForModal.diagnostics.thermals?.cpuTempC || 75}°C
                  </div>
                  <div className="text-[10px] text-[#FF9F0A]">
                    {selectedDeviceForModal.diagnostics.thermals?.thermalThrottling || "NONE"}
                  </div>
                </div>
              </div>
            )}

            {/* Component-Level Condition Breakdown */}
            <div className="space-y-3 mb-6">
              <h4 className="text-xs font-bold text-[#86868B] uppercase tracking-wider">
                Synthesized 8-Component Profile
              </h4>

              <div className="space-y-2">
                {(selectedDeviceForModal.conditionProfile || []).map((comp, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl border border-[#E5E5E7] dark:border-[#2C2C2E] bg-white dark:bg-[#1C1C1E] flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${getComponentStatusDot(comp.status)}`} />
                      <div>
                        <div className="text-xs font-bold text-[#1D1D1F] dark:text-white">
                          {comp.component}
                        </div>
                        <div className="text-[11px] text-[#6E6E73] dark:text-[#A1A1A6]">
                          {comp.summary || comp.statusLabel}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-[#F5F5F7] dark:bg-[#2C2C2E] text-[#6E6E73] dark:text-[#A1A1A6]">
                        {comp.statusLabel || comp.status}
                      </span>
                      <span className="text-[10px] text-[#86868B]">
                        {comp.confidence || "High"} Conf.
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* User Symptoms & Objectives */}
            {selectedDeviceForModal.symptoms?.userDescription && (
              <div className="p-3.5 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E] mb-6">
                <span className="text-[11px] font-bold text-[#86868B] uppercase tracking-wider block mb-1">
                  Reported User Notes:
                </span>
                <p className="text-xs text-[#1D1D1F] dark:text-[#F5F5F7] italic">
                  "{selectedDeviceForModal.symptoms.userDescription}"
                </p>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-4 border-t border-[#E5E5E7] dark:border-[#2C2C2E]">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => exportAssessmentPDF(selectedDeviceForModal)}
                  className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-full border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 text-xs font-semibold transition-colors cursor-pointer"
                  title="Download official PDF audit report"
                >
                  <FileText size={13} />
                  <span>Download PDF</span>
                </button>

                <button
                  type="button"
                  onClick={() => exportAssessmentExcel(selectedDeviceForModal)}
                  className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-full border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 text-xs font-semibold transition-colors cursor-pointer"
                  title="Export structured Excel data sheet"
                >
                  <FileSpreadsheet size={13} />
                  <span>Export Excel</span>
                </button>
              </div>

              <div className="flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setSelectedDeviceForModal(null)}
                  className="px-4 py-2 rounded-full text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E] transition-colors cursor-pointer"
                >
                  Close
                </button>

                <Link
                  href={`/engine?assessment_id=${selectedDeviceForModal.id}`}
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold transition-all shadow-md cursor-pointer"
                >
                  <span>Launch Optimizer</span>
                  <ArrowRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

            {/* ─── DOWNLOAD FORMAT SELECTION MODAL (PDF / EXCEL) ─── */}
      {downloadModalDevice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white dark:bg-[#1C1C1E] rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-[#E5E5E7] dark:border-[#2C2C2E]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
                  <Download size={18} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#1D1D1F] dark:text-white">
                    Download Assessment Report
                  </h3>
                  <p className="text-xs text-[#86868B] truncate max-w-[240px]">
                    {downloadModalDevice.laptop?.fullName || downloadModalDevice.laptop?.model || "Laptop Asset"}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setDownloadModalDevice(null)}
                className="w-7 h-7 rounded-full bg-[#F5F5F7] dark:bg-[#2C2C2E] text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white flex items-center justify-center transition-colors cursor-pointer"
              >
                <X size={14} />
              </button>
            </div>

            <p className="text-xs text-[#6E6E73] dark:text-[#A1A1A6] mb-5">
              Select your preferred report format to download:
            </p>

            <div className="space-y-3 mb-6">
              {/* Option 1: PDF */}
              <button
                type="button"
                onClick={() => {
                  exportAssessmentPDF(downloadModalDevice);
                  setDownloadModalDevice(null);
                }}
                className="w-full flex items-center justify-between p-4 rounded-2xl border border-[#E5E5E7] dark:border-[#2C2C2E] hover:border-[#0071E3] dark:hover:border-[#0071E3] hover:bg-blue-50/50 dark:hover:bg-blue-950/20 transition-all text-left group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400 flex items-center justify-center shrink-0">
                    <FileText size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-bold text-[#1D1D1F] dark:text-white group-hover:text-[#0071E3] transition-colors">
                        PDF Document (.pdf)
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300">
                        Recommended
                      </span>
                    </div>
                    <p className="text-[11px] text-[#86868B] mt-0.5">
                      Formatted hardware audit report & circular certificate
                    </p>
                  </div>
                </div>
                <Download size={16} className="text-[#86868B] group-hover:text-[#0071E3] group-hover:translate-y-0.5 transition-all" />
              </button>

              {/* Option 2: Excel */}
              <button
                type="button"
                onClick={() => {
                  exportAssessmentExcel(downloadModalDevice);
                  setDownloadModalDevice(null);
                }}
                className="w-full flex items-center justify-between p-4 rounded-2xl border border-[#E5E5E7] dark:border-[#2C2C2E] hover:border-emerald-500 dark:hover:border-emerald-500 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/20 transition-all text-left group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                    <FileSpreadsheet size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-bold text-[#1D1D1F] dark:text-white group-hover:text-emerald-600 transition-colors">
                        Excel Spreadsheet (.xlsx)
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                        Data Sheet
                      </span>
                    </div>
                    <p className="text-[11px] text-[#86868B] mt-0.5">
                      Structured telemetry, component health matrix & pathways
                    </p>
                  </div>
                </div>
                <Download size={16} className="text-[#86868B] group-hover:text-emerald-600 group-hover:translate-y-0.5 transition-all" />
              </button>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setDownloadModalDevice(null)}
                className="px-4 py-2 rounded-full text-xs font-semibold text-[#6E6E73] dark:text-[#A1A1A6] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E] transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}
