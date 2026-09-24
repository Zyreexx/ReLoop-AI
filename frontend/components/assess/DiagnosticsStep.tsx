"use client";

import React, { useState } from "react";
import { HelpCircle, AlertCircle, Info, ChevronDown, ChevronUp, CheckCircle2 } from "lucide-react";
import { DiagnosticData } from "@/types/assessment";

interface DiagnosticsStepProps {
  confirmedModelName: string;
  manufacturer: string;
  initialData: DiagnosticData;
  onComplete: (data: DiagnosticData) => void;
}

export const DiagnosticsStep: React.FC<DiagnosticsStepProps> = ({
  confirmedModelName,
  manufacturer,
  initialData,
  onComplete,
}) => {
  const [deviceAge, setDeviceAge] = useState<number>(initialData.deviceAgeYears || 4);

  // Battery state
  const [noBatteryInfo, setNoBatteryInfo] = useState<boolean>(
    initialData.battery?.notProvided || false
  );
  const [designCap, setDesignCap] = useState<number>(initialData.battery?.designCapacity || 51000);
  const [fullCap, setFullCap] = useState<number>(initialData.battery?.fullChargeCapacity || 37230);
  const [cycleCount, setCycleCount] = useState<number>(initialData.battery?.cycleCount || 482);
  const [unit, setUnit] = useState<"mWh" | "Wh">(initialData.battery?.unit || "mWh");
  const [showBatteryHelp, setShowBatteryHelp] = useState<boolean>(false);

  // SSD state
  const [noSsdInfo, setNoSsdInfo] = useState<boolean>(initialData.ssd?.notProvided || false);
  const [ssdHealth, setSsdHealth] = useState<number>(initialData.ssd?.healthPercentage || 91);
  const [powerHours, setPowerHours] = useState<number>(initialData.ssd?.powerOnHours || 3420);
  const [smartStatus, setSmartStatus] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.ssd?.smartStatus || "PASS"
  );

  // RAM state
  const [ramCapacity, setRamCapacity] = useState<number>(initialData.ram?.capacityGB || 16);
  const [ramTest, setRamTest] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.ram?.testResult || "PASS"
  );

  // Thermals state
  const [cpuTemp, setCpuTemp] = useState<number>(initialData.thermals?.cpuTempC || 88);
  const [gpuTemp, setGpuTemp] = useState<number>(initialData.thermals?.gpuTempC || 75);
  const [throttling, setThrottling] = useState<"DETECTED" | "NOT_DETECTED" | "UNKNOWN">(
    initialData.thermals?.thermalThrottling || "DETECTED"
  );
  const [overheating, setOverheating] = useState<boolean>(
    initialData.thermals?.overheatingSymptoms || true
  );

  // System diagnostics state
  const [hardwareResult, setHardwareResult] = useState<"PASS" | "FAIL" | "NOT_TESTED">(
    initialData.system?.hardwareResult || "PASS"
  );
  const [criticalFaults, setCriticalFaults] = useState<string>(
    initialData.system?.criticalFaults || "None reported"
  );

  const [validationError, setValidationError] = useState<string | null>(null);

  // Calculate battery health % dynamically
  const calculatedBatteryHealth =
    designCap > 0 ? Math.min(100, Math.round((fullCap / designCap) * 100)) : 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validation rules
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
    };

    onComplete(compiledData);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200 mb-2 inline-block">
          DIAGNOSTIC EVIDENCE
        </span>
        <h2 className="text-3xl font-bold text-[#1D1D1F] tracking-tight">2. Diagnostics</h2>
        <p className="text-[#6E6E73] text-sm sm:text-base mt-1">
          Provide actual device measurements where available.
        </p>
      </div>

      {/* Explanatory Banner */}
      <div className="mb-8 p-4 rounded-xl bg-blue-50/70 border border-blue-200 text-blue-900 text-xs sm:text-sm flex items-start gap-3">
        <Info className="w-5 h-5 text-[#0071E3] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Hardware Measurement Policy:</span>
          Photos can show visible condition, but internal component health requires actual device diagnostics. Values entered here are used to calculate silicon condition.
        </div>
      </div>

      {validationError && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* 7A Device Confirmation */}
        <div className="apple-card p-6 bg-white">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#6E6E73] mb-4">
            Device Information
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-3 rounded-xl bg-[#F5F5F7]">
              <span className="text-[11px] text-[#86868B] block font-medium">Manufacturer</span>
              <span className="text-sm font-bold text-[#1D1D1F]">{manufacturer}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F5F7]">
              <span className="text-[11px] text-[#86868B] block font-medium">Confirmed Model</span>
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

        {/* 7B Battery Section */}
        <div className="apple-card p-6 bg-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold mr-2">
                DIAGNOSTIC
              </span>
              <h3 className="text-lg font-bold text-[#1D1D1F] inline-block">
                Battery Diagnostics
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setShowBatteryHelp(!showBatteryHelp)}
              className="inline-flex items-center gap-1 text-xs text-[#0071E3] font-semibold hover:underline"
            >
              <HelpCircle size={14} />
              <span>How to find this (Windows)</span>
              {showBatteryHelp ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>

          {/* Windows Battery Report Expandable Helper */}
          {showBatteryHelp && (
            <div className="mb-6 p-4 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] text-xs text-[#1D1D1F] leading-relaxed">
              <span className="font-bold block mb-1">Windows Battery Report Guide:</span>
              <ol className="list-decimal pl-4 space-y-1">
                <li>Open Command Prompt or PowerShell.</li>
                <li>Type: <code className="bg-white px-1.5 py-0.5 rounded font-mono text-[11px]">powercfg /batteryreport</code> and press Enter.</li>
                <li>Open the generated HTML report in your browser to view Design Capacity and Full Charge Capacity.</li>
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
              <span>I don&apos;t have this battery information</span>
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
                  <label className="text-xs font-semibold text-[#6E6E73] block mb-1">Capacity Unit</label>
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

              {/* Calculated Output Card */}
              <div className="p-4 rounded-xl bg-[#F5F5F7] border border-[#E5E5E7] flex items-center justify-between">
                <div>
                  <span className="text-xs text-[#86868B] block">Calculated Battery Health</span>
                  <span className="text-2xl font-bold text-[#1D1D1F]">
                    {calculatedBatteryHealth}%
                  </span>
                  <span className="text-[11px] text-[#6E6E73] block">
                    Calculated from device diagnostic data
                  </span>
                </div>
                <span
                  className={`text-xs font-bold px-3 py-1 rounded-full ${
                    calculatedBatteryHealth >= 80
                      ? "bg-emerald-100 text-emerald-800"
                      : calculatedBatteryHealth >= 65
                      ? "bg-amber-100 text-amber-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {calculatedBatteryHealth >= 80
                    ? "Good Condition"
                    : calculatedBatteryHealth >= 65
                    ? "Degraded"
                    : "Service Recommended"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* 7C SSD Section */}
        <div className="apple-card p-6 bg-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold mr-2">
                DIAGNOSTIC
              </span>
              <h3 className="text-lg font-bold text-[#1D1D1F] inline-block">
                SSD & Storage Health
              </h3>
            </div>
          </div>

          <div className="mb-4">
            <label className="inline-flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1D1D1F]">
              <input
                type="checkbox"
                checked={noSsdInfo}
                onChange={(e) => setNoSsdInfo(e.target.checked)}
                className="rounded text-[#0071E3]"
              />
              <span>Not provided / Skip SSD diagnostic</span>
            </label>
          </div>

          {!noSsdInfo && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  Drive Health %
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
                  Power-On Hours (Approx)
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
          )}
        </div>

        {/* 7D RAM & 7E Thermals Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* RAM */}
          <div className="apple-card p-6 bg-white">
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold mr-2">
              DIAGNOSTIC
            </span>
            <h3 className="text-base font-bold text-[#1D1D1F] inline-block mb-4">
              RAM Memory
            </h3>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                  Installed RAM Capacity (GB)
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
                  Memory Test Result
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

          {/* Thermals */}
          <div className="apple-card p-6 bg-white">
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold mr-2">
              DIAGNOSTIC
            </span>
            <h3 className="text-base font-bold text-[#1D1D1F] inline-block mb-4">
              Thermal Measurements
            </h3>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                    CPU Temp (°C)
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
                  <option value="DETECTED">Detected</option>
                  <option value="NOT_DETECTED">Not Detected</option>
                  <option value="UNKNOWN">Unknown</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* 7F System Diagnostics */}
        <div className="apple-card p-6 bg-white">
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold mr-2">
            DIAGNOSTIC
          </span>
          <h3 className="text-lg font-bold text-[#1D1D1F] inline-block mb-4">
            System Hardware Diagnostics
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-[#6E6E73] block mb-1">
                Diagnostic Result
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
                Critical Hardware Faults
              </label>
              <input
                type="text"
                value={criticalFaults}
                onChange={(e) => setCriticalFaults(e.target.value)}
                placeholder="None reported"
                className="w-full p-2.5 rounded-xl border border-[#D2D2D7] text-sm font-semibold text-[#1D1D1F]"
              />
            </div>
          </div>

          <p className="text-xs text-[#86868B] mt-3">
            Note: Standard phrasing used for system report is: &quot;No critical faults detected from available diagnostics&quot;.
          </p>
        </div>

        {/* Submit Step */}
        <div className="flex justify-end pt-4">
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-sm font-semibold transition-all shadow-md cursor-pointer"
          >
            <span>Continue to User Symptoms →</span>
          </button>
        </div>
      </form>
    </div>
  );
};
