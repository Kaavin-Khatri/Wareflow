"use client";

import React, { useEffect, useRef, useState } from "react";
import { GlassModal } from "./glass/GlassModal";
import { GlassButton } from "./glass/GlassButton";
import { GlassInput } from "./glass/GlassInput";
import { getAuthToken, setTwoFactorVerified } from "@/lib/api-client";
import { ShieldCheck, KeyRound, AlertCircle } from "lucide-react";

export function TwoFactorChallengeModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [digits, setDigits] = useState<string[]>(["", "", "", "", "", ""]);
  const [backupCode, setBackupCode] = useState("");
  const [isBackupMode, setIsBackupMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    const handleRequired = () => {
      setIsOpen((currentlyOpen) => {
        if (currentlyOpen) return true;
        setError(null);
        setSuccess(false);
        setDigits(["", "", "", "", "", ""]);
        setBackupCode("");
        setTimeout(() => {
          inputRefs.current[0]?.focus();
        }, 100);
        return true;
      });
    };

    window.addEventListener("wareflow:2fa-required", handleRequired);
    return () => {
      window.removeEventListener("wareflow:2fa-required", handleRequired);
    };
  }, []);

  useEffect(() => {
    if (isOpen && !isBackupMode) {
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    }
  }, [isOpen, isBackupMode]);

  const handleDigitChange = (index: number, value: string) => {
    if (value.length > 1) {
      const pasted = value.replace(/\D/g, "").slice(0, 6);
      if (pasted.length > 0) {
        const nextDigits = [...digits];
        for (let i = 0; i < 6; i++) {
          nextDigits[i] = pasted[i] || "";
        }
        setDigits(nextDigits);
        const nextFocus = Math.min(pasted.length, 5);
        inputRefs.current[nextFocus]?.focus();
        if (pasted.length === 6) {
          verifyCode(pasted);
        }
        return;
      }
    }

    const cleanChar = value.replace(/\D/g, "");
    const nextDigits = [...digits];
    nextDigits[index] = cleanChar;
    setDigits(nextDigits);

    if (cleanChar && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    const fullCode = nextDigits.join("");
    if (fullCode.length === 6) {
      verifyCode(fullCode);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length > 0) {
      const nextDigits = [...digits];
      for (let i = 0; i < 6; i++) {
        nextDigits[i] = pasted[i] || "";
      }
      setDigits(nextDigits);
      const nextFocus = Math.min(pasted.length, 5);
      inputRefs.current[nextFocus]?.focus();
      if (pasted.length === 6) {
        verifyCode(pasted);
      }
    }
  };

  const verifyCode = async (codeToVerify: string) => {
    setIsLoading(true);
    setError(null);

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const apiUrl = baseUrl.replace(/\/$/, "");

    try {
      const token = await getAuthToken();

      const res = await fetch(`${apiUrl}/auth/2fa/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ code: codeToVerify }),
        credentials: "include",
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Invalid verification code. Please try again.");
      }

      setTwoFactorVerified(true);
      await fetch("/api/auth/session", { method: "PATCH" }).catch(() => {});

      setSuccess(true);
      window.dispatchEvent(new CustomEvent("wareflow:2fa-verified"));

      setTimeout(() => {
        setIsOpen(false);
        setSuccess(false);
      }, 700);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification failed. Please try again.");
      setDigits(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!backupCode.trim()) return;
    verifyCode(backupCode.trim());
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      title="Two-Factor Verification Required"
      description="Enter your 6-digit authenticator code to confirm this operation."
      maxWidth="md"
    >
      <div className="space-y-6 pt-2">
        {/* Error Notice */}
        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Notice */}
        {success && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2.5">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>Two-factor identity verified successfully.</span>
          </div>
        )}

        {!isBackupMode ? (
          <div className="space-y-6">
            <div className="flex justify-between gap-2" onPaste={handlePaste}>
              {digits.map((d, index) => (
                <input
                  key={index}
                  ref={(el) => {
                    inputRefs.current[index] = el;
                  }}
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  value={d}
                  disabled={isLoading || success}
                  onChange={(e) => handleDigitChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className="w-11 h-13 text-center text-xl font-bold rounded-xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition shadow-inner"
                />
              ))}
            </div>

            <div className="flex items-center justify-between gap-3 pt-2">
              <GlassButton
                variant="ghost"
                size="sm"
                type="button"
                onClick={() => {
                  setIsBackupMode(true);
                  setError(null);
                }}
                className="text-xs text-indigo-400"
              >
                <KeyRound className="w-3.5 h-3.5 mr-1" />
                Use Backup Code
              </GlassButton>

              <GlassButton
                variant="primary"
                size="sm"
                type="button"
                disabled={isLoading || digits.join("").length !== 6 || success}
                onClick={() => verifyCode(digits.join(""))}
              >
                {isLoading ? "Verifying..." : "Confirm & Save"}
              </GlassButton>
            </div>
          </div>
        ) : (
          <form onSubmit={handleBackupSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                8-Character Recovery Backup Code
              </label>
              <GlassInput
                value={backupCode}
                onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                placeholder="e.g. A1B2C3D4"
                maxLength={12}
                disabled={isLoading || success}
                className="text-center font-mono tracking-widest uppercase"
              />
            </div>

            <div className="flex items-center justify-between gap-3 pt-2">
              <GlassButton
                variant="ghost"
                size="sm"
                type="button"
                onClick={() => {
                  setIsBackupMode(false);
                  setError(null);
                }}
                className="text-xs text-indigo-400"
              >
                ← Authenticator Code
              </GlassButton>

              <GlassButton
                variant="primary"
                size="sm"
                type="submit"
                disabled={isLoading || !backupCode.trim() || success}
              >
                {isLoading ? "Verifying..." : "Use Backup Code"}
              </GlassButton>
            </div>
          </form>
        )}
      </div>
    </GlassModal>
  );
}
