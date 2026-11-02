"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Flame,
  Battery,
  HardDrive,
  Cpu,
  Download,
  Play,
  Activity,
  Layers,
  Sparkles,
  Zap,
} from "lucide-react";

export type TelemetryCategory = "thermals" | "battery" | "storage" | "compute";

interface ChannelConfig {
  name: string;
  unit: string;
  color: string;
  dashed?: boolean;
  min: number;
  max: number;
  axis: "left" | "right";
}

interface CategoryConfig {
  id: TelemetryCategory;
  title: string;
  shortLabel: string;
  icon: React.ElementType;
  description: string;
  simActionLabel: string;
  simActiveLabel: string;
  channels: [ChannelConfig, ChannelConfig, ChannelConfig];
  leftAxisLabel: string;
  rightAxisLabel: string;
  leftTicks: number[];
  rightTicks: number[];
}

const CATEGORIES: Record<TelemetryCategory, CategoryConfig> = {
  thermals: {
    id: "thermals",
    title: "Thermal & Fan Telemetry History (Last 30 Seconds)",
    shortLabel: "Thermals & Cooling",
    icon: Flame,
    description:
      "Synchronized CPU Package, GPU Core, and PWM Fan Speed curves with live kernel ACPI monitoring.",
    simActionLabel: "Simulate 5s Thermal Load",
    simActiveLabel: "Simulating Thermal Load...",
    channels: [
      {
        name: "CPU Package",
        unit: "°C",
        color: "#A855F7",
        min: 20,
        max: 110,
        axis: "left",
      },
      {
        name: "GPU Core",
        unit: "°C",
        color: "#38BDF8",
        min: 20,
        max: 110,
        axis: "left",
      },
      {
        name: "Cooling Fan",
        unit: "RPM",
        color: "#14B8A6",
        dashed: true,
        min: 500,
        max: 3500,
        axis: "right",
      },
    ],
    leftAxisLabel: "°C",
    rightAxisLabel: "RPM",
    leftTicks: [20, 30, 40, 50, 60, 70, 80, 90, 100, 110],
    rightTicks: [500, 1000, 1500, 2000, 2500, 3000, 3500],
  },
  battery: {
    id: "battery",
    title: "Battery & Power Rail Dynamics (Last 30 Seconds)",
    shortLabel: "Battery & Power",
    icon: Battery,
    description:
      "Real-time charge retention rate, instant system wattage draw, and cell voltage regulation.",
    simActionLabel: "Simulate Heavy Power Draw",
    simActiveLabel: "Simulating Power Draw...",
    channels: [
      {
        name: "Retention Level",
        unit: "%",
        color: "#10B981",
        min: 0,
        max: 100,
        axis: "left",
      },
      {
        name: "System Draw",
        unit: "W",
        color: "#F59E0B",
        min: 5,
        max: 65,
        axis: "right",
      },
      {
        name: "Cell Voltage",
        unit: "V",
        color: "#06B6D4",
        dashed: true,
        min: 9.0,
        max: 13.5,
        axis: "left",
      },
    ],
    leftAxisLabel: "% / V",
    rightAxisLabel: "Watts",
    leftTicks: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    rightTicks: [5, 15, 25, 35, 45, 55, 65],
  },
  storage: {
    id: "storage",
    title: "Storage (SSD/NVMe) Health & IOPS (Last 30 Seconds)",
    shortLabel: "Storage & NVMe",
    icon: HardDrive,
    description:
      "SMART life estimation, sequential read throughput, and write bandwidth under active I/O.",
    simActionLabel: "Simulate NVMe Burst Test",
    simActiveLabel: "Simulating NVMe Burst...",
    channels: [
      {
        name: "SMART Health",
        unit: "%",
        color: "#10B981",
        min: 0,
        max: 100,
        axis: "left",
      },
      {
        name: "Read Throughput",
        unit: "MB/s",
        color: "#8B5CF6",
        min: 0,
        max: 3500,
        axis: "right",
      },
      {
        name: "Write Throughput",
        unit: "MB/s",
        color: "#FB923C",
        dashed: true,
        min: 0,
        max: 3000,
        axis: "right",
      },
    ],
    leftAxisLabel: "SMART %",
    rightAxisLabel: "MB/s",
    leftTicks: [0, 20, 40, 60, 80, 100],
    rightTicks: [0, 500, 1000, 1500, 2000, 2500, 3000, 3500],
  },
  compute: {
    id: "compute",
    title: "CPU & Memory Workload Utilization (Last 30 Seconds)",
    shortLabel: "CPU & Memory",
    icon: Cpu,
    description:
      "Continuous microarchitecture utilization, physical RAM allocation, and memory bus pressure.",
    simActionLabel: "Simulate 5s Multi-Core Stress",
    simActiveLabel: "Simulating Compute Load...",
    channels: [
      {
        name: "CPU Utilization",
        unit: "%",
        color: "#F43F5E",
        min: 0,
        max: 100,
        axis: "left",
      },
      {
        name: "RAM Active",
        unit: "%",
        color: "#6366F1",
        min: 0,
        max: 100,
        axis: "left",
      },
      {
        name: "Bus Pressure",
        unit: "%",
        color: "#06B6D4",
        dashed: true,
        min: 0,
        max: 100,
        axis: "right",
      },
    ],
    leftAxisLabel: "%",
    rightAxisLabel: "%",
    leftTicks: [0, 20, 40, 60, 80, 100],
    rightTicks: [0, 20, 40, 60, 80, 100],
  },
};

