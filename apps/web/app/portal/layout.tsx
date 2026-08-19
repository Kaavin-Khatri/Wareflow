"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { auth } from "@/lib/firebase-client";
import { onAuthStateChanged, signOut } from "firebase/auth";

interface RetailerProfile {
  id: string;
  email: string;
  retailer_id: string;
  retailer_name: string;
  pricing_tier: string;
  credit_limit: number;
  credit_balance: number;
}

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/portal/login";
  const [profile, setProfile] = useState<RetailerProfile | null>(null);
  const [isLoading, setIsLoading] = useState(!isLoginPage);

  useEffect(() => {
    if (isLoginPage) {
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        router.push(`/portal/login?from=${encodeURIComponent(pathname)}`);
        return;
      }

      try {
        const idToken = await user.getIdToken();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/portal/me`, {
          headers: {
            Authorization: `Bearer ${idToken}`,
          },
        });

        if (res.ok) {
          const data = await res.json();
          setProfile(data);
        } else if (res.status === 403) {
          // If staff account accidentally visits /portal, redirect to /admin or logout
          const errData = await res.json().catch(() => ({}));
          if (String(errData.detail || "").includes("Staff")) {
            router.push("/dashboard");
          } else {
            router.push("/portal/login?error=inactive");
          }
        }
      } catch (err) {
        console.warn("Error fetching portal profile:", err);
      } finally {
        setIsLoading(false);
      }
    });

    return () => unsubscribe();
  }, [isLoginPage, pathname, router]);

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      await fetch("/api/auth/session", { method: "DELETE" });
      router.push("/portal/login");
    } catch (err) {
      console.error("Sign out error:", err);
    }
  };

  if (isLoginPage) {
    return <main className="min-h-screen">{children}</main>;
  }

  const availableCredit = profile ? Math.max(0, profile.credit_limit - profile.credit_balance) : 0;

  const navItems = [
    { name: "Catalog", href: "/portal/catalog", icon: "📦" },
    { name: "My Orders", href: "/portal/orders", icon: "📋" },
    { name: "Invoices & Ledger", href: "/portal/invoices", icon: "🧾" },
    { name: "Appearance", href: "/portal/settings/appearance", icon: "🎨" },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Glass Navbar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-900/80 backdrop-blur-xl transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Portal Badge */}
          <div className="flex items-center gap-3">
            <Link href="/portal/catalog" className="flex items-center gap-2 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <span className="font-bold text-white tracking-wider text-base">W</span>
              </div>
              <span className="font-bold text-lg text-white tracking-tight">WareFlow</span>
            </Link>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
              Retailer Portal
            </span>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? "bg-white/10 text-white shadow-sm border border-white/15"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Header Area: Credit line & Account */}
          <div className="flex items-center gap-4">
            {profile && (
              <div className="hidden sm:flex flex-col items-end px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs">
                <div className="flex items-center gap-1.5 font-semibold text-slate-300">
                  <span>{profile.retailer_name}</span>
                  <span className="capitalize px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] border border-amber-500/30">
                    {profile.pricing_tier}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-slate-400">
                  <span>Available Credit:</span>
                  <span className="font-mono font-medium text-emerald-400">
                    ₹{availableCredit.toLocaleString("en-IN")}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    (₹{profile.credit_limit.toLocaleString("en-IN")})
                  </span>
                </div>
              </div>
            )}

            <button
              onClick={handleSignOut}
              className="px-3 py-1.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-xs text-slate-300 hover:text-white transition-all"
              title="Sign Out"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {isLoading ? (
          <div className="flex items-center justify-center min-h-[50vh]">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          </div>
        ) : (
          children
        )}
      </main>
    </div>
  );
}
