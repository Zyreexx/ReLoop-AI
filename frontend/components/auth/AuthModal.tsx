"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, X, Sparkles, CheckCircle2, AlertCircle, ShieldCheck } from "lucide-react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth, UserProfile } from "@/context/AuthContext";
import styles from "./AuthModal.module.css";

// ─── Types ────────────────────────────────────────────────────────────────────

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

// ─── Auth Modal ───────────────────────────────────────────────────────────────

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
  const router = useRouter();
  const { loginWithGoogleSuccess } = useAuth();

  const [isRegister, setIsRegister] = useState(initialMode === "register");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [activeUserProfile, setActiveUserProfile] = useState<UserProfile | null>(null);

  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");

  useEffect(() => {
    setIsRegister(initialMode === "register");
    setAuthError(null);
  }, [initialMode, isOpen]);

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

  // ── Shared success handler ────────────────────────────────────────────────

  const handleAuthSuccess = (profile: UserProfile) => {
    setActiveUserProfile(profile);
    loginWithGoogleSuccess(profile);
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
      const redirectTarget = localStorage.getItem("reloop_redirect") || "/assess-device";
      localStorage.removeItem("reloop_redirect");
      router.push(redirectTarget);
    }, 1200);
  };

  // ── Google Sign-In / Sign-Up ──────────────────────────────────────────────

  /**
   * Called by the GoogleLogin component when the user picks a Google account.
   * The credential is a signed Google JWT (ID token).
   * We send it to our backend which:
   *  1. Verifies email_verified=true
   *  2. If mode=login: rejects if user is not already registered (404)
   *  3. If mode=register: creates the account, or logs in if already exists
   */
  const handleGoogleSuccess = async (credentialResponse: any) => {
    setAuthError(null);
    if (!credentialResponse.credential) {
      setAuthError("Failed to receive Google credential.");
      return;
    }

    setLoading(true);
    try {
      const mode = isRegister ? "register" : "login";
      const res = await fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          credential: credentialResponse.credential,
          mode,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        // 404 = not registered yet
        if (res.status === 404) {
          setAuthError(
            "No account found with this Google email. Please sign up first using the 'Sign Up' tab."
          );
        } else {
          setAuthError(data.error || "Google sign-in failed.");
        }
        return;
      }

      handleAuthSuccess({
        name: data.name,
        email: data.email,
        picture: data.picture,
        provider: "google",
      });
    } catch {
      setAuthError("Could not connect to the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setAuthError(
      "Google Sign-In failed. Ensure 'http://localhost:3000' is in Authorized JavaScript Origins."
    );
  };

  // ── Email Registration ────────────────────────────────────────────────────

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: regName,
          email: regEmail,
          password: regPassword,
          provider: "email",
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        // 409 = already registered
        if (res.status === 409) {
          setAuthError(
            "An account with this email already exists. Please sign in instead."
          );
          setTimeout(() => {
            setIsRegister(false);
            setAuthError(null);
          }, 2500);
        } else {
          setAuthError(data.error || "Registration failed.");
        }
        return;
      }

      handleAuthSuccess({
        name: data.name,
        email: data.email,
        picture: data.picture,
        provider: "email",
      });
    } catch {
      setAuthError("Could not connect to the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  // ── Email Login ───────────────────────────────────────────────────────────

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });

      const data = await res.json();

      if (!res.ok) {
        // 404 = not registered
        if (res.status === 404) {
          setAuthError(
            "No account found with this email. Please sign up first."
          );
          setTimeout(() => {
            setIsRegister(true);
            setRegEmail(loginEmail);
            setAuthError(null);
          }, 2500);
        } else if (res.status === 401) {
          setAuthError("Incorrect password. Please try again.");
        } else if (res.status === 400) {
          setAuthError(data.error || "Sign-in error.");
        } else {
          setAuthError(data.error || "Login failed.");
        }
        return;
      }

      handleAuthSuccess({
        name: data.name,
        email: data.email,
        picture: data.picture,
        provider: data.provider as "google" | "email",
      });
    } catch {
      setAuthError("Could not connect to the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  // ── JSX ───────────────────────────────────────────────────────────────────

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
          onSwitch={() => { setIsRegister(false); setAuthError(null); }}
        />
        <Hero
          variant="login"
          title="Hello there"
          text="Join ReLoop to assess hardware health, recover value, and extend product lifecycles."
          buttonLabel="Sign Up"
          onSwitch={() => { setIsRegister(true); setAuthError(null); }}
        />

        {/* ── Register Form ── */}
        <div className={`${styles.form} ${styles.formRegister}`}>
          <div className={styles.formHeader}>
            <h3 className={styles.formTitle}>Create account</h3>
            <p className={styles.formSubtitle}>Sign up with your Google account</p>
          </div>

          {authError && (
            <div className="mb-3 p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-1.5 leading-snug">
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              <span>{authError}</span>
            </div>
          )}

          {submitted ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 className="w-12 h-12 text-[#34C759] mb-3 animate-bounce" />
              <p className="text-sm font-semibold text-[#1D1D1F]">
                Welcome, {activeUserProfile?.name}!
              </p>
              <p className="text-xs text-[#6E6E73] mt-1">{activeUserProfile?.email}</p>
              <span className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-[#0071E3]">
                <ShieldCheck size={13} />
                Account created &amp; signed in
              </span>
            </div>
          ) : (
            <div>
              {/* Google Sign Up */}
              <div className="flex justify-center mb-3">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  theme="outline"
                  shape="pill"
                  text="signup_with"
                  size="large"
                />
              </div>

              <div className={styles.divider}>
                <span>or sign up with email</span>
              </div>

              <form onSubmit={handleRegisterSubmit}>
                <div className={styles.inputGroup}>
                  <label className={styles.label}>Full Name</label>
                  <input
                    type="text"
                    className={styles.input}
                    placeholder="Alex Morgan"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className={styles.inputGroup}>
                  <label className={styles.label}>Email Address</label>
                  <input
                    type="email"
                    className={styles.input}
                    placeholder="alex@example.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className={styles.inputGroup}>
                  <label className={styles.label}>Password</label>
                  <PasswordField
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  className={styles.submitBtn}
                  disabled={loading}
                >
                  {loading ? "Creating account…" : "Create Account"}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* ── Login Form ── */}
        <div className={`${styles.form} ${styles.formLogin}`}>
          <div className={styles.formHeader}>
            <h3 className={styles.formTitle}>Sign in to ReLoop</h3>
            <p className={styles.formSubtitle}>
              Use your Google account or email &amp; password
            </p>
          </div>

          {authError && (
            <div className="mb-3 p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-1.5 leading-snug">
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              <span>{authError}</span>
            </div>
          )}

          {submitted ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 className="w-12 h-12 text-[#34C759] mb-3 animate-bounce" />
              <p className="text-sm font-semibold text-[#1D1D1F]">
                Welcome back, {activeUserProfile?.name}!
              </p>
              <p className="text-xs text-[#6E6E73] mt-1">{activeUserProfile?.email}</p>
              <span className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-[#0071E3]">
                <ShieldCheck size={13} />
                Signed in successfully
              </span>
            </div>
          ) : (
            <div>
              {/* Google Sign In — only valid Google emails accepted */}
              <div className="flex justify-center mb-3">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  theme="outline"
                  shape="pill"
                  text="signin_with"
                  size="large"
                />
              </div>

              <p className="text-center text-[10px] text-[#6E6E73] mb-3">
                Google login only accepts verified Google email accounts.
              </p>

              <div className={styles.divider}>
                <span>or continue with email</span>
              </div>

              <form onSubmit={handleLoginSubmit}>
                <div className={styles.inputGroup}>
                  <label className={styles.label}>Email Address</label>
                  <input
                    type="email"
                    className={styles.input}
                    placeholder="name@organization.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                    disabled={loading}
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

                <button
                  type="submit"
                  className={styles.submitBtn}
                  disabled={loading}
                >
                  {loading ? "Signing in…" : "Sign In"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
