"use client";

import React, { useState, useRef, useEffect, useId, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, RotateCcw, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { SPRING_PRESETS } from "../motion/MotionProvider";

export interface GlassDatePickerProps {
  value: string; // "YYYY-MM-DD"
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  minDate?: string;
  maxDate?: string;
  required?: boolean;
  className?: string;
  triggerClassName?: string;
  menuClassName?: string;
  size?: "sm" | "md" | "lg";
  id?: string;
  name?: string;
  "aria-label"?: string;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const WEEK_DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

function parseIsoDate(val: string): Date | null {
  if (!val) return null;
  const [y, m, d] = val.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

function formatIso(year: number, month: number, day: number): string {
  const mm = String(month + 1).padStart(2, "0");
  const dd = String(day).padStart(2, "0");
  return `${year}-${mm}-${dd}`;
}

function formatReadable(val: string): string {
  const dt = parseIsoDate(val);
  if (!dt) return "";
  const d = String(dt.getDate()).padStart(2, "0");
  const m = String(dt.getMonth() + 1).padStart(2, "0");
  const y = dt.getFullYear();
  return `${d}-${m}-${y}`;
}

export function GlassDatePicker({
  value,
  onChange,
  placeholder = "DD-MM-YYYY",
  disabled = false,
  minDate,
  maxDate,
  required,
  className,
  triggerClassName,
  menuClassName,
  size = "sm",
  id,
  name,
  "aria-label": ariaLabel,
}: GlassDatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const generatedId = useId();
  const datePickerId = id || generatedId;

  // Track the month and year currently displayed in the calendar
  const initialDate = useMemo(() => parseIsoDate(value) || new Date(), [value]);
  const [viewYear, setViewYear] = useState<number>(initialDate.getFullYear());
  const [viewMonth, setViewMonth] = useState<number>(initialDate.getMonth());

  // Sync view when opened or when value changes
  useEffect(() => {
    const dt = parseIsoDate(value);
    if (dt) {
      setViewYear(dt.getFullYear());
      setViewMonth(dt.getMonth());
    }
  }, [value, isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const handlePrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((prev) => prev - 1);
    } else {
      setViewMonth((prev) => prev - 1);
    }
  };

  const handleNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((prev) => prev + 1);
    } else {
      setViewMonth((prev) => prev + 1);
    }
  };

  const handleSelectDay = (day: number) => {
    const iso = formatIso(viewYear, viewMonth, day);
    onChange(iso);
    setIsOpen(false);
  };

  const handleSelectToday = () => {
    const today = new Date();
    const iso = formatIso(today.getFullYear(), today.getMonth(), today.getDate());
    onChange(iso);
    setViewYear(today.getFullYear());
    setViewMonth(today.getMonth());
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange("");
    setIsOpen(false);
  };

  // Compute days in month and offset
  const { daysInMonth, firstDayOfWeek, totalDaysPrevMonth } = useMemo(() => {
    const dim = new Date(viewYear, viewMonth + 1, 0).getDate();
    const fd = new Date(viewYear, viewMonth, 1).getDay();
    const tdpm = new Date(viewYear, viewMonth, 0).getDate();
    return { daysInMonth: dim, firstDayOfWeek: fd, totalDaysPrevMonth: tdpm };
  }, [viewYear, viewMonth]);

  const todayIso = useMemo(() => {
    const now = new Date();
    return formatIso(now.getFullYear(), now.getMonth(), now.getDate());
  }, []);

  const isDayDisabled = (day: number): boolean => {
    const iso = formatIso(viewYear, viewMonth, day);
    if (minDate && iso < minDate) return true;
    if (maxDate && iso > maxDate) return true;
    return false;
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs rounded-xl min-h-[34px]",
    md: "px-3.5 py-2 text-xs rounded-xl min-h-[38px]",
    lg: "px-4 py-2.5 text-sm rounded-xl min-h-[42px]",
  };

  const readableText = value ? formatReadable(value) : "";

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative inline-block w-full min-w-[140px] text-left select-none",
        isOpen ? "z-[60]" : "z-auto",
        className
      )}
    >
      {/* Hidden input for form and test compatibility */}
      <input
        type="hidden"
        id={datePickerId}
        name={name}
        value={value}
        required={required}
      />

      {/* Glass Trigger Button */}
      <button
        type="button"
        id={`${datePickerId}-trigger`}
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-label={ariaLabel || readableText || placeholder}
        className={cn(
          "w-full flex items-center justify-between gap-2 bg-[var(--surface)]/80 hover:bg-[var(--surface-hover)] border border-[var(--glass-border)] text-[var(--text)] transition-all duration-200 outline-none focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent-subtle)] focus-visible:shadow-[0_0_16px_-2px_var(--accent-glow)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed",
          sizeClasses[size],
          isOpen && "border-[var(--accent)] ring-2 ring-[var(--accent-subtle)] shadow-[0_0_16px_-2px_var(--accent-glow)]",
          triggerClassName
        )}
      >
        <span className="flex items-center gap-2 truncate font-mono text-xs">
          <CalendarIcon className="w-3.5 h-3.5 text-[var(--accent)] shrink-0" />
          <span className={cn("truncate", !readableText && "text-[var(--text-subtle)] font-sans")}>
            {readableText || placeholder}
          </span>
        </span>
        <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider bg-[var(--surface-hover)] px-1.5 py-0.5 rounded border border-[var(--border)]">
          Date
        </span>
      </button>

      {/* Popover Calendar */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -4 }}
            transition={SPRING_PRESETS.snappy}
            role="dialog"
            aria-label="Date Picker Calendar"
            className={cn(
              "absolute left-0 z-[100] mt-1.5 w-72 rounded-2xl bg-[var(--surface-elevated)] backdrop-blur-2xl border border-[var(--glass-border)] shadow-2xl p-3 space-y-3 overflow-hidden",
              menuClassName
            )}
          >
            {/* Top Specular Sheen */}
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-[1.5px] bg-[var(--glass-highlight)] pointer-events-none"
            />

            {/* Header: Month & Year Navigator */}
            <div className="flex items-center justify-between pb-1 border-b border-[var(--border)]">
              <button
                type="button"
                onClick={handlePrevMonth}
                aria-label="Previous Month"
                className="w-7 h-7 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent hover:border-[var(--border)] transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <div className="text-xs font-bold text-[var(--text)] flex items-center gap-1.5 font-mono">
                <span>{MONTH_NAMES[viewMonth]}</span>
                <span className="text-[var(--accent)]">{viewYear}</span>
              </div>

              <button
                type="button"
                onClick={handleNextMonth}
                aria-label="Next Month"
                className="w-7 h-7 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent hover:border-[var(--border)] transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Weekdays Header */}
            <div className="grid grid-cols-7 gap-1 text-center">
              {WEEK_DAYS.map((wd) => (
                <div key={wd} className="text-[10px] font-bold text-[var(--text-subtle)] font-mono py-0.5">
                  {wd}
                </div>
              ))}
            </div>

            {/* Days Grid */}
            <div className="grid grid-cols-7 gap-1 text-center">
              {/* Previous month padding days */}
              {Array.from({ length: firstDayOfWeek }).map((_, idx) => {
                const dayNum = totalDaysPrevMonth - firstDayOfWeek + idx + 1;
                return (
                  <div
                    key={`prev-${idx}`}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-[11px] font-mono text-[var(--text-subtle)]/40 pointer-events-none"
                  >
                    {dayNum}
                  </div>
                );
              })}

              {/* Current month days */}
              {Array.from({ length: daysInMonth }).map((_, idx) => {
                const dayNum = idx + 1;
                const currentIso = formatIso(viewYear, viewMonth, dayNum);
                const isSelected = value === currentIso;
                const isToday = todayIso === currentIso;
                const disabledDay = isDayDisabled(dayNum);

                return (
                  <button
                    key={`day-${dayNum}`}
                    type="button"
                    disabled={disabledDay}
                    onClick={() => handleSelectDay(dayNum)}
                    className={cn(
                      "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-mono transition-all duration-150 cursor-pointer outline-none",
                      isSelected
                        ? "bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white font-bold shadow-[0_0_12px_var(--accent-glow)] ring-1 ring-white/20"
                        : "text-[var(--text)] hover:bg-[var(--surface-hover)] hover:text-[var(--accent)] hover:border hover:border-[var(--accent-border)]",
                      isToday && !isSelected && "border border-[var(--accent)] text-[var(--accent)] font-bold",
                      disabledDay && "opacity-30 cursor-not-allowed pointer-events-none hover:bg-transparent"
                    )}
                  >
                    {dayNum}
                  </button>
                );
              })}
            </div>

            {/* Quick Actions Footer */}
            <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs">
              <button
                type="button"
                onClick={handleSelectToday}
                className="text-[11px] font-medium text-[var(--accent)] hover:underline flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                Today
              </button>

              {!required && value && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="text-[11px] text-[var(--text-muted)] hover:text-rose-400 cursor-pointer"
                >
                  Clear
                </button>
              )}

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-[var(--surface-hover)] hover:bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] cursor-pointer flex items-center gap-1"
              >
                <Check className="w-3 h-3 text-emerald-400" />
                Done
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
