"use client";

import React, { useState, useEffect } from "react";
import { Eye, EyeOff, X, Sparkles, CheckCircle2 } from "lucide-react";
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

const Socials: React.FC = () => (
  <div className={styles.socials}>
    <button type="button" className={styles.socialBtn}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.56-1.701z" />
      </svg>
      Apple
    </button>
    <button type="button" className={styles.socialBtn}>
      <svg width="16" height="16" viewBox="0 0 24 24">
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
      Google
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
  const [isRegister, setIsRegister] = useState(initialMode === "register");
  const [submitted, setSubmitted] = useState(false);

  // Login form state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form state
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");

  useEffect(() => {
    setIsRegister(initialMode === "register");
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
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
          onSwitch={() => setIsRegister(false)}
        />

        <Hero
          variant="login"
          title="Hello there"
          text="Join ReLoop to assess hardware health, recover value, and extend product lifecycles."
          buttonLabel="Sign Up"
          onSwitch={() => setIsRegister(true)}
        />

        {/* Forms */}
        {/* Register Form */}
        <div className={`${styles.form} ${styles.formRegister}`}>
          <div className={styles.formHeader}>
            <h3 className={styles.formTitle}>Create account</h3>
            <p className={styles.formSubtitle}>Start managing product lifecycles today</p>
          </div>

          {submitted ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 className="w-12 h-12 text-[#34C759] mb-3 animate-bounce" />
              <p className="text-sm font-semibold text-[#1D1D1F]">Welcome to ReLoop!</p>
              <p className="text-xs text-[#6E6E73] mt-1">Preparing your workspace...</p>
            </div>
          ) : (
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

              <div className={styles.divider}>
                <span>or sign up with</span>
              </div>

              <Socials />
            </form>
          )}
        </div>

        {/* Login Form */}
        <div className={`${styles.form} ${styles.formLogin}`}>
          <div className={styles.formHeader}>
            <h3 className={styles.formTitle}>Sign in to ReLoop</h3>
            <p className={styles.formSubtitle}>Next-Life Engine decision dashboard</p>
          </div>

          {submitted ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 className="w-12 h-12 text-[#34C759] mb-3 animate-bounce" />
              <p className="text-sm font-semibold text-[#1D1D1F]">Signed in successfully</p>
              <p className="text-xs text-[#6E6E73] mt-1">Opening your assessment profile...</p>
            </div>
          ) : (
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

              <div className={styles.divider}>
                <span>or continue with</span>
              </div>

              <Socials />
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
