"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { auth } from "@/lib/firebase-client";
import { setTwoFactorVerified } from "@/lib/api-client";

function TwoFactorChallengeForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get("from") || "/dashboard";

  const [digits, setDigits] = useState<string[]>(["", "", "", "", "", ""]);
  const [backupCode, setBackupCode] = useState("");
  const [isBackupMode, setIsBackupMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (!isBackupMode && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [isBackupMode]);

  const handleDigitChange = (index: number, value: string) => {
    if (value.length > 1) {
      // Handle paste in single box
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
          submitCode(pasted);
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
      submitCode(fullCode);
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
        submitCode(pasted);
      }
    }
  };

  const submitCode = async (codeToVerify: string) => {
    setIsLoading(true);
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      let token = "";
      if (auth.currentUser) {
        token = await auth.currentUser.getIdToken();
      }

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

      // Establish verified session state in storage and server cookie
      setTwoFactorVerified(true);
      await fetch("/api/auth/session", { method: "PATCH" });

      router.push(from);
      router.refresh();
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
    submitCode(backupCode.trim());
  };

  return (
    <div className="w-full max-w-md p-8 rounded-2xl bg-zinc-900/70 border border-zinc-800/80 shadow-2xl backdrop-blur-xl animate-fade-in">
      {/* Icon & Title */}
      <div className="text-center mb-8">
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner">
          <svg
            className="w-7 h-7"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Two-Factor Authentication</h1>
        <p className="text-sm text-zinc-400 mt-2">
          {isBackupMode
            ? "Enter one of your 8-character single-use recovery backup codes."
            : "Enter the 6-digit code from your authenticator app (Google Authenticator, Authy, etc.)."}
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-3">
          <svg
            className="w-5 h-5 shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>{error}</div>
        </div>
      )}

      {!isBackupMode ? (
        <div className="space-y-6">
          {/* 6-Digit PIN Inputs */}
          <div className="flex justify-between gap-2.5" onPaste={handlePaste}>
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
                disabled={isLoading}
                onChange={(e) => handleDigitChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                className="w-12 h-14 text-center text-xl font-bold rounded-xl bg-zinc-950/80 border border-zinc-800 text-white focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition shadow-inner"
              />
            ))}
          </div>

          <button
            type="button"
            disabled={isLoading || digits.join("").length !== 6}
            onClick={() => submitCode(digits.join(""))}
            className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 cursor-pointer"
          >
            {isLoading ? "Verifying Code..." : "Verify & Continue"}
          </button>
        </div>
      ) : (
        <form onSubmit={handleBackupSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-2">
              Recovery Backup Code
            </label>
            <input
              type="text"
              autoFocus
              value={backupCode}
              onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
              placeholder="e.g. A1B2C3D4"
              maxLength={12}
              className="w-full px-4 py-3 rounded-xl bg-zinc-950 border border-zinc-800 text-sm text-white font-mono tracking-widest text-center focus:outline-none focus:border-indigo-500 uppercase"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !backupCode.trim()}
            className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 cursor-pointer"
          >
            {isLoading ? "Verifying Backup Code..." : "Use Backup Code"}
          </button>
        </form>
      )}

      {/* Switch mode */}
      <div className="mt-6 pt-6 border-t border-zinc-800/80 text-center">
        <button
          type="button"
          onClick={() => {
            setIsBackupMode(!isBackupMode);
            setError(null);
          }}
          className="text-xs text-indigo-400 hover:text-indigo-300 transition underline underline-offset-4 cursor-pointer"
        >
          {isBackupMode
            ? "← Return to Authenticator App code"
            : "Lost your device? Use a single-use backup code"}
        </button>
      </div>
    </div>
  );
}

export default function TwoFactorChallengePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100 p-4 relative overflow-hidden">
      {/* Glow gradient backdrop */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <Suspense
        fallback={<div className="text-zinc-500 text-sm">Loading security challenge...</div>}
      >
        <TwoFactorChallengeForm />
      </Suspense>
    </div>
  );
}
