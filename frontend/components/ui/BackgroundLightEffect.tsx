"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  color: string;
  maxLife: number;
  life: number;
}

export const BackgroundLightEffect: React.FC = () => {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Strictly EXCEPT the landing page ("/")
    if (pathname === "/" || !mounted) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = window.innerWidth;
    let height = window.innerHeight;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const mouse = {
      x: -1000,
      y: -1000,
      targetX: -1000,
      targetY: -1000,
      isOverBackground: false,
      opacity: 0,
      targetOpacity: 0,
    };

    const particles: Particle[] = [];
    const colors = [
      "0, 113, 227",   // ReLoop Electric Blue
      "52, 199, 89",   // Circular Green
      "0, 198, 255",   // Cyan Glow
      "88, 86, 214",   // Indigo Accent
    ];

    // Check if the cursor is directly on top of main display info, cards, tables, buttons, or links
    const checkIsOverMainDisplayOrInteractive = (x: number, y: number): boolean => {
      if (x < 0 || y < 0 || x > width || y > height) return true;
      const el = document.elementFromPoint(x, y);
      if (!el) return false;

      // STRICT EXCLUSION:
      // Must NOT work on:
      // 1. Main display info / content cards (.apple-card, bg-white, rounded cards, linear gradient cards, dark action cards)
      // 2. Interactive controls (buttons, links, form controls, icons, dialogs)
      const isCardOrInteractive = Boolean(
        el.closest(
          '.apple-card, [class*="bg-white"], [class*="rounded-2xl"], [class*="rounded-3xl"], [class*="bg-[#1D1D1F]"], [class*="from-blue-50"], [class*="from-amber-50"], table, form, button, a, input, select, textarea, [role="button"], svg, path, .lucide, [role="dialog"], [role="menu"]'
        )
      );

      return isCardOrInteractive;
    };

    let lastSpawn = 0;
    const handleMouseMove = (e: MouseEvent) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;

      const isOverContent = checkIsOverMainDisplayOrInteractive(e.clientX, e.clientY);
      mouse.isOverBackground = !isOverContent;
      mouse.targetOpacity = mouse.isOverBackground ? 1 : 0;

      // Spawn glowing particles strictly when cursor is over open background / blank whitespace
      if (mouse.isOverBackground) {
        const now = performance.now();
        if (now - lastSpawn > 22) {
          lastSpawn = now;
          const numSpawn = Math.random() > 0.4 ? 2 : 1;
          for (let i = 0; i < numSpawn; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 1.6 + 0.4;
            const color = colors[Math.floor(Math.random() * colors.length)];
            particles.push({
              x: e.clientX + (Math.random() - 0.5) * 12,
              y: e.clientY + (Math.random() - 0.5) * 12,
              vx: Math.cos(angle) * speed,
              vy: Math.sin(angle) * speed - 0.25,
              size: Math.random() * 3 + 1.5,
              alpha: Math.random() * 0.6 + 0.35,
              color,
              maxLife: Math.floor(Math.random() * 45 + 30),
              life: 0,
            });
          }
          if (particles.length > 60) {
            particles.splice(0, particles.length - 60);
          }
        }
      }
    };

    const handleMouseLeave = () => {
      mouse.isOverBackground = false;
      mouse.targetOpacity = 0;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    document.addEventListener("mouseleave", handleMouseLeave);

    // Animation Loop
    const render = () => {
      // Smooth lerp mouse position
      mouse.x += (mouse.targetX - mouse.x) * 0.20;
      mouse.y += (mouse.targetY - mouse.y) * 0.20;

      // Rapid fade-out when entering main display cards, smooth fade-in when in background
      if (!mouse.isOverBackground) {
        mouse.opacity = Math.max(0, mouse.opacity - 0.22);
      } else {
        mouse.opacity += (mouse.targetOpacity - mouse.opacity) * 0.16;
      }

      ctx.clearRect(0, 0, width, height);

      // 1. Render ambient glow aura (STRICTLY in background/blank areas)
      if (mouse.opacity > 0.01 && mouse.x > -200) {
        // Outer soft radiant field
        const outerGlow = ctx.createRadialGradient(
          mouse.x,
          mouse.y,
          0,
          mouse.x,
          mouse.y,
          240
        );
        outerGlow.addColorStop(0, `rgba(0, 113, 227, ${(0.15 * mouse.opacity).toFixed(3)})`);
        outerGlow.addColorStop(0.35, `rgba(0, 198, 255, ${(0.08 * mouse.opacity).toFixed(3)})`);
        outerGlow.addColorStop(0.7, `rgba(52, 199, 89, ${(0.03 * mouse.opacity).toFixed(3)})`);
        outerGlow.addColorStop(1, "rgba(245, 245, 247, 0)");

        ctx.fillStyle = outerGlow;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 240, 0, Math.PI * 2);
        ctx.fill();

        // Inner glowing core
        const coreGlow = ctx.createRadialGradient(
          mouse.x,
          mouse.y,
          0,
          mouse.x,
          mouse.y,
          75
        );
        coreGlow.addColorStop(0, `rgba(0, 113, 227, ${(0.26 * mouse.opacity).toFixed(3)})`);
        coreGlow.addColorStop(0.5, `rgba(0, 198, 255, ${(0.12 * mouse.opacity).toFixed(3)})`);
        coreGlow.addColorStop(1, "rgba(0, 113, 227, 0)");

        ctx.fillStyle = coreGlow;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 75, 0, Math.PI * 2);
        ctx.fill();

        // Subtle pulsing focus ring
        const ringRadius = 20 + Math.sin(Date.now() / 220) * 3;
        ctx.strokeStyle = `rgba(0, 113, 227, ${(0.28 * mouse.opacity).toFixed(3)})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, ringRadius, 0, Math.PI * 2);
        ctx.stroke();
      }

      // 2. Render floating particles (dissolve immediately if drifting into any card)
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];

        // If particle drifted over an info card or interactive element, dissolve immediately
        if (checkIsOverMainDisplayOrInteractive(p.x, p.y)) {
          p.alpha *= 0.65;
          if (p.alpha <= 0.02) {
            particles.splice(i, 1);
            continue;
          }
        }

        p.life++;
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.96;
        p.vy *= 0.96;

        const progress = p.life / p.maxLife;
        const currentAlpha = p.alpha * (1 - progress);

        if (progress >= 1 || currentAlpha <= 0.01) {
          particles.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.fillStyle = `rgba(${p.color}, ${currentAlpha.toFixed(3)})`;
        ctx.shadowColor = `rgba(${p.color}, ${currentAlpha.toFixed(3)})`;
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(0.5, p.size * (1 - progress * 0.3)), 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
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
  }, [pathname, mounted]);

  // Strictly disabled on landing page ("/")
  if (pathname === "/" || !mounted) {
    return null;
  }

  return (
    <div
      className="pointer-events-none fixed inset-0 z-40 overflow-hidden"
      aria-hidden="true"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  );
};
