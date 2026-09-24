"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, X, Sparkles, CheckCircle2, AlertCircle, ShieldCheck } from "lucide-react";
import { GoogleLogin, useGoogleLogin } from "@react-oauth/google";
import { useAuth, UserProfile } from "@/context/AuthContext";
import styles from "./AuthModal.module.css";

// Helper function to decode Google ID Token JWT
function parseJwt(token: string): any {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

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

  const router = useRouter();

  // Handle Official Google Sign-In Success (JWT ID Token)
  const handleGoogleSuccess = (credentialResponse: any) => {
    setAuthError(null);
    if (credentialResponse.credential) {
      const payload = parseJwt(credentialResponse.credential);
      if (payload) {
        const userObj: UserProfile = {
          name: payload.name || payload.email.split("@")[0],
          email: payload.email,
          picture: payload.picture,
          provider: "google",
        };
        setActiveUserProfile(userObj);
        loginWithGoogleSuccess(userObj);
        setSubmitted(true);
        setTimeout(() => {
          setSubmitted(false);
          onClose();
          const redirectTarget = localStorage.getItem("reloop_redirect") || "/assess-device";
          localStorage.removeItem("reloop_redirect");
          router.push(redirectTarget);
        }, 1000);
        return;
      }
    }
    setAuthError("Failed to parse Google credentials.");
  };

  // Instant Demo Sign-In (For rapid verification of UI and Navbar state)
  const handleDemoLogin = () => {
    const demoUser: UserProfile = {
      name: "Alex Rivera",
      email: "alex.reloop@gmail.com",
      picture: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
      provider: "google",
    };
    setActiveUserProfile(demoUser);
    loginWithGoogleSuccess(demoUser);
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
      const redirectTarget = localStorage.getItem("reloop_redirect") || "/assess-device";
      localStorage.removeItem("reloop_redirect");
      router.push(redirectTarget);
    }, 1000);
  };

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
      const redirectTarget = localStorage.getItem("reloop_redirect") || "/assess-device";
      localStorage.removeItem("reloop_redirect");
      router.push(redirectTarget);
    }, 1000);
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
                Signed in with Google
              </span>
            </div>
          ) : (
            <div>
              {/* Google Native One-Tap & Button */}
              <div className="flex justify-center mb-3">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => {
                    setAuthError(
                      "Google Sign-In requires 'http://localhost:3000' in Authorized JavaScript Origins in Google Console."
                    );
                  }}
                  theme="outline"
                  shape="pill"
                  text="signup_with"
                  size="large"
                />
              </div>

              {/* Instant Test Mode Helper */}
              <div className="text-center mb-2">
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  className="text-[11px] text-[#0071E3] hover:underline font-medium cursor-pointer"
                >
                  ⚡ Test Google Sign-In with Demo Profile
                </button>
              </div>

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
                Signed in with Google
              </span>
            </div>
          ) : (
            <div>
              {/* Google Native One-Tap & Button */}
              <div className="flex justify-center mb-3">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => {
                    setAuthError(
                      "Google Sign-In requires 'http://localhost:3000' in Authorized JavaScript Origins in Google Console."
                    );
                  }}
                  theme="outline"
                  shape="pill"
                  text="signin_with"
                  size="large"
                />
              </div>

              {/* Instant Test Mode Helper */}
              <div className="text-center mb-2">
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  className="text-[11px] text-[#0071E3] hover:underline font-medium cursor-pointer"
                >
                  ⚡ Test Google Sign-In with Demo Profile
                </button>
              </div>

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
