import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import GradientBackdrop from "@/components/GradientBackdrop";
import { MotionProvider } from "@/components/motion/MotionProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WareFlow — Wholesale Inventory & ERP",
  description: "AI-assisted wholesale inventory, order processing, and distribution ERP platform.",
};

const themeScript = `
  (function() {
    try {
      var saved = localStorage.getItem('wareflow-theme');
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      var isDark = saved === 'dark' || (!saved && prefersDark) || (saved === 'system' && prefersDark);
      if (isDark) {
        document.documentElement.classList.add('dark');
        document.documentElement.style.colorScheme = 'dark';
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.style.colorScheme = 'light';
      }

      var savedAccent = localStorage.getItem('wareflow-accent');
      var accents = {
        violet: { light: { a: '#7c3aed', h: '#6d28d9', s: 'rgba(124,58,237,0.08)', b: 'rgba(124,58,237,0.28)', g: 'rgba(124,58,237,0.35)' }, dark: { a: '#8b5cf6', h: '#a78bfa', s: 'rgba(139,92,246,0.12)', b: 'rgba(139,92,246,0.32)', g: 'rgba(139,92,246,0.45)' } },
        indigo: { light: { a: '#4f46e5', h: '#4338ca', s: 'rgba(79,70,229,0.08)', b: 'rgba(79,70,229,0.28)', g: 'rgba(79,70,229,0.35)' }, dark: { a: '#6366f1', h: '#818cf8', s: 'rgba(99,102,241,0.12)', b: 'rgba(99,102,241,0.32)', g: 'rgba(99,102,241,0.45)' } },
        emerald: { light: { a: '#059669', h: '#047857', s: 'rgba(5,150,105,0.08)', b: 'rgba(5,150,105,0.28)', g: 'rgba(5,150,105,0.35)' }, dark: { a: '#10b981', h: '#34d399', s: 'rgba(16,185,129,0.12)', b: 'rgba(16,185,129,0.32)', g: 'rgba(16,185,129,0.45)' } },
        cyan: { light: { a: '#0891b2', h: '#0e7490', s: 'rgba(8,145,178,0.08)', b: 'rgba(8,145,178,0.28)', g: 'rgba(8,145,178,0.35)' }, dark: { a: '#06b6d4', h: '#22d3ee', s: 'rgba(6,182,212,0.12)', b: 'rgba(6,182,212,0.32)', g: 'rgba(6,182,212,0.45)' } },
        rose: { light: { a: '#e11d48', h: '#be123c', s: 'rgba(225,29,72,0.08)', b: 'rgba(225,29,72,0.28)', g: 'rgba(225,29,72,0.35)' }, dark: { a: '#f43f5e', h: '#fb7185', s: 'rgba(244,63,94,0.12)', b: 'rgba(244,63,94,0.32)', g: 'rgba(244,63,94,0.45)' } },
        amber: { light: { a: '#d97706', h: '#b45309', s: 'rgba(217,119,6,0.08)', b: 'rgba(217,119,6,0.28)', g: 'rgba(217,119,6,0.35)' }, dark: { a: '#f59e0b', h: '#fbbf24', s: 'rgba(245,158,11,0.12)', b: 'rgba(245,158,11,0.32)', g: 'rgba(245,158,11,0.45)' } },
        cobalt: { light: { a: '#2563eb', h: '#1d4ed8', s: 'rgba(37,99,235,0.08)', b: 'rgba(37,99,235,0.28)', g: 'rgba(37,99,235,0.35)' }, dark: { a: '#3b82f6', h: '#60a5fa', s: 'rgba(59,130,246,0.12)', b: 'rgba(59,130,246,0.32)', g: 'rgba(59,130,246,0.45)' } }
      };
      var chosen = accents[savedAccent] || accents.violet;
      var cur = isDark ? chosen.dark : chosen.light;
      var root = document.documentElement;
      root.style.setProperty('--accent', cur.a);
      root.style.setProperty('--accent-hover', cur.h);
      root.style.setProperty('--accent-subtle', cur.s);
      root.style.setProperty('--accent-border', cur.b);
      root.style.setProperty('--accent-glow', cur.g);
    } catch (e) {}
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full flex flex-col font-sans bg-[var(--bg)] text-[var(--text)] transition-colors duration-300">
        <ThemeProvider>
          <MotionProvider>
            <GradientBackdrop />
            {children}
          </MotionProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
