"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";

export interface UserProfile {
  name: string;
  email: string;
  picture?: string;
  provider: "google" | "email";
  is_email_verified?: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;
  logout: () => void;
  loginWithGoogleSuccess: (profile: UserProfile) => void;
  syncGuestHistoryToAccount: (userEmail: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
  "459609082152-c8bqll8nrehc98p1ua8io2iad9io4rpm.apps.googleusercontent.com";

/**
 * Migrates any temporary assessments created while browsing as guest
 * into the authenticated user's permanent hardware ledger.
 */
export async function migrateGuestAssessmentsToUser(userEmail: string) {
  if (typeof window === "undefined" || !userEmail) return;
  try {
    const cleanEmail = userEmail.toLowerCase().trim();
    const userListKey = `reloop_user_assessments_${cleanEmail}`;
    const userList: any[] = JSON.parse(localStorage.getItem(userListKey) || "[]");
    const existingIds = new Set(userList.map((a: any) => a.id));

    // Gather guest records from reloop_guest_assessments and current_assessment
    const guestList: any[] = JSON.parse(localStorage.getItem("reloop_guest_assessments") || "[]");
    const current = localStorage.getItem("current_assessment");
    if (current) {
      try {
        const parsed = JSON.parse(current);
        if (parsed && (!parsed.userId || parsed.userId === "guest" || !parsed.userEmail)) {
          if (!guestList.some((g: any) => g.id === parsed.id)) {
            guestList.push(parsed);
          }
        }
      } catch {}
    }

    if (guestList.length > 0) {
      for (const item of guestList) {
        const enriched = {
          ...item,
          userId: cleanEmail,
          userEmail: cleanEmail,
          isGuest: false,
        };

        if (!existingIds.has(item.id)) {
          userList.unshift(enriched);
          existingIds.add(item.id);
        }

        // Also update individual item in localStorage
        try {
          localStorage.setItem(`assessment_${item.id}`, JSON.stringify(enriched));
        } catch {}

        // Sync to server API
        fetch("/api/assessments", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(enriched),
        }).catch((e) => console.warn("Failed syncing migrated assessment to API:", e));
      }

      localStorage.setItem(userListKey, JSON.stringify(userList));
      localStorage.removeItem("reloop_guest_assessments");
      console.log(`[ReLoop] Successfully migrated ${guestList.length} guest assessment(s) to ${cleanEmail}`);
    }
  } catch (err) {
    console.warn("[ReLoop] Guest assessment migration error:", err);
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("reloop_user");
      if (stored) {
        const parsed = JSON.parse(stored);
        setUser(parsed);
        if (parsed?.email) {
          migrateGuestAssessmentsToUser(parsed.email);
        }
      }
    } catch {
      // Ignore storage errors
    }
  }, []);

  const loginWithGoogleSuccess = (profile: UserProfile) => {
    setUser(profile);
    try {
      localStorage.setItem("reloop_user", JSON.stringify(profile));
      if (profile.email) {
        migrateGuestAssessmentsToUser(profile.email);
      }
    } catch {
      // Ignore storage errors
    }
  };

  const syncGuestHistoryToAccount = async (userEmail: string) => {
    await migrateGuestAssessmentsToUser(userEmail);
  };

  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem("reloop_user");
    } catch {
      // Ignore storage errors
    }
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthContext.Provider
        value={{
          user,
          setUser,
          logout,
          loginWithGoogleSuccess,
          syncGuestHistoryToAccount,
        }}
      >
        {children}
      </AuthContext.Provider>
    </GoogleOAuthProvider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
