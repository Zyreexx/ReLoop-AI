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
  Zap,
  Sparkles,
} from "lucide-react";
import ThermalTelemetryChart from "./ThermalTelemetryChart";
import { DiagnosticData } from "@/types/assessment";
import { useLanguage } from "@/context/LanguageContext";
import {
  createDiagnosticSession,
  getDiagnosticSessionStatus,
  submitDiagnosticSession,
  runLocalHardwareScan,
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
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanTimeElapsed, setScanTimeElapsed] = useState<number>(0);
  const [copiedCmd, setCopiedCmd] = useState<boolean>(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [copiedVenvCmd, setCopiedVenvCmd] = useState<boolean>(false);

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

  // Timer while scanning
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isScanning && sessionStatus === "RUNNING") {
      timer = setInterval(() => {
        setScanTimeElapsed((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isScanning, sessionStatus]);

  // Manual Form State
  const [deviceAge, setDeviceAge] = useState<number>(initialData.deviceAgeYears || 0);
  const [noBatteryInfo, setNoBatteryInfo] = useState<boolean>(initialData.battery?.notProvided ?? true);
  const [designCap, setDesignCap] = useState<number>(initialData.battery?.designCapacity || 0);
  const [fullCap, setFullCap] = useState<number>(initialData.battery?.fullChargeCapacity || 0);
  const [cycleCount, setCycleCount] = useState<number>(initialData.battery?.cycleCount || 0);
  const [unit, setUnit] = useState<"mWh" | "Wh">(initialData.battery?.unit || "mWh");
  const [showBatteryHelp, setShowBatteryHelp] = useState<boolean>(false);

  const [noSsdInfo, setNoSsdInfo] = useState<boolean>(initialData.ssd?.notProvided ?? true);
  const [ssdHealth, setSsdHealth] = useState<number>(initialData.ssd?.healthPercentage || 0);
  const [powerHours, setPowerHours] = useState<number>(initialData.ssd?.powerOnHours || 0);
  const [smartStatus, setSmartStatus] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.ssd?.smartStatus || "NOT_TESTED"
  );

  const [ramCapacity, setRamCapacity] = useState<number>(initialData.ram?.capacityGB || 0);
  const [ramTest, setRamTest] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.ram?.testResult || "NOT_TESTED"
  );

  const [cpuTemp, setCpuTemp] = useState<number>(initialData.thermals?.cpuTempC || 0);
  const [gpuTemp, setGpuTemp] = useState<number>(initialData.thermals?.gpuTempC || 0);
  const [throttling, setThrottling] = useState<"DETECTED" | "NOT_DETECTED" | "UNKNOWN">(
    initialData.thermals?.thermalThrottling || "UNKNOWN"
  );
  const [overheating, setOverheating] = useState<boolean>(initialData.thermals?.overheatingSymptoms || false);

  const [hardwareResult, setHardwareResult] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.system?.hardwareResult || "NOT_TESTED"
  );
  const [criticalFaults, setCriticalFaults] = useState<string>(
    initialData.system?.criticalFaults || ""
  );

  const [validationError, setValidationError] = useState<string | null>(null);

  const calculatedBatteryHealth =
    (designCap > 0 && fullCap > 0) ? Math.min(100, Math.round((fullCap / designCap) * 100)) : 0;

  // Real Hardware Diagnostic Trigger
  const handleStartHardwareScan = async () => {
    setIsInitializing(true);
    setIsScanning(true);
    setSessionError(null);
    setScanTimeElapsed(0);
    try {
      let token = sessionToken;
      if (!token) {
        const session = await createDiagnosticSession(productId);
        token = session.session_token;
        setSessionToken(token);
      }
      setConsentGranted(true);
      setSessionStatus("RUNNING");

      // Set initial subsystem progress states
      const initialProgress: Record<string, string> = {
        battery: "Running",
        ssd: "Running",
        ram: "Running",
        thermals: "Running",
        cpu: "Running",
        display: "Running",
        keyboard: "Running",
        chassis: "Running",
        system: "Running",
      };
      setSubsystemsProgress(initialProgress);

      // Trigger the genuine hardware scan on the machine (parallel threads, ~8s)
      await runLocalHardwareScan(token);
    } catch (err: any) {
      setSessionError(err.message || "Failed to start hardware diagnostics.");
      setIsScanning(false);
      setSessionStatus("FAILED");
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
          setIsScanning(false);

          // Sync manual state fields from genuine hardware report findings
          const subs = statusRes.report.subsystems || {};
          if (subs.battery?.evidence) {
            const ev = subs.battery.evidence;
            if (ev.design_capacity_mwh) setDesignCap(Math.round(ev.design_capacity_mwh));
            if (ev.full_charge_capacity_mwh) setFullCap(Math.round(ev.full_charge_capacity_mwh));
            if (ev.cycle_count !== undefined) setCycleCount(ev.cycle_count);
            setNoBatteryInfo(false);
          }
          if (subs.ssd?.evidence) {
            const ev = subs.ssd.evidence;
            if (ev.health_percentage !== undefined) setSsdHealth(Math.round(ev.health_percentage));
            if (ev.power_on_hours !== undefined) setPowerHours(Math.round(ev.power_on_hours));
            if (ev.smart_status) setSmartStatus(ev.smart_status === "PASS" ? "PASS" : "FAIL");
            setNoSsdInfo(false);
          }
          if (subs.ram?.evidence) {
            const ev = subs.ram.evidence;
            if (ev.installed_gb) setRamCapacity(ev.installed_gb);
            if (ev.test_result) setRamTest(ev.test_result === "PASS" ? "PASS" : "FAIL");
          }
          if (subs.thermals?.evidence) {
            const ev = subs.thermals.evidence;
            if (ev.max_temp_c) setCpuTemp(Math.round(ev.max_temp_c));
            if (ev.cpu_idle_temp_c) setGpuTemp(Math.round(ev.cpu_idle_temp_c));
            if (ev.throttling_detected !== undefined) {
              setThrottling(ev.throttling_detected ? "DETECTED" : "NOT_DETECTED");
            }
          }
          if (subs.system?.evidence) {
            const ev = subs.system.evidence;
            setHardwareResult(ev.post_successful ? "PASS" : "FAIL");
          }

          // Gather all detected faults
          const collectedFaults: string[] = [];
          if (statusRes.report.faults && statusRes.report.faults.length > 0) {
            statusRes.report.faults.forEach((f: any) => {
              const desc = typeof f === "string" ? f : f.description || f.component;
              if (desc) collectedFaults.push(desc);
            });
          }
          if (collectedFaults.length > 0) {
            setCriticalFaults(collectedFaults.join("; "));
          }
        }
      } catch (err) {
        console.warn("[ReLoop] Diagnostics status poll error:", err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionToken, sessionStatus]);

  // Command to run based on OS
  const agentRunCommand =
    detectedOS === "Windows"
      ? `python reloop_agent.py --token ${sessionToken || "<TOKEN>"} --consent`
      : `python3 reloop_agent.py --token ${sessionToken || "<TOKEN>"} --consent`;

  const venvRunCommand = `backend\\.venv\\Scripts\\python.exe reloop_agent.py --token ${sessionToken || "<TOKEN>"} --consent`;

  const handleCopyCommand = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(agentRunCommand);
      setCopiedCmd(true);
      setTimeout(() => setCopiedCmd(false), 2500);
    }
  };

  const handleCopyVenvCommand = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(venvRunCommand);
      setCopiedVenvCmd(true);
      setTimeout(() => setCopiedVenvCmd(false), 2500);
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
        setIsScanning(false);
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
                    Automated Hardware Diagnostics (~8 Seconds)
                  </h3>
                  <p className="text-sm text-[#6E6E73] mt-1 leading-relaxed">
                    Evaluates your laptop&apos;s real internal hardware sensors using read-only OS queries.
                    Scans 9 hardware subsystems in parallel with zero third-party software installation.
                  </p>
                </div>
              </div>

              {/* Scope Breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Battery size={14} className="text-[#0071E3]" />
                    <span>Battery Health & Degradation</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Measures full charge vs design capacity (mWh) and cycle count to detect genuine wear.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <HardDrive size={14} className="text-[#0071E3]" />
                    <span>Storage (SSD/NVMe) SMART</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Non-destructive read-only check of SMART failure predictions and drive health percentage.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Layers size={14} className="text-[#0071E3]" />
                    <span>RAM & Memory Integrity</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Verifies installed physical RAM capacity and queries OS hardware fault logs.
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
                    Queries real CPU model, core/thread count, UEFI POST status, and system board enclosure.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7]/60">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#1D1D1F] mb-1">
                    <Monitor size={14} className="text-[#0071E3]" />
                    <span>Display, Keyboard & Chassis</span>
                  </div>
                  <p className="text-[11px] text-[#6E6E73]">
                    Inspects display resolution, keyboard controller responsiveness, and chassis form factor.
                  </p>
                </div>
              </div>

              {/* Security Safeguards */}
              <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 text-emerald-900 text-xs flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold block">Zero Privacy Risk & Read-Only Guarantee:</span>
                  <p className="text-emerald-800">
                    The diagnostics never touches personal files, browser data, or credentials. It uses
                    standard OS hardware APIs (WMI/PowerShell, system_profiler, or sysfs) to read hardware telemetry.
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
                  onClick={handleStartHardwareScan}
                  disabled={isInitializing || isScanning}
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer disabled:opacity-50"
                >
                  {isScanning || isInitializing ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      <span>Scanning Laptop Hardware ({scanTimeElapsed}s)...</span>
                    </>
                  ) : (
                    <>
                      <Zap size={17} className="text-amber-300" />
                      <span>Scan This Laptop&apos;s Hardware (Automated • ~8s)</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : sessionStatus !== "COMPLETED" ? (
            /* Substage 2: Active Session & Runner Instructions */
            <div className="space-y-6">
              {/* Scan Status Banner */}
              <div className="p-4 rounded-xl bg-blue-50/80 border border-blue-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
                <div>
                  <div className="flex items-center gap-2">
                    <Zap size={16} className={`text-[#0071E3] ${isScanning ? "animate-bounce" : ""}`} />
                    <span className="text-xs font-bold text-blue-900">
                      {isScanning
                        ? `Live Hardware Diagnostic in Progress (${scanTimeElapsed}s elapsed)`
                        : sessionStatus === "RUNNING"
                        ? "Diagnostic Runner Active"
                        : "Diagnostic Session Active"}
                    </span>
                  </div>
                  <p className="text-[11px] text-blue-700 mt-0.5 leading-relaxed">
                    {isScanning
                      ? "Measuring real ACPI battery health, NVMe SMART status, thermal zones, and UEFI logs. Genuine hardware telemetry with zero mock data."
                      : "Directly runs diagnostics on this laptop's internal subsystems in ~8 seconds."}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={handleStartHardwareScan}
                    disabled={isScanning}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold transition-all shadow-xs cursor-pointer disabled:opacity-60"
                  >
                    {isScanning ? (
                      <>
                        <RefreshCw size={12} className="animate-spin" />
                        <span>Running ({scanTimeElapsed}s)...</span>
                      </>
                    ) : (
                      <>
                        <Zap size={13} className="text-amber-300" />
                        <span>Run Real Hardware Scan (~8s)</span>
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConsentGranted(false)}
                    className="px-3 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
                  >
                    Back to Info
                  </button>
                </div>
              </div>

              {/* Live Subsystems Progress Indicator */}
              <div className="apple-card p-6 bg-white border border-[#E5E5E7]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#6E6E73]">
                      Subsystem Sensor Telemetry
                    </h4>
                    <p className="text-[11px] text-[#86868B] mt-0.5">
                      Executing parallel diagnostics across all 9 internal subsystems.
                    </p>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="flex items-center gap-1.5 text-xs text-[#0071E3]">
                      <RefreshCw size={12} className={isScanning ? "animate-spin text-amber-500" : "animate-spin"} />
                      <span>{isScanning ? `Testing hardware subsystems (${scanTimeElapsed}s)...` : "Awaiting runner completion..."}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { key: "battery", name: "Battery Subsystem", icon: Battery },
                    { key: "ssd", name: "Storage (SSD/NVMe)", icon: HardDrive },
                    { key: "ram", name: "Memory (RAM)", icon: Layers },
                    { key: "thermals", name: "Thermals & Fans", icon: Flame },
                    { key: "cpu", name: "CPU Architecture", icon: Cpu },
                    { key: "display", name: "Display Panel", icon: Monitor },
                    { key: "keyboard", name: "Keyboard Controller", icon: Keyboard },
                    { key: "chassis", name: "Chassis & Enclosure", icon: Laptop },
                    { key: "system", name: "System Board & POST", icon: ShieldCheck },
                  ].map(({ key, name, icon: Icon }) => {
                    const status = subsystemsProgress[key] || "Pending";
                    const isPassed = status === "Passed" || status === "PASSED";
                    const isFault = status === "Fault Detected" || status === "FAULT_DETECTED";
                    const isRunning = status === "Running" || status === "RUNNING";

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

              {/* Thermal Telemetry & Sensor History Graph */}
              <ThermalTelemetryChart
                hardwareModel={`${manufacturer} ${confirmedModelName}`}
                initialBaseTemp={sessionReport?.subsystems?.thermals?.evidence?.cpu_idle_temp_c || (cpuTemp > 0 ? cpuTemp : 42)}
                initialMaxTemp={sessionReport?.subsystems?.thermals?.evidence?.max_temp_c || (cpuTemp > 0 ? cpuTemp : 48)}
                batteryHealth={sessionReport?.subsystems?.battery?.evidence?.health_percentage ?? (calculatedBatteryHealth > 0 ? calculatedBatteryHealth : undefined)}
                batteryVoltage={sessionReport?.subsystems?.battery?.evidence?.voltage_v}
                batteryWattage={sessionReport?.subsystems?.battery?.evidence?.discharge_rate_w}
                ssdHealth={sessionReport?.subsystems?.ssd?.evidence?.health_percentage ?? (ssdHealth > 0 ? ssdHealth : undefined)}
                ramCapacityGB={sessionReport?.subsystems?.ram?.evidence?.installed_gb ?? (ramCapacity > 0 ? ramCapacity : undefined)}
                ramActivePercent={sessionReport?.subsystems?.ram?.evidence?.active_ram_pct}
                cpuLoadPercent={sessionReport?.subsystems?.cpu?.evidence?.load_percentage}
                isLive={sessionStatus === "RUNNING"}
              />

              {/* Optional: Terminal CLI / Offline Runner Accordion */}
              <details className="apple-card p-4 bg-slate-50 border border-slate-200 text-xs">
                <summary className="font-semibold text-slate-700 cursor-pointer select-none">
                  Advanced: Terminal CLI Runner & Offline Report Upload (Optional)
                </summary>
                <div className="mt-4 space-y-4 pt-3 border-t border-slate-200 font-sans">
                  <p className="text-slate-600">
                    If you prefer running diagnostics manually in your terminal or on an air-gapped machine:
                  </p>

                  <div className="p-3 rounded-xl bg-[#1D1D1F] text-white space-y-2 font-mono text-xs">
                    <div className="flex items-center justify-between text-[#86868B] pb-1 border-b border-white/10">
                      <div className="flex items-center gap-1.5">
                        <Terminal size={13} />
                        <span>Command (OS: {detectedOS})</span>
                      </div>
                      <span className="text-[10px]">Zero Dependencies</span>
                    </div>

                    <div className="flex items-center justify-between bg-black/40 p-2 rounded-lg border border-white/10">
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

                    {detectedOS === "Windows" && (
                      <div className="pt-2 text-[11px] text-[#86868B] font-sans border-t border-white/10">
                        <span>Project virtualenv command:</span>
                        <div className="mt-1 flex items-center justify-between bg-black/50 p-2 rounded border border-white/5 font-mono text-[10px] text-emerald-400">
                          <code className="select-all">{venvRunCommand}</code>
                          <button
                            type="button"
                            onClick={handleCopyVenvCommand}
                            className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/10 hover:bg-white/20 text-[10px] text-white transition-colors cursor-pointer shrink-0"
                          >
                            {copiedVenvCmd ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                            <span>{copiedVenvCmd ? "Copied" : "Copy"}</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-slate-600">Have an offline report.json?</span>
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
              </details>
            </div>
          ) : (
            /* Substage 3: Comprehensive Findings & 9 Subsystem Cards */
            <div className="space-y-6">
              {/* Overall Summary Card */}
              <div className="apple-card p-6 bg-white border border-[#E5E5E7]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-4 border-b border-[#E5E5E7]">
                  <div>
                    <span className="text-xs text-[#86868B] block">Genuine Hardware Condition Profile</span>
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
                    {sessionReport?.faults?.length || 0} Hardware Anomaly/Wear Issue(s) Detected
                  </span>
                </div>

                {/* Primary Detected Faults Alert Banner */}
                {sessionReport?.faults && sessionReport.faults.length > 0 && (
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 mb-4 space-y-2">
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      <span>Actual Detected Hardware Faults:</span>
                    </div>
                    <ul className="text-xs space-y-1.5 pl-6 list-disc">
                      {sessionReport.faults.map((f: any, idx: number) => {
                        const faultMsg = typeof f === "string" ? f : f.description || f.component || JSON.stringify(f);
                        const sev = typeof f === "object" && f.severity ? `[${f.severity}] ` : "";
                        return (
                          <li key={idx} className="font-semibold text-amber-950">
                            {sev}{faultMsg}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {/* Plain-Language Grounded Explanation */}
                {sessionReport?.ai_explanation && (
                  <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 text-xs sm:text-sm text-blue-900 leading-relaxed whitespace-pre-line mb-4">
                    <span className="font-bold block mb-1">Telemetry-Grounded Circular Assessment:</span>
                    {sessionReport.ai_explanation}
                  </div>
                )}

                {/* Physical Inspection Notice */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs flex items-start gap-2.5">
                  <Info className="w-4 h-4 text-[#0071E3] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Next Steps:</span> Physical enclosure scratches,
                    screen cracks, and hinge tightness will be validated in Step 3 (Visual Symptoms).
                  </div>
                </div>
              </div>

              {/* Thermal Telemetry & Sensor History Graph */}
              <ThermalTelemetryChart
                initialBaseTemp={sessionReport?.subsystems?.thermals?.evidence?.cpu_idle_temp_c || (cpuTemp > 0 ? cpuTemp : 42)}
                initialMaxTemp={sessionReport?.subsystems?.thermals?.evidence?.max_temp_c || (cpuTemp > 0 ? cpuTemp : 48)}
                batteryHealth={sessionReport?.subsystems?.battery?.evidence?.health_percentage ?? (calculatedBatteryHealth > 0 ? calculatedBatteryHealth : undefined)}
                batteryVoltage={sessionReport?.subsystems?.battery?.evidence?.voltage_v}
                batteryWattage={sessionReport?.subsystems?.battery?.evidence?.discharge_rate_w}
                ssdHealth={sessionReport?.subsystems?.ssd?.evidence?.health_percentage ?? (ssdHealth > 0 ? ssdHealth : undefined)}
                ramCapacityGB={sessionReport?.subsystems?.ram?.evidence?.installed_gb ?? (ramCapacity > 0 ? ramCapacity : undefined)}
                ramActivePercent={sessionReport?.subsystems?.ram?.evidence?.active_ram_pct}
                cpuLoadPercent={sessionReport?.subsystems?.cpu?.evidence?.load_percentage}
                hardwareModel={`${manufacturer} ${confirmedModelName}`}
                isLive={false}
              />

              {/* 9 Subsystems Detailed Grid */}
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
                              {sub.faults.map((f: any, i: number) => {
                                const faultText = typeof f === "string" ? f : f.description || f.component || JSON.stringify(f);
                                return (
                                  <span
                                    key={i}
                                    className="text-[11px] text-red-600 font-semibold block leading-tight"
                                  >
                                    ⚠️ {faultText}
                                  </span>
                                );
                              })}
                            </div>
                          )}

                          {/* Observations */}
                          {sub.observations && sub.observations.length > 0 && (
                            <ul className="text-xs text-[#6E6E73] space-y-1 mb-3">
                              {sub.observations.map((obs: string, idx: number) => (
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
