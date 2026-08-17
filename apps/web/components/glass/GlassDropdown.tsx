"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/lib/utils";
import { SPRING_PRESETS } from "../motion/MotionProvider";

export interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  destructive?: boolean;
  onClick: () => void;
}

export interface GlassDropdownProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: "left" | "right";
  className?: string;
}

export function GlassDropdown({ trigger, items, align = "right", className }: GlassDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} className="relative inline-block text-left">
      <div onClick={() => setIsOpen(!isOpen)} className="cursor-pointer">
        {trigger}
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={SPRING_PRESETS.snappy}
            className={cn(
              "absolute z-50 mt-2 min-w-[180px] rounded-2xl bg-[var(--glass-bg-elevated)] backdrop-blur-2xl border border-[var(--glass-border)] shadow-xl p-1.5 space-y-0.5 overflow-hidden",
              align === "right" ? "right-0" : "left-0",
              className,
            )}
          >
            {/* Top Specular Sheen */}
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-[1px] bg-[var(--glass-highlight)] pointer-events-none"
            />

            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  item.onClick();
                  setIsOpen(false);
                }}
                className={cn(
                  "w-full flex items-center gap-2.5 px-3 py-2 text-xs rounded-xl font-medium transition cursor-pointer text-left",
                  item.destructive
                    ? "text-rose-400 hover:bg-rose-500/10"
                    : "text-[var(--text)] hover:bg-[var(--surface-hover)]",
                )}
              >
                {item.icon && <span className="w-4 h-4 shrink-0">{item.icon}</span>}
                <span className="flex-1 truncate">{item.label}</span>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
