"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  type AuthError,
} from "firebase/auth";
import { auth, googleProvider, appleProvider } from "@/lib/firebase-client";
import { setTwoFactorVerified } from "@/lib/api-client";

/**
 * Firebase reports a missing/incorrect NEXT_PUBLIC_FIREBASE_API_KEY as
 * `auth/api-key-not-valid.-please-pass-a-valid-api-key.`, which reads like a bug
 * to users. Name the actual cause instead.
 */
function friendlyAuthMessage(err: AuthError, fallback: string): string {
  const code = err.code || "";
  const msg = err.message || "";
  if (code.includes("api-key-not-valid") || code.includes("invalid-api-key")) {
    return "Sign-in is unavailable: this deployment is missing a valid Firebase API key (NEXT_PUBLIC_FIREBASE_API_KEY). Contact your administrator.";
  }
  if (
    code.includes("requests-to-this-api") ||
    code.includes("blocked") ||
    msg.includes("identitytoolkit")
  ) {
    return "Firebase Authentication is blocked on this API key (Identity Toolkit API not enabled on key). Please enable 'Identity Toolkit API' in Google Cloud Console or use the Firebase Web API Key.";
  }
  if (code.includes("operation-not-allowed") || msg.includes("operation-not-allowed")) {
    return "Sign-in with Apple is currently not enabled in your Firebase project. Please enable Apple under Firebase Console > Authentication > Sign-in method, or continue with Google / Email.";
  }
  if (code.includes("unauthorized-domain") || msg.includes("unauthorized-domain")) {
    return "This domain (localhost) is not in the list of authorized domains in Firebase Console > Authentication > Settings > Authorized domains.";
  }
  if (code.includes("user-not-found") || code.includes("wrong-password") || code.includes("invalid-credential")) {
    return "Invalid email or password. Please verify your credentials or create a new account.";
  }
  if (code.includes("email-already-in-use")) {
    return "An account with this email address already exists. Please switch to Sign In.";
  }
  if (code.includes("weak-password")) {
    return "Password is too weak. Please use at least 6 characters.";
  }
  if (code.includes("popup-blocked")) {
    return "The sign-in popup was blocked by your browser. Please allow popups for this site and try again.";
  }
  return err.message || fallback;
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get("from") || "/dashboard";

  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isAppleLoading, setIsAppleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const syncSessionAndBootstrap = async (idToken: string): Promise<boolean> => {
    if (!idToken) return false;

    // 1. Establish httpOnly session cookie
    await fetch("/api/auth/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken }),
    }).catch(() => {});

    // 2. Call backend /profiles/bootstrap to ensure profile row + role exists
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const bootstrapRes = await fetch(`${apiUrl}/profiles/bootstrap`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!bootstrapRes.ok && bootstrapRes.status === 403) {
        const data = await bootstrapRes.json();
        throw new Error(data.detail || "Access denied. Registration is by invitation only.");
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes("invitation only")) {
        throw err;
      }
    }

    // 3. Check 2FA status
    try {
      const statusRes = await fetch(`${apiUrl}/auth/2fa/status`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        if (statusData.is_enabled) {
          return true;
        }
      }
    } catch {
      // Quiet 2FA check
    }

    return false;
  };

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setErrorMessage(null);
    try {
      const userCredential = await signInWithPopup(auth, googleProvider);
      const idToken = await userCredential.user.getIdToken();
      const requires2FA = await syncSessionAndBootstrap(idToken);
      if (requires2FA) {
        router.push(`/login/2fa?from=${encodeURIComponent(from)}`);
      } else {
        setTwoFactorVerified(true);
        router.push(from);
      }
      router.refresh();
    } catch (err: unknown) {
      const authErr = err as AuthError;
      if (authErr.code === "auth/popup-closed-by-user") {
        setErrorMessage("Sign-in cancelled. Please complete the Google popup.");
      } else if (authErr.code === "auth/cancelled-popup-request") {
        setErrorMessage("Only one sign-in window can be open at a time.");
      } else {
        setErrorMessage(
          friendlyAuthMessage(
            authErr,
            "Failed to sign in with Google. Please check your connection.",
          ),
        );
      }
    } finally {
      setIsGoogleLoading(false);
    }
  };

  const handleAppleSignIn = async () => {
    setIsAppleLoading(true);
    setErrorMessage(null);
    try {
      const userCredential = await signInWithPopup(auth, appleProvider);
      const idToken = await userCredential.user.getIdToken();
      const requires2FA = await syncSessionAndBootstrap(idToken);
      if (requires2FA) {
        router.push(`/login/2fa?from=${encodeURIComponent(from)}`);
      } else {
        setTwoFactorVerified(true);
        router.push(from);
      }
      router.refresh();
    } catch (err: unknown) {
      const authErr = err as AuthError;
      if (authErr.code === "auth/popup-closed-by-user") {
        setErrorMessage("Sign-in cancelled. Please complete the Apple login popup.");
      } else if (authErr.code === "auth/cancelled-popup-request") {
        setErrorMessage("Only one sign-in window can be open at a time.");
      } else {
        setErrorMessage(
          friendlyAuthMessage(
            authErr,
            "Failed to sign in with Apple. Please check your connection.",
          ),
        );
      }
    } finally {
      setIsAppleLoading(false);
    }
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      let userCredential;
      if (mode === "signin") {
        userCredential = await signInWithEmailAndPassword(auth, email, password);
      } else {
        userCredential = await createUserWithEmailAndPassword(auth, email, password);
      }

      const idToken = await userCredential.user.getIdToken();
      const requires2FA = await syncSessionAndBootstrap(idToken);
      if (requires2FA) {
        router.push(`/login/2fa?from=${encodeURIComponent(from)}`);
      } else {
        setTwoFactorVerified(true);
        router.push(from);
      }
      router.refresh();
    } catch (err: unknown) {
      const authErr = err as AuthError;
      switch (authErr.code) {
        case "auth/invalid-credential":
        case "auth/wrong-password":
        case "auth/user-not-found":
          setErrorMessage("Invalid email or password. Please try again.");
          break;
        case "auth/email-already-in-use":
          setErrorMessage("An account already exists with this email. Switch to Sign In.");
          break;
        case "auth/weak-password":
          setErrorMessage("Password must be at least 6 characters.");
          break;
        case "auth/invalid-email":
          setErrorMessage("Please provide a valid email address.");
          break;
        default:
          setErrorMessage(friendlyAuthMessage(authErr, "Authentication failed. Please try again."));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl">
      {/* Error Banner */}
      {errorMessage && (
        <div
          role="alert"
          className="mb-6 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-sm text-rose-300"
        >
          {errorMessage}
        </div>
      )}

      {/* OAuth Actions */}
      <div className="space-y-3">
        {/* Google Sign-In */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={isGoogleLoading || isAppleLoading || isLoading}
          className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-700 bg-slate-800/90 px-4 py-3 text-sm font-semibold text-white transition-all hover:border-slate-600 hover:bg-slate-700/80 focus:ring-2 focus:ring-emerald-500/50 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isGoogleLoading ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
          ) : (
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path
                fill="#EA4335"
                d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
              />
              <path
                fill="#4285F4"
                d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
              />
              <path
                fill="#FBBC05"
                d="M5.6 14.8c-.3-.8-.4-1.8-.4-2.8s.1-2 .4-2.8L1.9 6.3C.7 8.7 0 10.3 0 12s.7 3.3 1.9 5.7l3.7-2.9z"
              />
              <path
                fill="#34A853"
                d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"
              />
            </svg>
          )}
          <span>Continue with Google</span>
        </button>

        {/* Apple Sign-In */}
        <button
          type="button"
          onClick={handleAppleSignIn}
          disabled={isGoogleLoading || isAppleLoading || isLoading}
          className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-700 bg-slate-800/90 px-4 py-3 text-sm font-semibold text-white transition-all hover:border-slate-600 hover:bg-slate-700/80 focus:ring-2 focus:ring-emerald-500/50 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isAppleLoading ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-transparent" />
          ) : (
            <svg className="h-5 w-5 fill-current" viewBox="0 0 24 24">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.61-.75 1.04-1.8 0.92-2.87-.9.04-2.02.6-2.66 1.34-.56.65-1.06 1.71-.93 2.74 1.02.08 2.05-.51 2.67-1.21z" />
            </svg>
          )}
          <span>Continue with Apple</span>
        </button>
      </div>

      {/* Divider */}
      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-800" />
        <span className="text-xs font-semibold tracking-wider text-slate-500 uppercase">
          or continue with email
        </span>
        <div className="h-px flex-1 bg-slate-800" />
      </div>

      {/* Mode Switcher */}
      <div className="mb-6 flex rounded-xl bg-slate-950/60 p-1 border border-slate-800/80">
        <button
          type="button"
          onClick={() => {
            setMode("signin");
            setErrorMessage(null);
          }}
          className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition-all ${
            mode === "signin"
              ? "bg-slate-800 text-white shadow-sm"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("signup");
            setErrorMessage(null);
          }}
          className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition-all ${
            mode === "signup"
              ? "bg-slate-800 text-white shadow-sm"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Create Account
        </button>
      </div>

      {/* Email / Password Form */}
      <form onSubmit={handleEmailSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-xs font-medium text-slate-300">
            Email Address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@wareflow.com"
            className="mt-1.5 block w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
          />
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="block text-xs font-medium text-slate-300">
              Password
            </label>
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="mt-1.5 block w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || isGoogleLoading}
          className="mt-2 flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 py-3 text-sm font-semibold text-slate-950 shadow-md shadow-emerald-500/20 transition-all hover:brightness-110 focus:ring-2 focus:ring-emerald-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
          ) : mode === "signin" ? (
            "Sign In with Email"
          ) : (
            "Create Staff Account"
          )}
        </button>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 text-slate-100 selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Background glow effects */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-emerald-600/15 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-indigo-600/15 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Brand Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 font-black text-slate-950 shadow-lg shadow-emerald-500/20">
            W
          </div>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-white">WareFlow</h1>
          <p className="mt-1 text-sm text-slate-400">
            Wholesale Distribution & Inventory Intelligence
          </p>
        </div>

        <Suspense
          fallback={
            <div className="flex h-96 w-full items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/80">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
            </div>
          }
        >
          <LoginForm />
        </Suspense>

        {/* Footer info */}
        <p className="mt-6 text-center text-xs text-slate-500">
          Protected by Firebase Enterprise Auth • Role permissions enforced server-side
        </p>
      </div>
    </div>
  );
}
