"use client";

import React, { useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/lib/utils";
import { SPRING_PRESETS } from "../motion/MotionProvider";

export interface GlassModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  maxWidth?: "sm" | "md" | "lg" | "xl";
}

const maxWidthMap = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
};

export function GlassModal({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
  maxWidth = "lg",
}: GlassModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop Blur Layer */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            aria-hidden="true"
            className="fixed inset-0 bg-black/60 backdrop-blur-md cursor-pointer"
          />

          {/* Modal Dialog Card with Specular Refraction */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={SPRING_PRESETS.glassMorph}
            role="dialog"
            aria-modal="true"
            className={cn(
              "relative w-full rounded-3xl bg-[var(--glass-bg-elevated)] backdrop-blur-2xl border border-[var(--glass-border)] shadow-2xl p-6 space-y-5 overflow-hidden z-10",
              maxWidthMap[maxWidth],
              className,
            )}
          >
            {/* Top Specular Sheen */}
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-[1.5px] bg-[var(--glass-highlight)] pointer-events-none"
            />

            {/* Header */}
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3.5">
              <div className="space-y-0.5 pr-6">
                <h3 className="text-base font-bold text-[var(--text)] tracking-tight">{title}</h3>
                {description && (
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">{description}</p>
                )}
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close dialog"
                className="w-7 h-7 rounded-lg glass-button-secondary flex items-center justify-center text-xs text-[var(--text-muted)] hover:text-[var(--text)] cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Body */}
            <div className="relative z-10">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
