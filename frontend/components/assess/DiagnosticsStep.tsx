"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  HelpCircle,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  ArrowLeft,
  Terminal,
  Download,
  Copy,
  Check,
  RefreshCw,
  Cpu,
  HardDrive,
  Battery,
  Flame,
  Monitor,
  Keyboard,
  ShieldCheck,
  Laptop,
  Layers,
  UploadCloud,
  FileCode,
  AlertTriangle,
} from "lucide-react";
import { DiagnosticData } from "@/types/assessment";
import { useLanguage } from "@/context/LanguageContext";
import {
  createDiagnosticSession,
  getDiagnosticSessionStatus,
  submitDiagnosticSession,
  DiagnosticSessionReport,
  SubsystemFinding,
} from "@/lib/api";

interface DiagnosticsStepProps {
  confirmedModelName: string;
  manufacturer: string;
  initialData: DiagnosticData;
  onComplete: (data: DiagnosticData) => void;
  onBack?: () => void;
  productId?: string;
}

export const DiagnosticsStep: React.FC<DiagnosticsStepProps> = ({
  confirmedModelName,
  manufacturer,
  initialData,
  onComplete,
  onBack,
  productId,
}) => {
  const { t } = useLanguage();

  // Mode: "agent" (automated smart diagnostics) or "manual" (manual input form)
  const [mode, setMode] = useState<"agent" | "manual">("agent");

  // Consent & Session State
  const [consentGranted, setConsentGranted] = useState<boolean>(false);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<"PENDING" | "RUNNING" | "COMPLETED" | "FAILED">("PENDING");
  const [subsystemsProgress, setSubsystemsProgress] = useState<Record<string, string>>({});
  const [sessionReport, setSessionReport] = useState<DiagnosticSessionReport | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const [copiedCmd, setCopiedCmd] = useState<boolean>(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  // Client OS detection
  const [detectedOS, setDetectedOS] = useState<"Windows" | "macOS" | "Linux">("Windows");
  useEffect(() => {
    if (typeof window !== "undefined") {
      const ua = navigator.userAgent;
      if (ua.includes("Mac") || ua.includes("Darwin")) setDetectedOS("macOS");
      else if (ua.includes("Linux") || ua.includes("X11")) setDetectedOS("Linux");
      else setDetectedOS("Windows");
    }
  }, []);

  // Manual Form State
  const [deviceAge, setDeviceAge] = useState<number>(initialData.deviceAgeYears || 4);
  const [noBatteryInfo, setNoBatteryInfo] = useState<boolean>(initialData.battery?.notProvided || false);
  const [designCap, setDesignCap] = useState<number>(initialData.battery?.designCapacity || 51000);
  const [fullCap, setFullCap] = useState<number>(initialData.battery?.fullChargeCapacity || 37230);
  const [cycleCount, setCycleCount] = useState<number>(initialData.battery?.cycleCount || 482);
  const [unit, setUnit] = useState<"mWh" | "Wh">(initialData.battery?.unit || "mWh");
  const [showBatteryHelp, setShowBatteryHelp] = useState<boolean>(false);

  const [noSsdInfo, setNoSsdInfo] = useState<boolean>(initialData.ssd?.notProvided || false);
  const [ssdHealth, setSsdHealth] = useState<number>(initialData.ssd?.healthPercentage || 91);
  const [powerHours, setPowerHours] = useState<number>(initialData.ssd?.powerOnHours || 3420);
  const [smartStatus, setSmartStatus] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.ssd?.smartStatus || "PASS"
  );

  const [ramCapacity, setRamCapacity] = useState<number>(initialData.ram?.capacityGB || 16);
  const [ramTest, setRamTest] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.ram?.testResult || "PASS"
  );

  const [cpuTemp, setCpuTemp] = useState<number>(initialData.thermals?.cpuTempC || 88);
  const [gpuTemp, setGpuTemp] = useState<number>(initialData.thermals?.gpuTempC || 75);
  const [throttling, setThrottling] = useState<"DETECTED" | "NOT_DETECTED" | "UNKNOWN">(
    initialData.thermals?.thermalThrottling || "DETECTED"
  );
  const [overheating, setOverheating] = useState<boolean>(initialData.thermals?.overheatingSymptoms || true);

  const [hardwareResult, setHardwareResult] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.system?.hardwareResult || "PASS"
  );
  const [criticalFaults, setCriticalFaults] = useState<string>(
    initialData.system?.criticalFaults || "None reported"
  );

  const [validationError, setValidationError] = useState<string | null>(null);

  const calculatedBatteryHealth =
    designCap > 0 ? Math.min(100, Math.round((fullCap / designCap) * 100)) : 0;

  // Initialize or fetch session on consent
  const handleStartSession = async () => {
    setIsInitializing(true);
    setSessionError(null);
    try {
      const session = await createDiagnosticSession(productId);
      setSessionToken(session.session_token);
      setSessionStatus(session.status);
      setSubsystemsProgress(session.subsystems_progress);
      setConsentGranted(true);
    } catch (err: any) {
      setSessionError(err.message || "Could not initialize diagnostic session.");
    } finally {
      setIsInitializing(false);
    }
  };

  // Live polling for diagnostic progress when session is active and not completed
  useEffect(() => {
    if (!sessionToken || sessionStatus === "COMPLETED" || sessionStatus === "FAILED") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const statusRes = await getDiagnosticSessionStatus(sessionToken);
        setSessionStatus(statusRes.status);
        if (statusRes.subsystems_progress) {
          setSubsystemsProgress(statusRes.subsystems_progress);
        }
        if (statusRes.report) {
          setSessionReport(statusRes.report);
          setSessionStatus("COMPLETED");

          // Sync manual state fields from report findings
          const subs = statusRes.report.subsystems || {};
          if (subs.battery?.evidence) {
            const ev = subs.battery.evidence;
            if (ev.design_capacity_mwh) setDesignCap(Math.round(ev.design_capacity_mwh));
            if (ev.full_charge_capacity_mwh) setFullCap(Math.round(ev.full_charge_capacity_mwh));
            if (ev.cycle_count !== undefined) setCycleCount(ev.cycle_count);
          }
          if (subs.ssd?.evidence) {
            const ev = subs.ssd.evidence;
            if (ev.health_percentage !== undefined) setSsdHealth(Math.round(ev.health_percentage));
            if (ev.smart_status) setSmartStatus(ev.smart_status === "PASS" ? "PASS" : "FAIL");
          }
          if (subs.ram?.evidence) {
            const ev = subs.ram.evidence;
            if (ev.installed_gb) setRamCapacity(ev.installed_gb);
            if (ev.test_result) setRamTest(ev.test_result === "PASS" ? "PASS" : "FAIL");
          }
          if (subs.thermals?.evidence) {
            const ev = subs.thermals.evidence;
            if (ev.max_temp_c) setCpuTemp(Math.round(ev.max_temp_c));
            if (ev.throttling_detected !== undefined) {
              setThrottling(ev.throttling_detected ? "DETECTED" : "NOT_DETECTED");
            }
          }
          if (subs.system?.evidence) {
            const ev = subs.system.evidence;
            setHardwareResult(ev.post_successful ? "PASS" : "FAIL");
            if (subs.system.faults && subs.system.faults.length > 0) {
              setCriticalFaults(subs.system.faults.join("; "));
            }
          }
        }
      } catch (err) {
        console.warn("[ReLoop] Diagnostics status poll error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionToken, sessionStatus]);

  // Command to run based on OS
  const agentRunCommand =
    detectedOS === "Windows"
      ? `python reloop_agent.py --token ${sessionToken || "<TOKEN>"}`
      : `python3 reloop_agent.py --token ${sessionToken || "<TOKEN>"}`;

  const handleCopyCommand = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(agentRunCommand);
      setCopiedCmd(true);
      setTimeout(() => setCopiedCmd(false), 2500);
    }
  };

  // Handle direct JSON upload if user ran agent with --json-output
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !sessionToken) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = JSON.parse(text);
        const report = await submitDiagnosticSession(sessionToken, parsed);
        setSessionReport(report);
        setSessionStatus("COMPLETED");
      } catch (err: any) {
        setSessionError(`JSON upload failed: ${err.message}`);
      }
    };
    reader.readAsText(file);
  };

  // Submit and proceed to Step 3
  const handleCompleteDiagnostics = () => {
    const compiledData: DiagnosticData = {
      deviceAgeYears: deviceAge,
      battery: {
        designCapacity: designCap,
        fullChargeCapacity: fullCap,
        cycleCount,
        unit,
        healthPercentage: calculatedBatteryHealth,
        notProvided: noBatteryInfo,
      },
      ssd: {
        healthPercentage: ssdHealth,
        powerOnHours: powerHours,
        smartStatus,
        notProvided: noSsdInfo,
      },
      ram: {
        capacityGB: ramCapacity,
        testResult: ramTest,
      },
      thermals: {
        cpuTempC: cpuTemp,
        gpuTempC: gpuTemp,
        thermalThrottling: throttling,
        overheatingSymptoms: overheating,
      },
      system: {
        hardwareResult,
        criticalFaults,
      },
      sessionToken: sessionToken || undefined,
      agentReport: sessionReport || undefined,
    };

    onComplete(compiledData);
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!noBatteryInfo) {
      if (fullCap > designCap) {
        setValidationError("Full Charge Capacity cannot exceed Design Capacity.");
        return;
      }
      if (designCap <= 0 || fullCap < 0 || cycleCount < 0) {
        setValidationError("Please enter valid positive numbers for battery measurements.");
        return;
      }
    }

    handleCompleteDiagnostics();
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200 mb-2 inline-block">
            {t("diag.badge", "Step 2 of 4 • Smart Diagnostics")}
          </span>
          <h2 className="text-3xl font-bold text-[#1D1D1F] tracking-tight">
            {t("diag.title", "Internal Hardware Diagnostics")}
          </h2>
          <p className="text-[#6E6E73] text-sm sm:text-base mt-1">
            {t(
              "diag.subtitle",
              "Evaluate internal hardware wear, detect anomalies, and calculate circular repair/upgrade potential."
            )}
          </p>
        </div>

        {/* Mode Switch Pill */}
        <div className="inline-flex p-1 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setMode("agent")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              mode === "agent"
                ? "bg-white text-[#1D1D1F] shadow-xs"
                : "text-[#6E6E73] hover:text-[#1D1D1F]"
            }`}
          >
            ⚡ {t("diag.smartAgentTab", "Smart Agent (Automated)")}
          </button>
          <button
            type="button"
            onClick={() => setMode("manual")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              mode === "manual"
                ? "bg-white text-[#1D1D1F] shadow-xs"
                : "text-[#6E6E73] hover:text-[#1D1D1F]"
            }`}
          >
            ✍️ {t("diag.manualTab", "Manual Entry")}
          </button>
        </div>
      </div>

      {sessionError && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{sessionError}</span>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────────── */}
      {/* MODE 1: SMART AGENT DIAGNOSTICS                                          */}
      {/* ───────────────────────────────────────────────────────────────────────── */}
      {mode === "agent" && (
        <div className="space-y-6">
          {/* Substage 1: Explicit Consent & Scope */}
          {!consentGranted ? (
            <div className="apple-card p-6 sm:p-8 bg-white border border-[#E5E5E7] space-y-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center shrink-0 text-[#0071E3]">
                  <ShieldCheck size={28} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[#1D1D1F] tracking-tight">
                    Cross-Platform Hardware Evaluation
                  </h3>
                  <p className="text-sm text-[#6E6E73] mt-1 leading-relaxed">
                    Browser security models cannot access low-level hardware sensors directly.
                    ReLoop uses a lightweight, read-only local diagnostic script to evaluate all 8
                    internal subsystems with zero external dependencies.
                  </p>
                </div>
              </div>

              {/* Scope Breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Battery size={14} className="text-[#0071E3]" />
                    <span>Battery Health & Cycles</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Measures full charge vs design capacity (mWh) and cycle counts to detect degradation.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <HardDrive size={14} className="text-[#0071E3]" />
                    <span>Storage (SSD/NVMe) SMART</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Non-destructive read-only check of SMART failure predictions and drive health.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Layers size={14} className="text-[#0071E3]" />
                    <span>RAM & Memory Integrity</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Verifies installed SO-DIMM capacity and scans OS hardware error logs (WHEA / EDAC).
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Flame size={14} className="text-[#0071E3]" />
                    <span>Thermals & Throttling</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Checks ACPI thermal zones and detects active firmware CPU thermal throttling events.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Cpu size={14} className="text-[#0071E3]" />
                    <span>Processor & System Board</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Queries CPU cores, UEFI POST sequence status, and motherboard power rail stability.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Monitor size={14} className="text-[#0071E3]" />
                    <span>Display, Keyboard & Chassis</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Checks display driver, keyboard controller status, and prompts visual hinge checks.
                  </p>
                </div>
              </div>

              {/* Security Safeguards */}
              <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 text-emerald-900 text-xs flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold block">Zero Privacy Risk & Read-Only Guarantee:</span>
                  <p className="text-emerald-800">
                    The agent never touches personal documents, browser history, or credentials. It executes
                    standard OS hardware queries with zero software installations or system modifications.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setMode("manual")}
                  className="text-xs font-semibold text-[#6E6E73] hover:text-[#1D1D1F] transition-colors cursor-pointer"
                >
                  I prefer to type specifications manually →
                </button>

                <button
                  type="button"
                  onClick={handleStartSession}
                  disabled={isInitializing}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer disabled:opacity-50"
                >
                  {isInitializing ? (
                    <>
                      <RefreshCw size={15} className="animate-spin" />
                      <span>Initializing Session...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck size={16} />
                      <span>Allow & Start Smart Diagnostics</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : sessionStatus !== "COMPLETED" ? (
            /* Substage 2: Active Session & Runner Instructions */
            <div className="space-y-6">
              {/* Instructions Card */}
              <div className="apple-card p-6 bg-white border border-[#E5E5E7] space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                    <h3 className="text-base font-bold text-[#1D1D1F]">
                      Diagnostic Session Active
                    </h3>
                  </div>
                  <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-[#F5F5F7] text-[#6E6E73]">
                    Token: {sessionToken}
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-[#6E6E73] leading-relaxed">
                  Run the diagnostic utility in your terminal to collect telemetry for your{" "}
                  <strong className="text-[#1D1D1F]">
                    {manufacturer} {confirmedModelName}
                  </strong>
                  . The findings will appear here automatically.
                </p>

                {/* Step-by-step Execution Box */}
                <div className="p-4 rounded-xl bg-[#1D1D1F] text-white space-y-3 font-mono text-xs">
                  <div className="flex items-center justify-between text-[#86868B] pb-1 border-b border-white/10">
                    <div className="flex items-center gap-1.5">
                      <Terminal size={13} />
                      <span>Detected OS: {detectedOS}</span>
                    </div>
                    <span className="text-[10px]">Zero Dependencies Required</span>
                  </div>

                  <div className="space-y-1.5">
                    <span className="text-[#86868B] text-[11px] block">
                      # 1. Download the agent (or run from existing repository):
                    </span>
                    <a
                      href="/backend-api/diagnostics/agent/download"
                      download="reloop_agent.py"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-sans font-semibold transition-colors"
                    >
                      <Download size={13} />
                      <span>Download reloop_agent.py</span>
                    </a>
                  </div>

                  <div className="space-y-1 pt-1">
                    <span className="text-[#86868B] text-[11px] block">
                      # 2. Run in terminal:
                    </span>
                    <div className="flex items-center justify-between bg-black/40 p-2.5 rounded-lg border border-white/10">
                      <code className="text-emerald-400 select-all">{agentRunCommand}</code>
                      <button
                        type="button"
                        onClick={handleCopyCommand}
                        className="ml-2 inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-[11px] text-white transition-colors cursor-pointer shrink-0"
                      >
                        {copiedCmd ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                        <span>{copiedCmd ? "Copied" : "Copy"}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* File Upload Option */}
                <div className="flex items-center justify-between text-xs text-[#6E6E73] pt-2">
                  <span>Ran diagnostics offline?</span>
                  <label className="inline-flex items-center gap-1 text-[#0071E3] font-semibold hover:underline cursor-pointer">
                    <UploadCloud size={14} />
                    <span>Upload report.json file</span>
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>

              {/* Live Subsystems Progress Indicator */}
              <div className="apple-card p-6 bg-white border border-[#E5E5E7]">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#6E6E73]">
                    Live Telemetry Collector Status
                  </h4>
                  <div className="flex items-center gap-1.5 text-xs text-[#0071E3]">
                    <RefreshCw size={12} className="animate-spin" />
                    <span>Listening for agent stream...</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { key: "battery", name: "Battery Subsystem", icon: Battery },
                    { key: "ssd", name: "Storage (SSD/NVMe)", icon: HardDrive },
                    { key: "ram", name: "Memory (RAM)", icon: Layers },
                    { key: "thermals", name: "Thermals & Fans", icon: Flame },
                    { key: "cpu", name: "CPU Architecture", icon: Cpu },
                    { key: "display", name: "Display Panel", icon: Monitor },
                    { key: "keyboard", name: "Keyboard Controller", icon: Keyboard },
                    { key: "system", name: "System Board & POST", icon: ShieldCheck },
                  ].map(({ key, name, icon: Icon }) => {
                    const status = subsystemsProgress[key] || "Pending";
                    const isPassed = status === "Passed";
                    const isFault = status === "Fault Detected";
                    const isRunning = status === "Running";

                    return (
                      <div
                        key={key}
                        className={`p-3 rounded-xl border transition-all ${
                          isPassed
                            ? "bg-emerald-50/50 border-emerald-200"
                            : isFault
                            ? "bg-amber-50/50 border-amber-200"
                            : isRunning
                            ? "bg-blue-50/50 border-blue-200"
                            : "bg-[#F5F5F7] border-[#E5E5E7]/60"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 mb-1.5">
                          <Icon
                            size={14}
                            className={
                              isPassed
                                ? "text-emerald-600"
                                : isFault
                                ? "text-amber-600"
                                : isRunning
                                ? "text-[#0071E3]"
                                : "text-[#86868B]"
                            }
                          />
                          <span className="text-[11px] font-semibold text-[#1D1D1F] truncate">
                            {name}
                          </span>
                        </div>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full inline-block ${
                            isPassed
                              ? "bg-emerald-100 text-emerald-800"
                              : isFault
                              ? "bg-amber-100 text-amber-800"
                              : isRunning
                              ? "bg-blue-100 text-blue-800"
                              : "bg-[#E5E5E7] text-[#6E6E73]"
                          }`}
                        >
                          {status}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Substage 3: Comprehensive Findings & 8 Subsystem Cards */
            <div className="space-y-6">
              {/* Overall Summary Card */}
              <div className="apple-card p-6 bg-white border border-[#E5E5E7]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-4 border-b border-[#E5E5E7]">
                  <div>
                    <span className="text-xs text-[#86868B] block">Hardware Condition Profile</span>
                    <h3 className="text-2xl font-bold text-[#1D1D1F]">
                      Overall Status:{" "}
                      <span
                        className={
                          sessionReport?.overall_hardware_health === "GOOD"
                            ? "text-emerald-600"
                            : sessionReport?.overall_hardware_health === "FAIR"
                            ? "text-amber-600"
                            : "text-red-600"
                        }
                      >
                        {sessionReport?.overall_hardware_health || "FAIR"}
                      </span>
                    </h3>
                  </div>

                  <span
                    className={`text-xs font-bold px-3 py-1.5 rounded-full self-start ${
                      sessionReport?.faults && sessionReport.faults.length > 0
                        ? "bg-amber-100 text-amber-800 border border-amber-200"
                        : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    }`}
                  >
                    {sessionReport?.faults?.length || 0} Anomaly/Wear Indicator(s) Detected
                  </span>
                </div>

                {/* Plain-Language Grounded Explanation */}
                {sessionReport?.ai_explanation && (
                  <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 text-xs sm:text-sm text-blue-900 leading-relaxed whitespace-pre-line mb-4">
                    <span className="font-bold block mb-1">Telemetry-Grounded Circular Assessment:</span>
                    {sessionReport.ai_explanation}
                  </div>
                )}

                {/* Physical Inspection Notice */}
                <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Physical Guardrail Notice:</span> Battery swelling,
                    chassis drop dents, and physical keyboard switch travel cannot be verified by
                    telemetry alone and are validated in the next step.
                  </div>
                </div>
              </div>

              {/* 8 Subsystems Detailed Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {sessionReport?.subsystems &&
                  Object.entries(sessionReport.subsystems).map(([key, sub]) => {
                    const compStatus = sub.component_status || "GOOD";
                    const isHealthy = compStatus === "GOOD";
                    const isWear = compStatus === "WEAR";
                    const isReplace = compStatus === "REPLACE";

                    return (
                      <div
                        key={key}
                        className="apple-card p-5 bg-white border border-[#E5E5E7] flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-bold uppercase tracking-wider text-[#6E6E73]">
                              {key.toUpperCase()}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                isHealthy
                                  ? "bg-emerald-100 text-emerald-800"
                                  : isWear
                                  ? "bg-amber-100 text-amber-800"
                                  : isReplace
                                  ? "bg-red-100 text-red-800"
                                  : "bg-gray-100 text-gray-800"
                              }`}
                            >
                              {compStatus}
                            </span>
                          </div>

                          {/* Faults if any */}
                          {sub.faults && sub.faults.length > 0 && (
                            <div className="mb-2 space-y-1">
                              {sub.faults.map((f, i) => (
                                <span
                                  key={i}
                                  className="text-[11px] text-red-600 font-semibold block leading-tight"
                                >
                                  ⚠️ {f}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Observations */}
                          {sub.observations && sub.observations.length > 0 && (
                            <ul className="text-xs text-[#6E6E73] space-y-1 mb-3">
                              {sub.observations.map((obs, idx) => (
                                <li key={idx}>• {obs}</li>
                              ))}
                            </ul>
                          )}
                        </div>

                        {/* Evidence Source Footer */}
                        <div className="pt-2 border-t border-[#F5F5F7] flex items-center justify-between text-[10px] text-[#86868B]">
                          <span className="truncate">{sub.source}</span>
                          <span className="font-mono font-semibold">
                            Severity: {sub.fault_severity || "INFO"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
              </div>

              {/* Continue Button */}
              <div className="flex items-center justify-between pt-4">
                {onBack ? (
                  <button
                    type="button"
                    onClick={onBack}
                    className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full border border-[#D2D2D7] bg-white hover:bg-[#F5F5F7] text-[#1D1D1F] text-sm font-semibold transition-all shadow-xs cursor-pointer"
                  >
                    <ArrowLeft size={16} />
                    <span>Back</span>
                  </button>
                ) : <div />}

                <button
                  type="button"
                  onClick={handleCompleteDiagnostics}
                  className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer ml-auto"
                >
                  <span>Continue to Symptoms →</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────────────────── */}
      {/* MODE 2: MANUAL ENTRY FORM                                                 */}
      {/* ───────────────────────────────────────────────────────────────────────── */}
      {mode === "manual" && (
        <form onSubmit={handleManualSubmit} className="space-y-8">
          {validationError && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          {/* Device Confirmation */}
          <div className="apple-card p-6 bg-white">
            <h3 className="text-sm font-bold uppercase tracking-wider text-[#6E6E73] mb-4">
              {t("diag.deviceInfo", "Device Confirmation")}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3 rounded-xl bg-[#F5F5F7]">
                <span className="text-[11px] text-[#86868B] block font-medium">Manufacturer</span>
                <span className="text-sm font-bold text-[#1D1D1F]">{manufacturer}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#F5F5F7]">
                <span className="text-[11px] text-[#86868B] block font-medium">Model</span>
                <span className="text-sm font-bold text-[#1D1D1F]">{confirmedModelName}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#F5F5F7]">
                <label className="text-[11px] text-[#86868B] block font-medium mb-1">
                  Estimated Age (Years)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="15"
                  value={deviceAge}
                  onChange={(e) => setDeviceAge(parseFloat(e.target.value) || 0)}
                  className="w-full text-sm font-bold text-[#1D1D1F] bg-white border border-[#D2D2D7] rounded-lg px-2 py-1"
                />
              </div>
            </div>
          </div>

          {/* Battery Section */}
          <div className="apple-card p-6 bg-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold mr-2">
                  TELEMETRY
                </span>
                <h3 className="text-lg font-bold text-[#1D1D1F] inline-block">
                  Battery Subsystem
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowBatteryHelp(!showBatteryHelp)}
                className="inline-flex items-center gap-1 text-xs text-[#0071E3] font-semibold hover:underline cursor-pointer"
              >
                <HelpCircle size={14} />
                <span>How to get report</span>
                {showBatteryHelp ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>

            {showBatteryHelp && (
              <div className="mb-6 p-4 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] text-xs text-[#1D1D1F] leading-relaxed">
                <span className="font-bold block mb-1">Generating Battery Report:</span>
                <ol className="list-decimal pl-4 space-y-1">
                  <li>Windows: Open CMD and run <code>powercfg /batteryreport</code></li>
                  <li>macOS: Option-click the Apple menu → System Information → Power</li>
                  <li>Linux: Check <code>upower -i /org/freedesktop/UPower/devices/battery_BAT0</code></li>
                </ol>
              </div>
            )}

            <div className="mb-4">
              <label className="inline-flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1D1D1F]">
                <input
                  type="checkbox"
                  checked={noBatteryInfo}
                  onChange={(e) => setNoBatteryInfo(e.target.checked)}
                  className="rounded text-[#0071E3]"
                />
                <span>Battery telemetry not available</span>
              </label>
            </div>

            {!noBatteryInfo && (
              <div>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
                  <div>
                    <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                      Design Capacity ({unit})
                    </label>
                    <input
                      type="number"
                      value={designCap}
                      onChange={(e) => setDesignCap(parseInt(e.target.value) || 0)}
                      className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                      Full Charge Capacity ({unit})
                    </label>
                    <input
                      type="number"
                      value={fullCap}
                      onChange={(e) => setFullCap(parseInt(e.target.value) || 0)}
                      className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                      Cycle Count
                    </label>
                    <input
                      type="number"
                      value={cycleCount}
                      onChange={(e) => setCycleCount(parseInt(e.target.value) || 0)}
                      className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#6E6E73] block mb-1">Unit</label>
                    <select
                      value={unit}
                      onChange={(e) => setUnit(e.target.value as "mWh" | "Wh")}
                      className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F] bg-white"
                    >
                      <option value="mWh">mWh</option>
                      <option value="Wh">Wh</option>
                    </select>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] flex items-center justify-between">
                  <div>
                    <span className="text-xs text-[#86868B] block">Calculated Battery Health</span>
                    <span className="text-2xl font-bold text-[#1D1D1F]">
                      {calculatedBatteryHealth}%
                    </span>
                  </div>
                  <span
                    className={`text-xs font-bold px-3 py-1 rounded-full ${
                      calculatedBatteryHealth >= 80
                        ? "bg-emerald-100 text-emerald-800"
                        : calculatedBatteryHealth >= 50
                        ? "bg-amber-100 text-amber-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {calculatedBatteryHealth >= 80
                      ? "Healthy"
                      : calculatedBatteryHealth >= 50
                      ? "Service Recommended"
                      : "Replace Required"}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* SSD Section */}
          <div className="apple-card p-6 bg-white">
            <h3 className="text-lg font-bold text-[#1D1D1F] mb-4">
              Storage Subsystem (SSD/NVMe)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  SMART Health (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={ssdHealth}
                  onChange={(e) => setSsdHealth(parseInt(e.target.value) || 0)}
                  className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  Power On Hours
                </label>
                <input
                  type="number"
                  value={powerHours}
                  onChange={(e) => setPowerHours(parseInt(e.target.value) || 0)}
                  className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  SMART Status
                </label>
                <select
                  value={smartStatus}
                  onChange={(e) => setSmartStatus(e.target.value as any)}
                  className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F] bg-white"
                >
                  <option value="PASS">PASS</option>
                  <option value="FAIL">FAIL</option>
                  <option value="NOT_TESTED">NOT TESTED</option>
                </select>
              </div>
            </div>
          </div>

          {/* RAM & Thermals Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="apple-card p-6 bg-white">
              <h3 className="text-base font-bold text-[#1D1D1F] mb-4">System Memory (RAM)</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                    Installed Capacity
                  </label>
                  <select
                    value={ramCapacity}
                    onChange={(e) => setRamCapacity(parseInt(e.target.value))}
                    className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F] bg-white"
                  >
                    <option value={4}>4 GB</option>
                    <option value={8}>8 GB</option>
                    <option value={16}>16 GB</option>
                    <option value={32}>32 GB</option>
                    <option value={64}>64 GB</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                    Memory Diagnostic Result
                  </label>
                  <select
                    value={ramTest}
                    onChange={(e) => setRamTest(e.target.value as any)}
                    className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F] bg-white"
                  >
                    <option value="PASS">PASS</option>
                    <option value="FAIL">FAIL</option>
                    <option value="NOT_TESTED">NOT TESTED</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="apple-card p-6 bg-white">
              <h3 className="text-base font-bold text-[#1D1D1F] mb-4">Thermal Subsystem</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                      CPU Max Temp (°C)
                    </label>
                    <input
                      type="number"
                      value={cpuTemp}
                      onChange={(e) => setCpuTemp(parseInt(e.target.value) || 0)}
                      className="w-full p-2 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                      GPU Temp (°C)
                    </label>
                    <input
                      type="number"
                      value={gpuTemp}
                      onChange={(e) => setGpuTemp(parseInt(e.target.value) || 0)}
                      className="w-full p-2 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                    Thermal Throttling
                  </label>
                  <select
                    value={throttling}
                    onChange={(e) => setThrottling(e.target.value as any)}
                    className="w-full p-2 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F] bg-white"
                  >
                    <option value="DETECTED">DETECTED</option>
                    <option value="NOT_DETECTED">NOT DETECTED</option>
                    <option value="UNKNOWN">UNKNOWN</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* System Diagnostics */}
          <div className="apple-card p-6 bg-white">
            <h3 className="text-base font-bold text-[#1D1D1F] mb-4">System Board / Motherboard</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  POST / Power Rails Result
                </label>
                <select
                  value={hardwareResult}
                  onChange={(e) => setHardwareResult(e.target.value as any)}
                  className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F] bg-white"
                >
                  <option value="PASS">PASS</option>
                  <option value="FAIL">FAIL</option>
                  <option value="NOT_TESTED">NOT TESTED</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  Reported Critical Faults
                </label>
                <input
                  type="text"
                  value={criticalFaults}
                  onChange={(e) => setCriticalFaults(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4">
            {onBack ? (
              <button
                type="button"
                onClick={onBack}
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full border border-[#D2D2D7] bg-white hover:bg-[#F5F5F7] text-[#1D1D1F] text-sm font-semibold transition-all shadow-xs cursor-pointer"
              >
                <ArrowLeft size={16} />
                <span>Back</span>
              </button>
            ) : <div />}

            <button
              type="submit"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer ml-auto"
            >
              <span>Continue to Symptoms →</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
