"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  type AuthError,
} from "firebase/auth";
import { auth, googleProvider } from "@/lib/firebase-client";

function PortalLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get("from") || "/portal/catalog";
  const inviteTokenFromUrl = searchParams.get("invite") || "";
  const emailFromUrl = searchParams.get("email") || "";

  const [mode, setMode] = useState<"signin" | "signup">(inviteTokenFromUrl ? "signup" : "signin");
  const [email, setEmail] = useState(emailFromUrl);
  const [password, setPassword] = useState("");
  const [inviteToken, setInviteToken] = useState(inviteTokenFromUrl);
  const [displayName, setDisplayName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const syncRetailerSession = async (idToken: string) => {
    // 1. Establish session cookie
    await fetch("/api/auth/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken }),
    });

    // 2. Call backend /portal/auth/bootstrap
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const bootstrapRes = await fetch(`${apiUrl}/portal/auth/bootstrap`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${idToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        invite_token: inviteToken || undefined,
        display_name: displayName || undefined,
      }),
    });

    if (!bootstrapRes.ok) {
      const data = await bootstrapRes.json().catch(() => ({}));
      const detail = data.detail || "Authentication failed.";
      if (bootstrapRes.status === 403 && String(detail).includes("Staff accounts")) {
        throw new Error(
          "Staff accounts cannot log in to the Retailer Portal. Please use the Staff Login at /login."
        );
      }
      throw new Error(detail);
    }

    return await bootstrapRes.json();
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      let userCred;
      if (mode === "signup") {
        userCred = await createUserWithEmailAndPassword(auth, email, password);
      } else {
        userCred = await signInWithEmailAndPassword(auth, email, password);
      }

      const idToken = await userCred.user.getIdToken();
      await syncRetailerSession(idToken);
      router.push(from);
      router.refresh();
    } catch (err: unknown) {
      const authErr = err as AuthError & { message?: string };
      if (authErr.code === "auth/user-not-found" || authErr.code === "auth/wrong-password" || authErr.code === "auth/invalid-credential") {
        setErrorMessage("Invalid email or password. Please try again.");
      } else if (authErr.code === "auth/email-already-in-use") {
        setErrorMessage("An account with this email already exists. Please sign in instead.");
        setMode("signin");
      } else if (authErr.code === "auth/weak-password") {
        setErrorMessage("Password must be at least 6 characters long.");
      } else {
        setErrorMessage(authErr.message || "Failed to authenticate. Please check your credentials.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setErrorMessage(null);

    try {
      const userCred = await signInWithPopup(auth, googleProvider);
      const idToken = await userCred.user.getIdToken();
      await syncRetailerSession(idToken);
      router.push(from);
      router.refresh();
    } catch (err: unknown) {
      const authErr = err as AuthError & { message?: string };
      if (authErr.code === "auth/popup-closed-by-user") {
        setErrorMessage("Sign-in cancelled. Please complete the Google popup.");
      } else {
        setErrorMessage(authErr.message || "Failed to sign in with Google.");
      }
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 rounded-3xl bg-slate-900/70 border border-white/10 backdrop-blur-2xl shadow-2xl shadow-indigo-950/40">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 mb-4 shadow-lg shadow-indigo-500/25">
          <span className="text-2xl font-black text-white tracking-wider">W</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Retailer Portal</h1>
        <p className="text-sm text-slate-400 mt-1">Wholesale Self-Service & Ordering</p>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="flex rounded-xl bg-white/5 p-1 mb-6 border border-white/10">
        <button
          type="button"
          onClick={() => setMode("signin")}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
            mode === "signin"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => setMode("signup")}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
            mode === "signup"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Accept Invite / Sign Up
        </button>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5">
          <span className="text-base leading-none">⚠️</span>
          <span className="flex-1">{errorMessage}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleEmailAuth} className="space-y-4">
        {mode === "signup" && (
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Invite Token
            </label>
            <input
              type="text"
              value={inviteToken}
              onChange={(e) => setInviteToken(e.target.value)}
              placeholder="e.g. inv_ab12cd34"
              className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
            />
          </div>
        )}

        {mode === "signup" && (
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Contact / Manager Name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Your Name"
              className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Business Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="retailer@business.com"
            className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-slate-300">Password</label>
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          <input
            type={showPassword ? "text" : "password"}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || isGoogleLoading}
          className="w-full mt-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <div className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
          ) : mode === "signup" ? (
            "Complete Account Setup"
          ) : (
            "Sign In to Portal"
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="flex items-center gap-3 my-6">
        <div className="flex-1 h-px bg-white/10" />
        <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">or</span>
        <div className="flex-1 h-px bg-white/10" />
      </div>

      {/* Google OAuth button */}
      <button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={isLoading || isGoogleLoading}
        className="w-full py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-200 hover:text-white text-xs font-semibold flex items-center justify-center gap-2.5 transition-all disabled:opacity-50"
      >
        {isGoogleLoading ? (
          <div className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
        ) : (
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#EA4335"
              d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
            />
            <path
              fill="#4285F4"
              d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
            />
            <path
              fill="#FBBC05"
              d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3 0-.8.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15.1s.7 5.4 1.9 7.8l3.7-2.9z"
            />
            <path
              fill="#34A853"
              d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16.5C3.7 20.2 7.5 23.5 12 23.5z"
            />
          </svg>
        )}
        <span>Sign in with Google</span>
      </button>

      {/* Staff cross-link reminder */}
      <div className="mt-8 text-center text-xs text-slate-500">
        Are you a WareFlow staff member?{" "}
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
          Go to Staff Login
        </Link>
      </div>
    </div>
  );
}

export default function PortalLoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/40 via-slate-950 to-slate-950">
      <Suspense fallback={<div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />}>
        <PortalLoginForm />
      </Suspense>
    </div>
  );
}
