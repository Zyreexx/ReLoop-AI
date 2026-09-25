"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AuthModal } from "@/components/auth/AuthModal";
import { InteractiveEngineSection } from "@/components/landing/InteractiveEngineSection";
import { AssessedDeviceEngine } from "@/components/engine/AssessedDeviceEngine";

function EngineContent({ onOpenAuth }: { onOpenAuth: (mode: "login" | "register") => void }) {
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");

  // If an assessment ID is provided (e.g. redirected from device assessment),
  // show EXCLUSIVELY the details and circular pathways for the uploaded device (no Lenovo / MacBook).
  if (assessmentId) {
    return (
      <AssessedDeviceEngine
        assessmentId={assessmentId}
        onOpenAuth={onOpenAuth}
      />
    );
  }

  // Fallback to demo simulator when visiting /engine without an uploaded device assessment
  return <InteractiveEngineSection onOpenAuth={onOpenAuth} />;
}

export default function EnginePage() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  const handleOpenAuth = (mode: "login" | "register") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F5F7] text-[#1D1D1F] relative">
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
      <Navbar onOpenAuth={handleOpenAuth} />
      <main className="flex-1">
        <Suspense
          fallback={
            <div className="max-w-5xl mx-auto px-6 py-24 text-center">
              <div className="w-10 h-10 rounded-full border-4 border-[#0071E3] border-t-transparent animate-spin mx-auto mb-3" />
              <p className="text-xs font-semibold text-[#6E6E73]">Loading optimizer engine...</p>
            </div>
          }
        >
          <EngineContent onOpenAuth={handleOpenAuth} />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