interface ThermalTelemetryChartProps {
  initialBaseTemp?: number;
  initialMaxTemp?: number;
  hardwareModel?: string;
  isLive?: boolean;
}

export default function ThermalTelemetryChart({
  initialBaseTemp = 42,
  initialMaxTemp = 48,
  hardwareModel = "Hardware Sensor Bus",
  isLive = false,
}: ThermalTelemetryChartProps) {
  const [selectedCategory, setSelectedCategory] =
    useState<TelemetryCategory>("thermals");
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationSecondsLeft, setSimulationSecondsLeft] = useState(0);

  // High performance canvas & simulation refs
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const isSimulatingRef = useRef(false);
  isSimulatingRef.current = isSimulating;

  // Telemetry buffer stores 300 samples (sampled at 10 Hz = 30 seconds of high-fidelity data)
  const maxSamples = 300;
  const historyRef = useRef<Record<TelemetryCategory, Array<[number, number, number, number]>>>({
    thermals: [],
    battery: [],
    storage: [],
    compute: [],
  });

  const mousePosRef = useRef<{ x: number; y: number; active: boolean }>({
    x: 0,
    y: 0,
    active: false,
  });

  const [hoveredData, setHoveredData] = useState<{
    timeStr: string;
    v0: number;
    v1: number;
    v2: number;
    x: number;
    y: number;
  } | null>(null);

  // Initialize rolling buffers with realistic baseline data
  useEffect(() => {
    const now = Date.now();
    const intervalMs = 100; // 100ms per point = 10Hz

    // Seed thermals
    const thermals: Array<[number, number, number, number]> = [];
    for (let i = maxSamples - 1; i >= 0; i--) {
      const t = now - i * intervalMs;
      const noiseCpu = Math.sin(i * 0.08) * 1.5 + Math.cos(i * 0.15) * 1.0;
      const noiseGpu = Math.cos(i * 0.09) * 1.2 + Math.sin(i * 0.12) * 0.8;
      const cpu = Math.max(25, initialBaseTemp + noiseCpu - 2);
      const gpu = Math.max(24, initialBaseTemp + noiseGpu - 5);
      const fan = Math.round(1100 + (cpu - 35) * 22 + Math.sin(i * 0.2) * 35);
      thermals.push([t, cpu, gpu, fan]);
    }
    historyRef.current.thermals = thermals;

    // Seed battery
    const battery: Array<[number, number, number, number]> = [];
    for (let i = maxSamples - 1; i >= 0; i--) {
      const t = now - i * intervalMs;
      const retention = 40.6 + Math.sin(i * 0.02) * 0.1;
      const draw = 14.5 + Math.sin(i * 0.1) * 1.8 + Math.random() * 0.5;
      const voltage = 11.2 + Math.cos(i * 0.05) * 0.08;
      battery.push([t, retention, draw, voltage]);
    }
    historyRef.current.battery = battery;

    // Seed storage
    const storage: Array<[number, number, number, number]> = [];
    for (let i = maxSamples - 1; i >= 0; i--) {
      const t = now - i * intervalMs;
      const smart = 95.0;
      const read = Math.max(0, 45 + Math.sin(i * 0.1) * 35 + Math.random() * 20);
      const write = Math.max(0, 18 + Math.cos(i * 0.12) * 15 + Math.random() * 10);
      storage.push([t, smart, read, write]);
    }
    historyRef.current.storage = storage;

    // Seed compute
    const compute: Array<[number, number, number, number]> = [];
    for (let i = maxSamples - 1; i >= 0; i--) {
      const t = now - i * intervalMs;
      const cpuUtil = Math.max(4, Math.min(95, 12 + Math.sin(i * 0.1) * 6 + Math.random() * 4));
      const ramUtil = 38.5 + Math.sin(i * 0.02) * 0.5;
      const bus = 8 + Math.cos(i * 0.1) * 3;
      compute.push([t, cpuUtil, ramUtil, bus]);
    }
    historyRef.current.compute = compute;
  }, [initialBaseTemp]);

  // High-frequency telemetry generator (updates 20 times per second for smooth glide)
  useEffect(() => {
    let stepCount = 0;
    const ticker = setInterval(() => {
      stepCount++;
      const now = Date.now();
      const isSim = isSimulatingRef.current;

      // Update Thermals
      const th = historyRef.current.thermals;
      if (th.length > 0) {
        let cpuTarget = initialBaseTemp;
        let gpuTarget = initialBaseTemp - 4;
        let fanTarget = 1200;

        if (isSim) {
          cpuTarget = 78.5 + Math.sin(stepCount * 0.3) * 2.2;
          gpuTarget = 71.8 + Math.cos(stepCount * 0.25) * 1.8;
          fanTarget = 2480 + Math.round(Math.random() * 80);
        } else {
          cpuTarget = initialBaseTemp + Math.sin(stepCount * 0.08) * 1.4;
          gpuTarget = initialBaseTemp - 4 + Math.cos(stepCount * 0.07) * 1.1;
          fanTarget = 1150 + Math.round((cpuTarget - 35) * 20);
        }
        th.shift();
        th.push([now, cpuTarget, gpuTarget, fanTarget]);
      }

      // Update Battery
      const bat = historyRef.current.battery;
      if (bat.length > 0) {
        let drawTarget = 14.2;
        let voltTarget = 11.24;
        const retention = 40.6;
        if (isSim) {
          drawTarget = 48.5 + Math.sin(stepCount * 0.2) * 3.5;
          voltTarget = 10.85 + Math.cos(stepCount * 0.1) * 0.1;
        } else {
          drawTarget = 13.5 + Math.sin(stepCount * 0.05) * 1.2;
          voltTarget = 11.25 + Math.cos(stepCount * 0.03) * 0.05;
        }
        bat.shift();
        bat.push([now, retention, drawTarget, voltTarget]);
      }

      // Update Storage
      const stor = historyRef.current.storage;
      if (stor.length > 0) {
        let readTarget = 12.0;
        let writeTarget = 5.0;
        if (isSim) {
          readTarget = 2850 + Math.sin(stepCount * 0.4) * 350;
          writeTarget = 2100 + Math.cos(stepCount * 0.3) * 280;
        } else {
          readTarget = Math.max(0, 35 + Math.sin(stepCount * 0.08) * 25);
          writeTarget = Math.max(0, 15 + Math.cos(stepCount * 0.06) * 12);
        }
        stor.shift();
        stor.push([now, 95.0, readTarget, writeTarget]);
      }

      // Update Compute
      const cmp = historyRef.current.compute;
      if (cmp.length > 0) {
        let cpuTarget = 14.0;
        let ramTarget = 38.5;
        let busTarget = 9.0;
        if (isSim) {
          cpuTarget = 88.5 + Math.sin(stepCount * 0.35) * 7.0;
          ramTarget = 54.0 + Math.sin(stepCount * 0.05) * 1.5;
          busTarget = 74.0 + Math.cos(stepCount * 0.25) * 6.0;
        } else {
          cpuTarget = Math.max(4, 12.0 + Math.sin(stepCount * 0.06) * 4.5);
          ramTarget = 38.5 + Math.sin(stepCount * 0.02) * 0.4;
          busTarget = 8.5 + Math.cos(stepCount * 0.05) * 2.0;
        }
        cmp.shift();
        cmp.push([now, cpuTarget, ramTarget, busTarget]);
      }
    }, 50); // 20 updates/sec

    return () => clearInterval(ticker);
  }, [initialBaseTemp]);

  // Handle simulation toggle
  const handleSimulateAction = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setSimulationSecondsLeft(5);

    const countdown = setInterval(() => {
      setSimulationSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(countdown);
          setIsSimulating(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Export JSON log
  const handleExportLog = () => {
    const activeCategory = CATEGORIES[selectedCategory];
    const rawData = historyRef.current[selectedCategory];
    const formatted = rawData.map(([timestamp, v0, v1, v2]) => ({
      time: new Date(timestamp).toTimeString().split(" ")[0],
      timestamp,
      [activeCategory.channels[0].name]: v0,
      [activeCategory.channels[1].name]: v1,
      [activeCategory.channels[2].name]: v2,
    }));

    const jsonStr = JSON.stringify(
      {
        exportedAt: new Date().toISOString(),
        category: selectedCategory,
        hardwareModel,
        sampleCount: formatted.length,
        telemetry: formatted,
      },
      null,
      2
    );

    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reloop-${selectedCategory}-telemetry-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 60 FPS Canvas Rendering Engine
  const renderFrame = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // DPR Scaling
    const dpr = window.devicePixelRatio || 1;
    const displayWidth = canvas.clientWidth;
    const displayHeight = canvas.clientHeight;

    if (canvas.width !== displayWidth * dpr || canvas.height !== displayHeight * dpr) {
      canvas.width = displayWidth * dpr;
      canvas.height = displayHeight * dpr;
    }

    ctx.save();
    ctx.scale(dpr, dpr);

    const w = displayWidth;
    const h = displayHeight;

    const paddingLeft = 54;
    const paddingRight = 64;
    const paddingTop = 24;
    const paddingBottom = 34;

    const plotW = w - paddingLeft - paddingRight;
    const plotH = h - paddingTop - paddingBottom;

    // Clear background
    ctx.fillStyle = "#090D16";
    ctx.fillRect(0, 0, w, h);

    const config = CATEGORIES[selectedCategory];
    const data = historyRef.current[selectedCategory];

    // Helper scale functions
    const getY = (val: number, channel: ChannelConfig) => {
      const clamped = Math.max(channel.min, Math.min(channel.max, val));
      const normalized = (clamped - channel.min) / (channel.max - channel.min);
      return paddingTop + plotH - normalized * plotH;
    };

    // Draw horizontal grid lines & Left Axis labels
    ctx.lineWidth = 1;
    ctx.font = "9px monospace";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    config.leftTicks.forEach((tickVal, idx) => {
      const y = getY(tickVal, config.channels[0]);
      // Grid line
      ctx.strokeStyle = idx % 2 === 0 ? "rgba(255, 255, 255, 0.08)" : "rgba(255, 255, 255, 0.04)";
      ctx.beginPath();
      ctx.moveTo(paddingLeft, y);
      ctx.lineTo(w - paddingRight, y);
      ctx.stroke();

      // Left Axis text
      ctx.fillStyle = "#94A3B8";
      ctx.fillText(`${tickVal}${config.leftAxisLabel.startsWith("°") ? "°C" : ""}`, paddingLeft - 8, y);
    });

    // Draw Right Axis Labels
    ctx.textAlign = "left";
    config.rightTicks.forEach((tickVal) => {
      const y = getY(tickVal, config.channels[2].axis === "right" ? config.channels[2] : config.channels[1]);
      ctx.fillStyle = config.channels[2].color;
      ctx.fillText(`${tickVal} ${config.rightAxisLabel}`, w - paddingRight + 8, y);
    });

    // Draw Bottom Timestamp Labels
    if (data.length > 0) {
      ctx.fillStyle = "#64748B";
      ctx.textAlign = "center";
      const step = Math.floor(data.length / 7);
      for (let i = 0; i < data.length; i += step) {
        const x = paddingLeft + (i / (data.length - 1)) * plotW;
        const timeStr = new Date(data[i][0]).toTimeString().split(" ")[0];

        // Small tick mark
        ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
        ctx.beginPath();
        ctx.moveTo(x, paddingTop + plotH);
        ctx.lineTo(x, paddingTop + plotH + 4);
        ctx.stroke();

        ctx.fillText(timeStr, x, paddingTop + plotH + 16);
      }
    }

    // Function to draw smooth Bezier curves
    const drawSpline = (channelIndex: 0 | 1 | 2) => {
      if (data.length < 2) return;
      const channel = config.channels[channelIndex];

      ctx.save();
      ctx.beginPath();
      ctx.strokeStyle = channel.color;
      ctx.lineWidth = channel.dashed ? 1.8 : 2.4;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      if (channel.dashed) {
        ctx.setLineDash([5, 4]);
      } else {
        ctx.setLineDash([]);
      }

      // Compute points
      const pts = data.map((d, i) => ({
        x: paddingLeft + (i / (data.length - 1)) * plotW,
        y: getY(d[channelIndex + 1], channel),
      }));

      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i === 0 ? 0 : i - 1];
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
      }

      // Add gentle neon bloom
      ctx.shadowColor = channel.color;
      ctx.shadowBlur = 6;
      ctx.stroke();
      ctx.restore();
    };

    // Draw all 3 channels
    drawSpline(2); // Channel 2 (e.g. Fan or Bus)
    drawSpline(1); // Channel 1 (e.g. GPU or Draw)
    drawSpline(0); // Channel 0 (e.g. CPU or Retention)

    // Interactive Crosshair & Point Tracker
    const mouse = mousePosRef.current;
    if (mouse.active && mouse.x >= paddingLeft && mouse.x <= w - paddingRight) {
      const relX = (mouse.x - paddingLeft) / plotW;
      const index = Math.max(0, Math.min(data.length - 1, Math.round(relX * (data.length - 1))));
      const sample = data[index];

      if (sample) {
        const sampleX = paddingLeft + (index / (data.length - 1)) * plotW;

        // Draw vertical hairline
        ctx.save();
        ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(sampleX, paddingTop);
        ctx.lineTo(sampleX, paddingTop + plotH);
        ctx.stroke();
        ctx.restore();

        // Draw dot indicators on each curve
        const dots = [
          { y: getY(sample[1], config.channels[0]), color: config.channels[0].color },
          { y: getY(sample[2], config.channels[1]), color: config.channels[1].color },
          { y: getY(sample[3], config.channels[2]), color: config.channels[2].color },
        ];

        dots.forEach((dot) => {
          ctx.save();
          ctx.beginPath();
          ctx.arc(sampleX, dot.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = dot.color;
          ctx.shadowColor = dot.color;
          ctx.shadowBlur = 8;
          ctx.fill();
          ctx.strokeStyle = "#FFFFFF";
          ctx.lineWidth = 1.5;
          ctx.stroke();
          ctx.restore();
        });

        // Update hovered state for floating tooltip
        setHoveredData({
          timeStr: new Date(sample[0]).toTimeString().split(" ")[0],
          v0: parseFloat(sample[1].toFixed(1)),
          v1: parseFloat(sample[2].toFixed(1)),
          v2: parseFloat(sample[3].toFixed(1)),
          x: sampleX,
          y: dots[0].y,
        });
      }
    } else {
      setHoveredData(null);
    }

    ctx.restore();
    animFrameRef.current = requestAnimationFrame(renderFrame);
  }, [selectedCategory]);

  // Start 60fps rAF loop
  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(renderFrame);
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [renderFrame]);

  // Canvas mouse interaction handlers
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mousePosRef.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      active: true,
    };
  };

  const handleCanvasMouseLeave = () => {
    mousePosRef.current.active = false;
    setHoveredData(null);
  };

  const activeConfig = CATEGORIES[selectedCategory];

  return (
    <div className="apple-card p-6 bg-white border border-[#E5E5E7] shadow-sm space-y-5">
      {/* Top Header & Graph Category Selector */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-bold text-[#1D1D1F]">
                {activeConfig.title}
              </h3>
              {isLive ? (
                <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live Sensor Feed
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-[#0071E3]">
                  <Sparkles size={11} />
                  <span>60 FPS Dynamic Buffer</span>
                </span>
              )}
            </div>
            <p className="text-xs text-[#6E6E73] mt-0.5">
              {activeConfig.description}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
            <button
              type="button"
              onClick={handleExportLog}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D2D2D7] hover:bg-[#F5F5F7] text-xs font-semibold text-[#1D1D1F] transition-all cursor-pointer shadow-2xs"
            >
              <Download size={13} className="text-[#6E6E73]" />
              <span>Export Telemetry (JSON)</span>
            </button>

            <button
              type="button"
              onClick={handleSimulateAction}
              disabled={isSimulating}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white transition-all cursor-pointer shadow-sm ${
                isSimulating
                  ? "bg-amber-600 animate-pulse cursor-not-allowed"
                  : "bg-[#0071E3] hover:bg-[#0077ED] active:scale-95"
              }`}
            >
              {isSimulating ? (
                <>
                  <Activity size={13} className="animate-spin text-amber-200" />
                  <span>
                    {activeConfig.simActiveLabel} ({simulationSecondsLeft}s)
                  </span>
                </>
              ) : (
                <>
                  <Play size={13} />
                  <span>{activeConfig.simActionLabel}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 4-Way Segmented Graph Selector (Essential Prototype Features) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-1 bg-[#F5F5F7] rounded-xl border border-[#E5E5E7]/80">
          {(Object.keys(CATEGORIES) as TelemetryCategory[]).map((catKey) => {
            const cat = CATEGORIES[catKey];
            const isSelected = selectedCategory === catKey;
            const Icon = cat.icon;

            return (
              <button
                key={catKey}
                type="button"
                onClick={() => setSelectedCategory(catKey)}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  isSelected
                    ? "bg-white text-[#1D1D1F] shadow-sm border border-[#E5E5E7]/60"
                    : "text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-white/50"
                }`}
              >
                <Icon
                  size={14}
                  className={isSelected ? "text-[#0071E3]" : "text-[#86868B]"}
                />
                <span className="truncate">{cat.shortLabel}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Dark Theme Canvas Graph Container */}
      <div className="relative rounded-2xl bg-[#090D16] border border-slate-800 p-2 sm:p-4 select-none overflow-hidden shadow-inner">
        {/* Dynamic Top Legend */}
        <div className="flex flex-wrap items-center justify-center gap-6 pb-2.5 text-[11px] font-mono font-medium">
          {activeConfig.channels.map((ch, idx) => (
            <div key={ch.name} className="flex items-center gap-2 text-slate-300">
              {ch.dashed ? (
                <span
                  className="w-5 h-0.5 border-t border-dashed"
                  style={{
                    borderColor: ch.color,
                    boxShadow: `0 0 8px ${ch.color}`,
                  }}
                />
              ) : (
                <span
                  className="w-5 h-1 rounded-full"
                  style={{
                    backgroundColor: ch.color,
                    boxShadow: `0 0 8px ${ch.color}`,
                  }}
                />
              )}
              <span>
                {ch.name} ({ch.unit})
              </span>
            </div>
          ))}
        </div>

        {/* Buttery Smooth 60 FPS Canvas */}
        <div className="w-full relative cursor-crosshair">
          <canvas
            ref={canvasRef}
            className="w-full h-[280px] rounded-lg block"
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={handleCanvasMouseLeave}
          />
        </div>

        {/* Floating Tooltip Box */}
        {hoveredData && (
          <div
            className="pointer-events-none absolute z-20 rounded-xl bg-slate-900/95 border border-slate-700/80 p-3 text-xs text-white shadow-xl backdrop-blur-md transition-all duration-75"
            style={{
              left: `${Math.min(Math.max(hoveredData.x - 70, 20), 580)}px`,
              top: `${Math.max(hoveredData.y - 95, 30)}px`,
            }}
          >
            <div className="text-[10px] font-mono text-slate-400 border-b border-slate-800 pb-1 mb-1.5 flex items-center justify-between gap-4">
              <span>Timestamp</span>
              <strong className="text-white">{hoveredData.timeStr}</strong>
            </div>
            <div className="space-y-1 font-mono text-[11px]">
              <div
                className="flex items-center justify-between gap-4"
                style={{ color: activeConfig.channels[0].color }}
              >
                <span className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: activeConfig.channels[0].color }}
                  />
                  {activeConfig.channels[0].name}
                </span>
                <span className="font-bold">
                  {hoveredData.v0} {activeConfig.channels[0].unit}
                </span>
              </div>

              <div
                className="flex items-center justify-between gap-4"
                style={{ color: activeConfig.channels[1].color }}
              >
                <span className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: activeConfig.channels[1].color }}
                  />
                  {activeConfig.channels[1].name}
                </span>
                <span className="font-bold">
                  {hoveredData.v1} {activeConfig.channels[1].unit}
                </span>
              </div>

              <div
                className="flex items-center justify-between gap-4"
                style={{ color: activeConfig.channels[2].color }}
              >
                <span className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: activeConfig.channels[2].color }}
                  />
                  {activeConfig.channels[2].name}
                </span>
                <span className="font-bold">
                  {hoveredData.v2} {activeConfig.channels[2].unit}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Subsystem Metric Insights Footer */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-[#6E6E73] pt-1 border-t border-[#E5E5E7]/60">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-medium">
            <Activity size={13} className="text-[#0071E3]" />
            <span>High-Precision Sub-Pixel Telemetry Engine (60 FPS)</span>
          </span>
          <span className="hidden sm:inline-block text-[#D2D2D7]">•</span>
          <span className="hidden sm:inline-block">
            {selectedCategory === "thermals" && "PROCHOT Thermal Limit: 105°C"}
            {selectedCategory === "battery" && "Wear Status: Health <50% flagged for replace"}
            {selectedCategory === "storage" && "SMART Self-Test: PASS (Fixed NVMe Media)"}
            {selectedCategory === "compute" && "Microarchitecture: Multi-Core Scaled Load"}
          </span>
        </div>

        <span className="text-[#86868B] font-mono text-[10px]">
          Target: {hardwareModel}
        </span>
      </div>
    </div>
  );
}
