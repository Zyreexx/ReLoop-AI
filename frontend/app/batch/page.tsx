"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Download,
  Layers,
  Leaf,
  DollarSign,
  Laptop,
  ArrowRight,
  Loader2,
  Trash2,
  Play,
  XCircle,
} from "lucide-react";

const SAMPLE_CSV = `manufacturer,model,model_year,category,serial_number,battery_health_pct,ssd_health_pct
Apple,MacBook Pro 14 (M1 Pro),2021,LAPTOP,C02G10X0MD6R,82.5,96.0
Dell,Latitude 5420,2021,LAPTOP,8HJ39B3,71.0,88.0
Lenovo,ThinkPad T14 Gen 2,2021,LAPTOP,PF234XYZ,89.0,94.0
HP,EliteBook 840 G8,2021,LAPTOP,5CD1234567,64.0,91.0
Apple,iPhone 13,2021,SMARTPHONE,F17G890123,78.0,99.0
Dell,OptiPlex 7090 Tower,2021,DESKTOP,7XK9921,100.0,95.0
Dell,PowerEdge R640,2019,SERVER,SRV88290,100.0,92.0
Apple,iPad Air 4,2020,TABLET,DMPD890123,83.0,97.0`;

export default function BatchInventoryPage() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [file, setFile] = useState<File | null>(null);
  const [csvPreview, setCsvPreview] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      const reader = new FileReader();
      reader.onload = (event) => {
        setCsvPreview(event.target?.result as string || "");
      };
      reader.readAsText(selected);
    }
  };

  const handleLoadSample = () => {
    const blob = new Blob([SAMPLE_CSV], { type: "text/csv" });
    const sampleFile = new File([blob], "enterprise_fleet_sample.csv", { type: "text/csv" });
    setFile(sampleFile);
    setCsvPreview(SAMPLE_CSV);
    setErrorMsg(null);
  };

  const handleStartBatch = async () => {
    if (!file && !csvPreview) {
      setErrorMsg("Please select a CSV file or load the sample fleet.");
      return;
    }
    setLoading(true);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      if (file) {
        formData.append("file", file);
      } else {
        const blob = new Blob([csvPreview], { type: "text/csv" });
        formData.append("file", blob, "batch_inventory.csv");
      }

      const res = await fetch("/api/batch/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || "Failed to start batch assessment job");
      }

      const data = await res.json();
      setJobId(data.job_id);
    } catch (err: any) {
      setErrorMsg(err.message || "Network error submitting batch job");
      setLoading(false);
    }
  };

  // Poll for job progress
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/batch/${jobId}/status`);
        if (res.ok) {
          const status = await res.json();
          setJobStatus(status);

          if (status.status === "COMPLETED" || status.status === "FAILED" || status.status === "CANCELLED") {
            clearInterval(interval);
            setLoading(false);

            // Fetch summary
            const sumRes = await fetch(`/api/batch/${jobId}/summary`);
            if (sumRes.ok) {
              const sumData = await sumRes.json();
              setSummary(sumData);
            }
          }
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="min-h-screen bg-[#F5F5F7] dark:bg-[#000000] text-[#1D1D1F] dark:text-[#F5F5F7] flex flex-col font-sans transition-colors duration-300">
      <Navbar onOpenAuth={handleOpenAuth} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0071E3]/10 text-[#0071E3] dark:text-[#2997FF] text-xs font-semibold uppercase tracking-wider mb-2">
              <Layers className="w-3.5 h-3.5" />
              Enterprise Edition
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#1D1D1F] dark:text-white">
              Fleet Inventory Assessment
            </h1>
            <p className="mt-2 text-base text-[#86868B] max-w-2xl">
              Upload CSV or JSON inventory to batch-evaluate hundreds of enterprise devices, compute deterministic circular pathways, and aggregate CO2 and cost savings.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleLoadSample}
              className="px-4 py-2 text-xs font-medium rounded-xl border border-[#D2D2D7] dark:border-[#3A3A3C] hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
            >
              Load Sample Fleet (8 items)
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-2xl bg-[#FF3B30]/10 border border-[#FF3B30]/20 text-[#FF3B30] text-sm flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Upload & Progress Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* File Upload Dropzone */}
          <div className="lg:col-span-1 bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] shadow-xs flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#1D1D1F] dark:text-white mb-2">
                1. Upload Inventory File
              </h2>
              <p className="text-xs text-[#86868B] mb-4">
                Supported columns: manufacturer, model, model_year, category, serial_number, battery_health_pct.
              </p>

              <label className="border-2 border-dashed border-[#D2D2D7] dark:border-[#3A3A3C] rounded-2xl p-6 flex flex-col items-center justify-center gap-2 hover:border-[#0071E3] transition-colors cursor-pointer">
                <UploadCloud className="w-8 h-8 text-[#0071E3]" />
                <span className="text-sm font-medium text-[#1D1D1F] dark:text-white">
                  {file ? file.name : "Choose CSV or drop file here"}
                </span>
                <span className="text-xs text-[#86868B]">CSV up to 50MB</span>
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>

            <div className="mt-6 pt-4 border-t border-[#E5E5EA] dark:border-[#2C2C2E] flex items-center justify-between">
              <span className="text-xs text-[#86868B]">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : "No file loaded"}
              </span>
              <button
                disabled={loading || (!file && !csvPreview)}
                onClick={handleStartBatch}
                className={`px-5 py-2.5 rounded-full text-xs font-semibold text-white flex items-center gap-2 transition-all cursor-pointer ${
                  loading || (!file && !csvPreview)
                    ? "bg-[#86868B]/40 cursor-not-allowed"
                    : "bg-[#0071E3] hover:bg-[#0077ED] shadow-sm"
                }`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Start Assessment
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Job Telemetry & Progress */}
          <div className="lg:col-span-2 bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[#1D1D1F] dark:text-white">
                  2. Assessment Pipeline Execution
                </h2>
                {jobStatus && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      jobStatus.status === "COMPLETED"
                        ? "bg-[#34C759]/15 text-[#34C759]"
                        : jobStatus.status === "RUNNING"
                        ? "bg-[#0071E3]/15 text-[#0071E3] animate-pulse"
                        : "bg-[#FF9500]/15 text-[#FF9500]"
                    }`}
                  >
                    {jobStatus.status}
                  </span>
                )}
              </div>

              {jobStatus ? (
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-xs font-medium text-[#86868B] mb-1.5">
                      <span>Overall Progress</span>
                      <span>
                        {jobStatus.processed_devices} / {jobStatus.total_devices} devices (
                        {jobStatus.progress_percentage?.toFixed(0) || 0}%)
                      </span>
                    </div>
                    <div className="w-full bg-[#E5E5EA] dark:bg-[#2C2C2E] h-2.5 rounded-full overflow-hidden">
                      <div
                        className="bg-[#0071E3] h-full transition-all duration-300"
                        style={{ width: `${jobStatus.progress_percentage || 0}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 pt-2">
                    <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                      <div className="text-xs text-[#86868B]">Valid Items</div>
                      <div className="text-xl font-bold text-[#1D1D1F] dark:text-white">
                        {jobStatus.total_devices}
                      </div>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                      <div className="text-xs text-[#86868B]">Duplicates Ignored</div>
                      <div className="text-xl font-bold text-[#FF9500]">
                        {jobStatus.duplicate_devices}
                      </div>
                    </div>
                    <div className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/50">
                      <div className="text-xs text-[#86868B]">Completed</div>
                      <div className="text-xl font-bold text-[#34C759]">
                        {jobStatus.processed_devices}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 flex flex-col items-center justify-center text-center text-[#86868B]">
                  <RotateCcw className="w-8 h-8 mb-2 opacity-40" />
                  <p className="text-sm">No batch job active. Click "Start Assessment" or load the sample fleet.</p>
                </div>
              )}
            </div>

            {summary && (
              <div className="mt-6 pt-4 border-t border-[#E5E5EA] dark:border-[#2C2C2E] flex flex-wrap items-center justify-between gap-3">
                <span className="text-xs text-[#34C759] font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Fleet Assessment Ready
                </span>
                <div className="flex items-center gap-2">
                  <a
                    href={`/api/batch/${jobId}/export/csv`}
                    className="px-3.5 py-1.5 rounded-full border border-[#D2D2D7] dark:border-[#3A3A3C] text-xs font-semibold text-[#1D1D1F] dark:text-white hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export CSV
                  </a>
                  <a
                    href={`/api/batch/${jobId}/export/excel`}
                    className="px-3.5 py-1.5 rounded-full bg-[#34C759] hover:bg-[#2eb34f] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    Export Excel (.xlsx)
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Fleet Analytics Summary Cards */}
        {summary && (
          <div className="mb-10">
            <h2 className="text-xl font-bold text-[#1D1D1F] dark:text-white mb-4">
              Fleet Aggregates & Circular Pathways
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <div className="bg-white dark:bg-[#1C1C1E] p-5 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <div className="flex items-center justify-between text-xs text-[#86868B] mb-1">
                  <span>Total Assessed</span>
                  <Laptop className="w-4 h-4 text-[#0071E3]" />
                </div>
                <div className="text-2xl font-bold text-[#1D1D1F] dark:text-white">
                  {summary.total_devices}
                </div>
                <div className="text-xs text-[#86868B] mt-1">Multi-category fleet</div>
              </div>

              <div className="bg-white dark:bg-[#1C1C1E] p-5 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <div className="flex items-center justify-between text-xs text-[#86868B] mb-1">
                  <span>Avoided CO2</span>
                  <Leaf className="w-4 h-4 text-[#34C759]" />
                </div>
                <div className="text-2xl font-bold text-[#34C759]">
                  {summary.total_co2_avoided_kg.toFixed(0)} <span className="text-sm font-normal text-[#86868B]">kg</span>
                </div>
                <div className="text-xs text-[#86868B] mt-1">Embodied carbon conserved</div>
              </div>

              <div className="bg-white dark:bg-[#1C1C1E] p-5 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <div className="flex items-center justify-between text-xs text-[#86868B] mb-1">
                  <span>E-Waste Diverted</span>
                  <Layers className="w-4 h-4 text-[#FF9500]" />
                </div>
                <div className="text-2xl font-bold text-[#FF9500]">
                  {summary.total_ewaste_diverted_kg.toFixed(1)} <span className="text-sm font-normal text-[#86868B]">kg</span>
                </div>
                <div className="text-xs text-[#86868B] mt-1">Kept out of landfills</div>
              </div>

              <div className="bg-white dark:bg-[#1C1C1E] p-5 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
                <div className="flex items-center justify-between text-xs text-[#86868B] mb-1">
                  <span>Estimated Cost</span>
                  <DollarSign className="w-4 h-4 text-[#0071E3]" />
                </div>
                <div className="text-2xl font-bold text-[#1D1D1F] dark:text-white">
                  ₹{summary.total_estimated_cost_inr.toLocaleString()}
                </div>
                <div className="text-xs text-[#86868B] mt-1">Total circular intervention</div>
              </div>
            </div>

            {/* Pathways Distribution */}
            <div className="bg-white dark:bg-[#1C1C1E] p-6 rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E]">
              <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-white mb-3">
                Deterministic Recommendation Distribution
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
                {Object.entries(summary.pathway_counts || {}).map(([pathway, count]: any) => (
                  <div key={pathway} className="p-3 rounded-2xl bg-[#F5F5F7] dark:bg-[#2C2C2E]/60 text-center">
                    <div className="text-xs font-semibold text-[#0071E3] dark:text-[#2997FF]">{pathway}</div>
                    <div className="text-xl font-bold text-[#1D1D1F] dark:text-white mt-1">{count}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Device Records Table */}
        {summary && summary.devices && summary.devices.length > 0 && (
          <div className="bg-white dark:bg-[#1C1C1E] rounded-3xl border border-[#D2D2D7]/60 dark:border-[#2C2C2E] overflow-hidden">
            <div className="p-5 border-b border-[#E5E5EA] dark:border-[#2C2C2E] flex justify-between items-center">
              <h3 className="text-base font-bold text-[#1D1D1F] dark:text-white">
                Individual Device Evaluations ({summary.devices.length})
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#F5F5F7] dark:bg-[#2C2C2E]/50 text-[#86868B] uppercase font-semibold">
                  <tr>
                    <th className="py-3 px-4">Serial / ID</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Model</th>
                    <th className="py-3 px-4">Health</th>
                    <th className="py-3 px-4">Recommended Pathway</th>
                    <th className="py-3 px-4">Est. Cost</th>
                    <th className="py-3 px-4">CO2 Avoided</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E5EA] dark:divide-[#2C2C2E]">
                  {summary.devices.map((d: any, idx: number) => (
                    <tr key={idx} className="hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium">{d.serial_number || d.device_id?.slice(0, 10)}</td>
                      <td className="py-3 px-4 uppercase">{d.category || "LAPTOP"}</td>
                      <td className="py-3 px-4 font-medium text-[#1D1D1F] dark:text-white">
                        {d.manufacturer} {d.model}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-semibold">{d.overall_hardware_health || "UNKNOWN"}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#0071E3]/10 text-[#0071E3] dark:text-[#2997FF] font-semibold text-[11px]">
                          {d.primary_pathway || "N/A"}
                        </span>
                      </td>
                      <td className="py-3 px-4">₹{(d.estimated_cost_inr || 0).toLocaleString()}</td>
                      <td className="py-3 px-4 text-[#34C759] font-medium">{d.co2_avoided_kg?.toFixed(1) || 0} kg</td>
                      <td className="py-3 px-4">
                        <span className="text-[#34C759] font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {d.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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

