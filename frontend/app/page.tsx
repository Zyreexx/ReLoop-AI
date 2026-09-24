"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import { HeroSection } from "@/components/landing/HeroSection";
import { PathwaysSection } from "@/components/landing/PathwaysSection";
import { IntakeWorkflowSection } from "@/components/landing/IntakeWorkflowSection";
import { InteractiveEngineSection } from "@/components/landing/InteractiveEngineSection";
import { PhilosophySection } from "@/components/landing/PhilosophySection";

export default function Home() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F5F7] text-[#1D1D1F]">
      {/* Sliding Auth Modal Component (from user screenshots) */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />

      {/* Navigation */}
      <Navbar onOpenAuth={handleOpenAuth} />

      {/* Main Content Sections */}
      <main className="flex-1">
        {/* Hero Section */}
        <HeroSection onOpenAuth={handleOpenAuth} />

        {/* 6 Circular Pathways Section */}
        <PathwaysSection />

        {/* 3-Step Evidence Intake & Provenance */}
        <IntakeWorkflowSection />

        {/* Live Interactive Optimizer Engine */}
        <InteractiveEngineSection onOpenAuth={handleOpenAuth} />

        {/* Core Philosophy & Comparison */}
        <PhilosophySection onOpenAuth={handleOpenAuth} />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
