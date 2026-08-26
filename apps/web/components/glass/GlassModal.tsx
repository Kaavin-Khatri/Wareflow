"use client";

import React, { useEffect, useId, useState } from "react";
import { createPortal } from "react-dom";
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
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl";
}

const maxWidthMap = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
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
  const [mounted, setMounted] = useState(() => typeof window !== "undefined");
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Lock background body scroll when modal is active
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <div
          data-testid="glass-modal-portal"
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
        >
          {/* Backdrop Blur Layer */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            aria-hidden="true"
            className="fixed inset-0 bg-black/75 backdrop-blur-md cursor-pointer z-0"
          />

          {/* Modal Dialog Card with Specular Refraction */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={SPRING_PRESETS.glassMorph}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={description ? descId : undefined}
            className={cn(
              "relative w-full rounded-3xl bg-[var(--surface-elevated)] backdrop-blur-2xl border border-[var(--glass-border)] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.7)] p-6 space-y-5 my-auto z-10 max-h-[90vh] overflow-y-auto",
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
                <h3 id={titleId} className="text-base font-bold text-[var(--text)] tracking-tight">
                  {title}
                </h3>
                {description && (
                  <p id={descId} className="text-xs text-[var(--text-muted)] leading-relaxed">
                    {description}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close dialog"
                className="w-7 h-7 rounded-lg glass-button-secondary flex items-center justify-center text-xs text-[var(--text-muted)] hover:text-[var(--text)] focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:outline-none cursor-pointer transition-colors"
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

  if (process.env.NODE_ENV !== "test" && typeof document !== "undefined" && document.body) {
    return createPortal(modalContent, document.body);
  }
  return modalContent;
}
