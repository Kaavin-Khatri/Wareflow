"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import AppLayout from "@/components/AppLayout";
import { apiClient } from "@/lib/api-client";

interface TwoFactorStatus {
  is_enabled: boolean;
  is_required: boolean;
  enrolled_at: string | null;
  remaining_backup_codes: number;
}

interface TwoFactorEnrollData {
  secret: string;
  qr_code_data_url: string;
  backup_codes: string[];
}

export default function SecuritySettingsPage() {
  const [status, setStatus] = useState<TwoFactorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Setup Wizard State
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [enrollData, setEnrollData] = useState<TwoFactorEnrollData | null>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [enrollingStep, setEnrollingStep] = useState<1 | 2>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);

  // Disable 2FA State
  const [isDisabling, setIsDisabling] = useState(false);
  const [disableCode, setDisableCode] = useState("");

  // Regenerate Backup Codes State
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenCode, setRegenCode] = useState("");
  const [newBackupCodes, setNewBackupCodes] = useState<string[] | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<TwoFactorStatus>("/auth/2fa/status");
      setStatus(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load 2FA security status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const data = await apiClient.get<TwoFactorStatus>("/auth/2fa/status");
        if (!ignore) setStatus(data);
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load 2FA status.");
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, []);

  const handleStartEnrollment = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const data = await apiClient.post<TwoFactorEnrollData>("/auth/2fa/enroll", {});
      setEnrollData(data);
      setIsEnrolling(true);
      setEnrollingStep(1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate 2FA enrollment.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyCode.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const updatedStatus = await apiClient.post<TwoFactorStatus>("/auth/2fa/verify-enrollment", {
        code: verifyCode.trim(),
      });
      setStatus(updatedStatus);
      setIsEnrolling(false);
      setEnrollData(null);
      setVerifyCode("");
      setSuccessMessage("Two-factor authentication has been successfully enabled!");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid code. Check your authenticator app.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisable2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!disableCode.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const updatedStatus = await apiClient.post<TwoFactorStatus>("/auth/2fa/disable", {
        code: disableCode.trim(),
      });
      setStatus(updatedStatus);
      setIsDisabling(false);
      setDisableCode("");
      setSuccessMessage("Two-factor authentication has been disabled.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid verification code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegenerateCodes = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regenCode.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const codes = await apiClient.post<string[]>("/auth/2fa/regenerate-backup-codes", {
        code: regenCode.trim(),
      });
      setNewBackupCodes(codes);
      setRegenCode("");
      await fetchStatus();
      setSuccessMessage("10 new recovery backup codes generated.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to regenerate backup codes.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = (text: string, type: "key" | "codes") => {
    navigator.clipboard.writeText(text);
    if (type === "key") {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    } else {
      setCopiedCodes(true);
      setTimeout(() => setCopiedCodes(false), 2000);
    }
  };

  const downloadCodesAsText = (codes: string[]) => {
    const text = `WAREFLOW 2FA RECOVERY BACKUP CODES\nGenerated: ${new Date().toISOString()}\n\nEach code can be used exactly once:\n\n${codes.join("\n")}\n\nKeep these in a secure place.`;
    const element = document.createElement("a");
    const file = new Blob([text], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "wareflow-2fa-backup-codes.txt";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <AppLayout>
      <div className="space-y-8 max-w-5xl">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Security & Authentication
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Protect your account and wholesale financial data with multi-factor authentication.
          </p>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg
                className="w-5 h-5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>{successMessage}</span>
            </div>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-xs text-emerald-400/80 hover:text-emerald-300 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg
                className="w-5 h-5 shrink-0"
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
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-xs text-red-400/80 hover:text-red-300 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {loading ? (
          <div className="p-12 text-center text-zinc-500 text-sm animate-pulse">
            Loading security status...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Primary Status Card */}
            <div className="md:col-span-2 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 p-6 space-y-6 backdrop-blur-sm shadow-xl">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">
                    Two-Factor Authentication (TOTP)
                  </h2>
                  <p className="text-xs text-zinc-400 mt-1">
                    Adds an extra layer of protection using standard RFC 6238 time-based
                    authenticator apps.
                  </p>
                </div>
                {status?.is_enabled ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-zinc-400 text-xs font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
                    Disabled
                  </span>
                )}
              </div>

              {/* Status Details */}
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800/80 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-zinc-400">Policy Requirement:</span>
                  <span className="font-medium text-white">
                    {status?.is_required ? (
                      <span className="text-amber-400 font-semibold">Mandatory for your role</span>
                    ) : (
                      "Optional (Operational role)"
                    )}
                  </span>
                </div>
                {status?.is_enabled && status?.enrolled_at && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-400">Enrolled On:</span>
                    <span className="font-mono text-zinc-300">
                      {new Date(status.enrolled_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                  </div>
                )}
                {status?.is_enabled && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-400">Active Recovery Codes:</span>
                    <span className="font-semibold text-indigo-400">
                      {status.remaining_backup_codes} of 10 available
                    </span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3 pt-2">
                {!status?.is_enabled ? (
                  <button
                    onClick={handleStartEnrollment}
                    disabled={isSubmitting}
                    className="py-2.5 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition shadow-lg shadow-indigo-600/30 flex items-center gap-2 cursor-pointer"
                  >
                    {isSubmitting ? "Setting Up..." : "Set Up 2FA"}
                  </button>
                ) : (
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      onClick={() => {
                        setIsRegenerating(true);
                        setNewBackupCodes(null);
                        setError(null);
                      }}
                      className="py-2 px-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-medium transition cursor-pointer"
                    >
                      Regenerate Backup Codes
                    </button>
                    <button
                      onClick={() => {
                        setIsDisabling(true);
                        setError(null);
                      }}
                      className="py-2 px-4 rounded-xl bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 text-xs font-medium transition cursor-pointer"
                    >
                      Disable 2FA
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Role Policy Info Box */}
            <div className="rounded-2xl bg-zinc-900/60 border border-zinc-800/80 p-6 space-y-4 backdrop-blur-sm">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-white">Enforcement Rules</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Roles with financial and administrative permissions (Owner, Manager, Accountant) are
                required to maintain active 2FA.
              </p>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Warehouse Staff and Sales Staff are exempt by default for rapid shop-floor order
                scanning.
              </p>
            </div>
          </div>
        )}

        {/* Setup Wizard Modal */}
        {isEnrolling && enrollData && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="w-full max-w-lg rounded-2xl bg-zinc-900 border border-zinc-800 p-6 space-y-6 shadow-2xl">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4">
                <h3 className="text-base font-bold text-white">
                  {enrollingStep === 1
                    ? "Step 1 of 2: Scan QR & Save Backup Codes"
                    : "Step 2 of 2: Confirm 6-Digit Code"}
                </h3>
                <button
                  onClick={() => setIsEnrolling(false)}
                  className="text-zinc-500 hover:text-white text-sm"
                >
                  ✕
                </button>
              </div>

              {enrollingStep === 1 ? (
                <div className="space-y-5">
                  <div className="flex flex-col sm:flex-row items-center gap-6 p-4 rounded-xl bg-zinc-950 border border-zinc-800">
                    <div className="w-40 h-40 bg-white p-2 rounded-xl shrink-0 flex items-center justify-center">
                      <Image
                        src={enrollData.qr_code_data_url}
                        alt="2FA QR Code"
                        width={160}
                        height={160}
                        unoptimized
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <div className="space-y-2 text-center sm:text-left">
                      <p className="text-xs text-zinc-300 font-medium">
                        Scan with your Authenticator app
                      </p>
                      <p className="text-[11px] text-zinc-500">
                        Compatible with Google Authenticator, Authy, Microsoft Authenticator, or
                        1Password.
                      </p>
                      <div className="pt-1">
                        <span className="text-[10px] text-zinc-400 block mb-1">
                          Manual entry secret:
                        </span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(enrollData.secret, "key")}
                          className="font-mono text-xs bg-zinc-900 hover:bg-zinc-800 text-indigo-300 px-2.5 py-1.5 rounded-lg border border-zinc-800 transition flex items-center gap-1.5 cursor-pointer mx-auto sm:mx-0"
                        >
                          {copiedKey ? "Copied!" : enrollData.secret}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Backup Codes Download Box */}
                  <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold text-zinc-200">Recovery Backup Codes</h4>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            copyToClipboard(enrollData.backup_codes.join("\n"), "codes")
                          }
                          className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer"
                        >
                          {copiedCodes ? "Copied All!" : "Copy"}
                        </button>
                        <span className="text-zinc-600">•</span>
                        <button
                          type="button"
                          onClick={() => downloadCodesAsText(enrollData.backup_codes)}
                          className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer"
                        >
                          Download .txt
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {enrollData.backup_codes.map((c, i) => (
                        <div
                          key={i}
                          className="font-mono text-xs text-zinc-300 bg-zinc-900 px-2.5 py-1 rounded text-center"
                        >
                          {c}
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setEnrollingStep(2)}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition cursor-pointer"
                  >
                    Next: Verify Code →
                  </button>
                </div>
              ) : (
                <form onSubmit={handleConfirmEnrollment} className="space-y-5">
                  <p className="text-xs text-zinc-400">
                    Enter the 6-digit code currently shown in your authenticator app to finalize
                    setup.
                  </p>
                  <div>
                    <input
                      type="text"
                      autoFocus
                      inputMode="numeric"
                      maxLength={6}
                      value={verifyCode}
                      onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
                      placeholder="123456"
                      className="w-full py-3 px-4 rounded-xl bg-zinc-950 border border-zinc-800 text-center font-mono text-2xl font-bold tracking-widest text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setEnrollingStep(1)}
                      className="w-1/3 py-2.5 px-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-medium transition cursor-pointer"
                    >
                      ← Back
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting || verifyCode.length !== 6}
                      className="w-2/3 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition shadow-lg shadow-indigo-600/30 cursor-pointer"
                    >
                      {isSubmitting ? "Activating..." : "Activate 2FA"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Regenerate Backup Codes Modal */}
        {isRegenerating && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="w-full max-w-md rounded-2xl bg-zinc-900 border border-zinc-800 p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
                <h3 className="text-base font-bold text-white">Regenerate Backup Codes</h3>
                <button
                  onClick={() => setIsRegenerating(false)}
                  className="text-zinc-500 hover:text-white text-sm"
                >
                  ✕
                </button>
              </div>

              {!newBackupCodes ? (
                <form onSubmit={handleRegenerateCodes} className="space-y-4">
                  <p className="text-xs text-zinc-400">
                    Enter your 6-digit TOTP code to generate 10 fresh single-use backup recovery
                    codes. All previous backup codes will be revoked immediately.
                  </p>
                  <input
                    type="text"
                    autoFocus
                    maxLength={6}
                    value={regenCode}
                    onChange={(e) => setRegenCode(e.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                    className="w-full py-2.5 px-4 rounded-xl bg-zinc-950 border border-zinc-800 text-center font-mono text-lg font-bold tracking-widest text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    type="submit"
                    disabled={isSubmitting || regenCode.length !== 6}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium transition cursor-pointer"
                  >
                    {isSubmitting ? "Generating..." : "Generate 10 New Codes"}
                  </button>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-emerald-400">
                        New Recovery Codes
                      </span>
                      <button
                        type="button"
                        onClick={() => downloadCodesAsText(newBackupCodes)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
                      >
                        Download .txt
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {newBackupCodes.map((c, i) => (
                        <div
                          key={i}
                          className="font-mono text-xs text-zinc-300 bg-zinc-900 px-2.5 py-1 rounded text-center"
                        >
                          {c}
                        </div>
                      ))}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsRegenerating(false)}
                    className="w-full py-2.5 px-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-medium transition cursor-pointer"
                  >
                    Done
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Disable 2FA Modal */}
        {isDisabling && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="w-full max-w-md rounded-2xl bg-zinc-900 border border-zinc-800 p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
                <h3 className="text-base font-bold text-white">
                  Disable Two-Factor Authentication
                </h3>
                <button
                  onClick={() => setIsDisabling(false)}
                  className="text-zinc-500 hover:text-white text-sm"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleDisable2FA} className="space-y-4">
                <p className="text-xs text-amber-400/90 leading-relaxed">
                  ⚠️ Disabling 2FA removes extra security from your account. Enter your current
                  6-digit code or recovery backup code to confirm.
                </p>
                <input
                  type="text"
                  autoFocus
                  maxLength={12}
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value.toUpperCase())}
                  placeholder="6-digit code or backup code"
                  className="w-full py-2.5 px-4 rounded-xl bg-zinc-950 border border-zinc-800 text-center font-mono text-sm tracking-widest text-white focus:outline-none focus:border-red-500 uppercase"
                />
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setIsDisabling(false)}
                    className="w-1/2 py-2.5 px-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-medium transition cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !disableCode.trim()}
                    className="w-1/2 py-2.5 px-4 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium transition cursor-pointer"
                  >
                    {isSubmitting ? "Disabling..." : "Confirm Disable"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
