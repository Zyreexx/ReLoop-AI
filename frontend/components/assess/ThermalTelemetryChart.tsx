"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import { Download, Play, Flame, CheckCircle, RefreshCw, Activity } from "lucide-react";

export interface TelemetryPoint {
  time: string;
  timestamp: number;
  cpuTemp: number; // °C (20 to 110)
  gpuTemp: number; // °C (20 to 110)
  fanRpm: number;  // RPM (500 to 3500)
}

interface ThermalTelemetryChartProps {
  initialBaseTemp?: number;
  initialMaxTemp?: number;
  hardwareModel?: string;
  isLive?: boolean;
  telemetryData?: TelemetryPoint[];
}

export default function ThermalTelemetryChart({
  initialBaseTemp = 42,
  initialMaxTemp = 48,
  hardwareModel = "Hardware Sensor Bus",
  isLive = false,
  telemetryData,
}: ThermalTelemetryChartProps) {
  const [dataPoints, setDataPoints] = useState<TelemetryPoint[]>(telemetryData || []);
  const [hoveredPoint, setHoveredPoint] = useState<{
    point: TelemetryPoint;
    x: number;
    y: number;
  } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Sync incoming real telemetry stream if provided
  useEffect(() => {
    if (telemetryData) {
      setDataPoints(telemetryData);
    }
  }, [telemetryData]);

  // Export JSON log
  const handleExportLog = () => {
    const jsonStr = JSON.stringify(
      {
        exportedAt: new Date().toISOString(),
        hardwareModel,
        sampleCount: dataPoints.length,
        telemetry: dataPoints,
      },
      null,
      2
    );

    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reloop-thermal-telemetry-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Dimensions for SVG Chart
  const svgWidth = 840;
  const svgHeight = 280;
  const paddingLeft = 52;
  const paddingRight = 62;
  const paddingTop = 28;
  const paddingBottom = 42;

  const chartWidth = svgWidth - paddingLeft - paddingRight;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  // Temperature scale: 20°C to 110°C (range 90)
  const tempMin = 20;
  const tempMax = 110;
  const tempToY = (temp: number) => {
    const clamped = Math.max(tempMin, Math.min(tempMax, temp));
    return paddingTop + chartHeight - ((clamped - tempMin) / (tempMax - tempMin)) * chartHeight;
  };

  // Fan RPM scale: 500 RPM to 3500 RPM (range 3000)
  const rpmMin = 500;
  const rpmMax = 3500;
  const rpmToY = (rpm: number) => {
    const clamped = Math.max(rpmMin, Math.min(rpmMax, rpm));
    return paddingTop + chartHeight - ((clamped - rpmMin) / (rpmMax - rpmMin)) * chartHeight;
  };

  // Map index to X coordinate
  const indexToX = (index: number) => {
    if (dataPoints.length <= 1) return paddingLeft;
    return paddingLeft + (index / (dataPoints.length - 1)) * chartWidth;
  };

  // Generate smooth SVG Bézier path
  const generateSmoothPath = (getY: (p: TelemetryPoint) => number) => {
    if (dataPoints.length < 2) return "";
    const points = dataPoints.map((p, i) => ({ x: indexToX(i), y: getY(p) }));

    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? 0 : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2 < points.length ? i + 2 : i + 1];

      // Catmull-Rom to Cubic Bézier conversion
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }
    return d;
  };

  const cpuPath = useMemo(() => generateSmoothPath((p) => tempToY(p.cpuTemp)), [dataPoints]);
  const gpuPath = useMemo(() => generateSmoothPath((p) => tempToY(p.gpuTemp)), [dataPoints]);
  const fanPath = useMemo(() => generateSmoothPath((p) => rpmToY(p.fanRpm)), [dataPoints]);

  // Y-axis tick values
  const tempTicks = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110];
  const rpmTicks = [500, 1000, 1500, 2000, 2500, 3000, 3500];

  // Mouse move handler for interactive tooltip
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const scaleX = svgWidth / rect.width;
    const adjustedX = mouseX * scaleX;

    if (adjustedX < paddingLeft || adjustedX > svgWidth - paddingRight) {
      setHoveredPoint(null);
      return;
    }

    const relX = (adjustedX - paddingLeft) / chartWidth;
    const index = Math.round(relX * (dataPoints.length - 1));
    const clampedIndex = Math.max(0, Math.min(dataPoints.length - 1, index));
    const point = dataPoints[clampedIndex];

    if (point) {
      setHoveredPoint({
        point,
        x: indexToX(clampedIndex),
        y: tempToY(point.cpuTemp),
      });
    }
  };

  const handleMouseLeave = () => {
    setHoveredPoint(null);
  };

  return (
    <div className="apple-card p-6 bg-white border border-[#E5E5E7] shadow-sm space-y-4">
      {/* Header bar matching the user's reference */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base sm:text-lg font-bold text-[#1D1D1F]">
              Thermal Sensor Telemetry
            </h3>
            {isLive ? (
              <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Agent Telemetry
              </span>
            ) : (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                Sensor Bus Idle
              </span>
            )}
          </div>
          <p className="text-xs text-[#6E6E73] mt-0.5">
            Synchronized CPU Package, GPU Core, and PWM Fan Speed curves — {isLive ? "verified through hardware diagnostics." : "hardware sensor telemetry stream."}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
          <button
            type="button"
            onClick={handleExportLog}
            disabled={dataPoints.length === 0}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D2D2D7] hover:bg-[#F5F5F7] text-xs font-semibold text-[#1D1D1F] transition-all cursor-pointer shadow-2xs disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={13} className="text-[#6E6E73]" />
            <span>Export Log (JSON)</span>
          </button>
        </div>
      </div>

      {/* Main Dark Theme Graph Container */}
      <div
        ref={containerRef}
        className="relative rounded-2xl bg-[#090D16] border border-slate-800 p-2 sm:p-4 select-none overflow-hidden shadow-inner"
      >
        {/* Top Legend Bar */}
        <div className="flex items-center justify-center gap-6 pb-2 text-[11px] font-mono font-medium">
          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-5 h-1 rounded-full bg-[#A855F7] shadow-[0_0_8px_#A855F7]" />
            <span>CPU Package (°C)</span>
          </div>

          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-5 h-1 rounded-full bg-[#38BDF8] shadow-[0_0_8px_#38BDF8]" />
            <span>GPU Core (°C)</span>
          </div>

          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-5 h-0.5 border-t border-dashed border-[#14B8A6] shadow-[0_0_8px_#14B8A6]" />
            <span>Cooling Fan (RPM)</span>
          </div>
        </div>

        {/* SVG Canvas */}
        <div className="w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-auto min-w-[620px]"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            <defs>
              {/* CPU Glow Gradient */}
              <linearGradient id="cpuGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#A855F7" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#A855F7" stopOpacity="0.0" />
              </linearGradient>

              {/* GPU Glow Gradient */}
              <linearGradient id="gpuGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.18" />
                <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Horizontal Gridlines (Temperature) */}
            {tempTicks.map((t) => {
              const y = tempToY(t);
              return (
                <g key={`grid-temp-${t}`}>
                  <line
                    x1={paddingLeft}
                    y1={y}
                    x2={svgWidth - paddingRight}
                    y2={y}
                    stroke="rgba(255, 255, 255, 0.07)"
                    strokeWidth="1"
                    strokeDasharray={t % 20 === 0 ? "none" : "2 3"}
                  />
                  {/* Left Y-Axis Label: Temperature */}
                  <text
                    x={paddingLeft - 8}
                    y={y + 3.5}
                    textAnchor="end"
                    className="text-[9px] font-mono fill-slate-400 select-none"
                  >
                    {t}°C
                  </text>
                </g>
              );
            })}

            {/* Right Y-Axis Labels: Fan RPM */}
            {rpmTicks.map((rpm) => {
              const y = rpmToY(rpm);
              return (
                <text
                  key={`label-rpm-${rpm}`}
                  x={svgWidth - paddingRight + 8}
                  y={y + 3.5}
                  textAnchor="start"
                  className="text-[9px] font-mono fill-teal-400 select-none"
                >
                  {rpm} RPM
                </text>
              );
            })}

            {/* X-Axis Rolling Timestamps */}
            {dataPoints.map((p, i) => {
              // Display every 4th or 5th timestamp to keep axis clean
              if (i % 4 !== 0 && i !== dataPoints.length - 1) return null;
              const x = indexToX(i);
              return (
                <g key={`time-${p.timestamp}-${i}`}>
                  <line
                    x1={x}
                    y1={paddingTop + chartHeight}
                    x2={x}
                    y2={paddingTop + chartHeight + 4}
                    stroke="rgba(255, 255, 255, 0.2)"
                    strokeWidth="1"
                  />
                  <text
                    x={x}
                    y={paddingTop + chartHeight + 16}
                    textAnchor="middle"
                    className="text-[8.5px] font-mono fill-slate-400 select-none"
                    transform={`rotate(-25, ${x}, ${paddingTop + chartHeight + 16})`}
                  >
                    {p.time}
                  </text>
                </g>
              );
            })}

            {dataPoints.length === 0 && (
              <g>
                <text
                  x={svgWidth / 2}
                  y={paddingTop + chartHeight / 2}
                  textAnchor="middle"
                  className="text-xs font-mono fill-slate-400 select-none"
                >
                  Waiting for hardware telemetry stream...
                </text>
              </g>
            )}

            {/* Cooling Fan RPM Path (Dashed Teal) */}
            <path
              d={fanPath}
              fill="none"
              stroke="#14B8A6"
              strokeWidth="2"
              strokeDasharray="4 3"
              strokeLinecap="round"
              className="transition-all duration-300"
            />

            {/* GPU Core Temp Path (Cyan) */}
            <path
              d={gpuPath}
              fill="none"
              stroke="#38BDF8"
              strokeWidth="2.5"
              strokeLinecap="round"
              className="transition-all duration-300"
            />

            {/* CPU Package Temp Path (Purple) */}
            <path
              d={cpuPath}
              fill="none"
              stroke="#A855F7"
              strokeWidth="2.5"
              strokeLinecap="round"
              className="transition-all duration-300"
            />

            {/* Interactive Hover Indicator */}
            {hoveredPoint && (
              <g>
                {/* Vertical Cursor Line */}
                <line
                  x1={hoveredPoint.x}
                  y1={paddingTop}
                  x2={hoveredPoint.x}
                  y2={paddingTop + chartHeight}
                  stroke="rgba(255, 255, 255, 0.35)"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                />

                {/* Point Highlight on CPU Curve */}
                <circle
                  cx={hoveredPoint.x}
                  y={tempToY(hoveredPoint.point.cpuTemp)}
                  r="4.5"
                  fill="#A855F7"
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />

                {/* Point Highlight on GPU Curve */}
                <circle
                  cx={hoveredPoint.x}
                  y={tempToY(hoveredPoint.point.gpuTemp)}
                  r="4"
                  fill="#38BDF8"
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />

                {/* Point Highlight on Fan Curve */}
                <circle
                  cx={hoveredPoint.x}
                  y={rpmToY(hoveredPoint.point.fanRpm)}
                  r="3.5"
                  fill="#14B8A6"
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />
              </g>
            )}
          </svg>
        </div>

        {/* Floating Tooltip Box */}
        {hoveredPoint && (
          <div
            className="pointer-events-none absolute z-20 rounded-xl bg-slate-900/95 border border-slate-700/80 p-3 text-xs text-white shadow-xl backdrop-blur-md"
            style={{
              left: `${Math.min(
                Math.max(hoveredPoint.x - 70, 60),
                svgWidth - 170
              )}px`,
              top: `${Math.max(hoveredPoint.y - 85, 40)}px`,
            }}
          >
            <div className="text-[10px] font-mono text-slate-400 border-b border-slate-800 pb-1 mb-1.5 flex items-center justify-between gap-4">
              <span>Timestamp</span>
              <strong className="text-white">{hoveredPoint.point.time}</strong>
            </div>
            <div className="space-y-1 font-mono text-[11px]">
              <div className="flex items-center justify-between gap-3 text-purple-300">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#A855F7]" />
                  CPU Package
                </span>
                <span className="font-bold">{hoveredPoint.point.cpuTemp}°C</span>
              </div>
              <div className="flex items-center justify-between gap-3 text-sky-300">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#38BDF8]" />
                  GPU Core
                </span>
                <span className="font-bold">{hoveredPoint.point.gpuTemp}°C</span>
              </div>
              <div className="flex items-center justify-between gap-3 text-teal-300">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#14B8A6]" />
                  Cooling Fan
                </span>
                <span className="font-bold">{hoveredPoint.point.fanRpm} RPM</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Details */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-[#6E6E73] pt-1">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <Activity size={12} className="text-[#0071E3]" />
            <span>Sampling: 1 Hz Rolling Window</span>
          </span>
          <span className="hidden sm:inline-block">•</span>
          <span className="hidden sm:inline-block">Peak Thermal Limit: 105°C (PROCHOT)</span>
        </div>
        <span className="text-[#86868B] font-mono text-[10px]">
          Target: {hardwareModel}
        </span>
      </div>
    </div>
  );
}

