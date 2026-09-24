"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

interface TrailPoint {
  x: number;
  y: number;
  id: number;
  radius: number;
  color: string;
}

export const BackgroundLightEffect: React.FC = () => {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const mousePos = useRef({ x: -1000, y: -1000 });
  const targetPos = useRef({ x: -1000, y: -1000 });
  const [active, setActive] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Only activate on pages OTHER than the landing page
    if (pathname === "/" || !mounted) return;

    let animId: number;
    const trails: TrailPoint[] = [];
    let pointId = 0;
    let lastSpawn = 0;

    const colors = [
      "rgba(0, 113, 227, ", // ReLoop Electric Blue
      "rgba(52, 199, 89, ",  // Circular Green
      "rgba(0, 198, 255, ",  // Radiant Cyan
    ];

    const handleMouseMove = (e: MouseEvent) => {
      targetPos.current = { x: e.clientX, y: e.clientY };
      setActive(true);

      const now = performance.now();
      if (now - lastSpawn > 35) {
        lastSpawn = now;
        const color = colors[pointId % colors.length];
        trails.push({
          x: e.clientX,
          y: e.clientY,
          id: pointId++,
          radius: Math.random() * 28 + 20,
          color,
        });
        if (trails.length > 25) {
          trails.shift();
        }
      }
    };

    const handleMouseLeave = () => {
      setActive(false);
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    document.addEventListener("mouseleave", handleMouseLeave);

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const render = () => {
      // Smooth lerp mouse position for silky motion
      mousePos.current.x += (targetPos.current.x - mousePos.current.x) * 0.18;
      mousePos.current.y += (targetPos.current.y - mousePos.current.y) * 0.18;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (active && mousePos.current.x > -500) {
        // 1. Primary ambient spotlight (large diffused field)
        const primaryGlow = ctx.createRadialGradient(
          mousePos.current.x,
          mousePos.current.y,
          0,
          mousePos.current.x,
          mousePos.current.y,
          420
        );
        primaryGlow.addColorStop(0, "rgba(0, 113, 227, 0.14)");
        primaryGlow.addColorStop(0.35, "rgba(52, 199, 89, 0.08)");
        primaryGlow.addColorStop(0.7, "rgba(0, 113, 227, 0.03)");
        primaryGlow.addColorStop(1, "rgba(245, 245, 247, 0)");

        ctx.fillStyle = primaryGlow;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 2. High-vibrancy core spotlight
        const coreGlow = ctx.createRadialGradient(
          mousePos.current.x,
          mousePos.current.y,
          0,
          mousePos.current.x,
          mousePos.current.y,
          160
        );
        coreGlow.addColorStop(0, "rgba(0, 113, 227, 0.22)");
        coreGlow.addColorStop(0.5, "rgba(0, 198, 255, 0.10)");
        coreGlow.addColorStop(1, "rgba(0, 113, 227, 0)");

        ctx.fillStyle = coreGlow;
        ctx.beginPath();
        ctx.arc(mousePos.current.x, mousePos.current.y, 160, 0, Math.PI * 2);
        ctx.fill();

        // 3. Ethereal ambient light trails in the blank space
        for (let i = trails.length - 1; i >= 0; i--) {
          const p = trails[i];
          const age = trails.length - i;
          const alpha = Math.max(0, 0.12 - (age / trails.length) * 0.12);

          if (alpha <= 0.005) {
            trails.splice(i, 1);
            continue;
          }

          const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
          grad.addColorStop(0, `${p.color}${alpha.toFixed(3)})`);
          grad.addColorStop(1, `${p.color}0)`);

          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("resize", resize);
    };
  }, [pathname, mounted, active]);

  // Except landing page
  if (pathname === "/" || !mounted) {
    return null;
  }

  return (
    <div
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden transition-opacity duration-500"
      style={{ opacity: active ? 1 : 0 }}
      aria-hidden="true"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  );
};
