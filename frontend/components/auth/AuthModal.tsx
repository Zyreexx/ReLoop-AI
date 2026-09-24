"use client";

import React, { useState, useEffect } from "react";
import { Eye, EyeOff, X, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { useGoogleLogin } from "@react-oauth/google";
import { useAuth, UserProfile } from "@/context/AuthContext";
import styles from "./AuthModal.module.css";

interface PasswordFieldProps {
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
}

const PasswordField: React.FC<PasswordFieldProps> = ({
  placeholder = "••••••••",
  value,
  onChange,
  required = true,
}) => {
  const [show, setShow] = useState(false);

  return (
    <div className={styles.passwordField}>
      <input
        type={show ? "text" : "password"}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        required={required}
      />
      <button
        type="button"
        className={styles.eyeBtn}
        onClick={() => setShow((prev) => !prev)}
        aria-label={show ? "Hide password" : "Show password"}
      >
        {show ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
};

interface SocialsProps {
  onGoogleClick: () => void;
  isLoading?: boolean;
}

const Socials: React.FC<SocialsProps> = ({ onGoogleClick, isLoading }) => (
  <div className={styles.socials}>
    <button
      type="button"
      onClick={onGoogleClick}
      disabled={isLoading}
      className={`${styles.socialBtn} w-full flex items-center justify-center gap-2.5 py-2.5 bg-white border border-[#D2D2D7] rounded-xl hover:bg-[#F5F5F7] transition-all cursor-pointer shadow-2xs`}
    >
      <svg width="18" height="18" viewBox="0 0 24 24">
        <path
          fill="#4285F4"
          d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.14z"
        />
        <path
          fill="#34A853"
          d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"
        />
        <path
          fill="#FBBC05"
          d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
        />
        <path
          fill="#EA4335"
          d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
        />
      </svg>
      <span className="text-xs font-semibold text-[#1D1D1F]">
        {isLoading ? "Signing in..." : "Continue with Google"}
      </span>
    </button>
  </div>
);

interface HeroProps {
  variant: "login" | "register";
  title: string;
  text: string;
  buttonLabel: string;
  onSwitch: () => void;
}

const Hero: React.FC<HeroProps> = ({ variant, title, text, buttonLabel, onSwitch }) => (
  <div className={`${styles.hero} ${variant === "register" ? styles.heroRegister : styles.heroLogin}`}>
    <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center mb-2">
      <Sparkles className="w-6 h-6 text-white" />
    </div>
    <h2 className={styles.heroTitle}>{title}</h2>
    <p className={styles.heroText}>{text}</p>
    <button type="button" className={styles.switchBtn} onClick={onSwitch}>
      {buttonLabel}
    </button>
  </div>
);

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: "login" | "register";
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  initialMode = "login",
}) => {
  const { loginWithGoogleSuccess } = useAuth();
  const [isRegister, setIsRegister] = useState(initialMode === "register");
  const [submitted, setSubmitted] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [activeUserProfile, setActiveUserProfile] = useState<UserProfile | null>(null);

  // Login form state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form state
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");

  useEffect(() => {
    setIsRegister(initialMode === "register");
    setAuthError(null);
  }, [initialMode, isOpen]);

  // Google OAuth Login Hook
  const handleGoogleAuth = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setGoogleLoading(true);
      setAuthError(null);
      try {
        const res = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
          headers: {
            Authorization: `Bearer ${tokenResponse.access_token}`,
          },
        });
        const profile = await res.json();
        const userObj: UserProfile = {
          name: profile.name || profile.email.split("@")[0],
          email: profile.email,
          picture: profile.picture,
          provider: "google",
        };
        setActiveUserProfile(userObj);
        loginWithGoogleSuccess(userObj);
        setSubmitted(true);
        setTimeout(() => {
          setSubmitted(false);
          setGoogleLoading(false);
          onClose();
        }, 1200);
      } catch (err) {
        console.error("Failed to fetch Google profile:", err);
        setAuthError("Failed to retrieve Google profile info.");
        setGoogleLoading(false);
      }
    },
    onError: (err) => {
      console.error("Google Auth error:", err);
      setAuthError("Google Sign-In was cancelled or not authorized.");
      setGoogleLoading(false);
    },
  });

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const userObj: UserProfile = {
      name: isRegister ? regName : loginEmail.split("@")[0],
      email: isRegister ? regEmail : loginEmail,
      provider: "email",
    };
    setActiveUserProfile(userObj);
    loginWithGoogleSuccess(userObj);
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
    }, 1200);
  };

  return (
    <div className={styles.backdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div
        className={`${styles.card} ${isRegister ? styles.cardRegister : ""}`}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={18} />
        </button>

        {/* Sliding card background */}
        <div className={styles.cardBg} />

        {/* Hero panels */}
        <Hero
          variant="register"
          title="Welcome back"
          text="Access your saved product condition reports and optimization history."
          buttonLabel="Sign In"
          onSwitch={() => {
            setIsRegister(false);
            setAuthError(null);
          }}
        />

        <Hero
          variant="login"
          title="Hello there"
          text="Join ReLoop to assess hardware health, recover value, and extend product lifecycles."
          buttonLabel="Sign Up"
          onSwitch={() => {
            setIsRegister(true);
            setAuthError(null);
          }}
        />

        {/* Forms */}
        {/* Register Form */}
        <div className={`${styles.form} ${styles.formRegister}`}>
          <div className={styles.formHeader}>
            <h3 className={styles.formTitle}>Create account</h3>
            <p className={styles.formSubtitle}>Sign up with Google or Email</p>
          </div>

          {authError && (
            <div className="mb-3 p-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-1.5">
              <AlertCircle size={14} className="shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          {submitted ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 className="w-12 h-12 text-[#34C759] mb-3 animate-bounce" />
              <p className="text-sm font-semibold text-[#1D1D1F]">
                Welcome, {activeUserProfile?.name}!
              </p>
              <p className="text-xs text-[#6E6E73] mt-1">Preparing your workspace...</p>
            </div>
          ) : (
            <div>
              {/* Google One-Click Button */}
              <Socials onGoogleClick={() => handleGoogleAuth()} isLoading={googleLoading} />

              <div className={styles.divider}>
                <span>or sign up with email</span>
              </div>

              <form onSubmit={handleSubmit}>
                <div className={styles.inputGroup}>
                  <label className={styles.label}>Full Name</label>
                  <input
                    type="text"
                    className={styles.input}
                    placeholder="Alex Morgan"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    required
                  />
                </div>

                <div className={styles.inputGroup}>
                  <label className={styles.label}>Work or Personal Email</label>
                  <input
                    type="email"
                    className={styles.input}
                    placeholder="alex@reloop.ai"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                  />
                </div>

                <div className={styles.inputGroup}>
                  <label className={styles.label}>Password</label>
                  <PasswordField
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                  />
                </div>

                <button type="submit" className={styles.submitBtn}>
                  Create Account
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Login Form */}
        <div className={`${styles.form} ${styles.formLogin}`}>
          <div className={styles.formHeader}>
            <h3 className={styles.formTitle}>Sign in to ReLoop</h3>
            <p className={styles.formSubtitle}>Access your device decision dashboard</p>
          </div>

          {authError && (
            <div className="mb-3 p-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-1.5">
              <AlertCircle size={14} className="shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          {submitted ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 className="w-12 h-12 text-[#34C759] mb-3 animate-bounce" />
              <p className="text-sm font-semibold text-[#1D1D1F]">
                Welcome back, {activeUserProfile?.name}!
              </p>
              <p className="text-xs text-[#6E6E73] mt-1">Opening your assessment profile...</p>
            </div>
          ) : (
            <div>
              {/* Google One-Click Button */}
              <Socials onGoogleClick={() => handleGoogleAuth()} isLoading={googleLoading} />

              <div className={styles.divider}>
                <span>or continue with email</span>
              </div>

              <form onSubmit={handleSubmit}>
                <div className={styles.inputGroup}>
                  <label className={styles.label}>Email Address</label>
                  <input
                    type="email"
                    className={styles.input}
                    placeholder="name@organization.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                  />
                </div>

                <div className={styles.inputGroup}>
                  <div className="flex justify-between items-center mb-1">
                    <label className={styles.label}>Password</label>
                    <a href="#forgot" className="text-xs text-[#0071E3] hover:underline">
                      Forgot?
                    </a>
                  </div>
                  <PasswordField
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </div>

                <button type="submit" className={styles.submitBtn}>
                  Sign In
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
