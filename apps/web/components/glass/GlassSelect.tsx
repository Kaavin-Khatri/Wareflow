"use client";

import React, { useState, useRef, useEffect, useId } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ChevronDown, Check, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { SPRING_PRESETS } from "../motion/MotionProvider";

export interface GlassSelectOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface GlassSelectProps {
  options: (GlassSelectOption | string)[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  triggerClassName?: string;
  menuClassName?: string;
  size?: "sm" | "md" | "lg";
  searchable?: boolean;
  name?: string;
  id?: string;
  "aria-label"?: string;
}

export function GlassSelect({
  options,
  value,
  onChange,
  placeholder = "Select an option...",
  disabled = false,
  className,
  triggerClassName,
  menuClassName,
  size = "sm",
  searchable,
  name,
  id,
  "aria-label": ariaLabel,
}: GlassSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const generatedId = useId();
  const selectId = id || generatedId;

  // Normalize options to GlassSelectOption format
  const normalizedOptions: GlassSelectOption[] = options.map((opt) =>
    typeof opt === "string" ? { value: opt, label: opt } : opt,
  );

  const selectedOption = normalizedOptions.find((opt) => opt.value === value);

  // Auto enable search if more than 7 options unless explicitly disabled
  const showSearch = searchable ?? normalizedOptions.length > 7;

  const filteredOptions = normalizedOptions.filter((opt) =>
    opt.label.toLowerCase().includes(searchQuery.toLowerCase().trim()),
  );

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus search input on open
  useEffect(() => {
    if (isOpen && showSearch) {
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
  }, [isOpen, showSearch]);

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    if (e.key === "Enter" || e.key === " ") {
      if (!isOpen) {
        e.preventDefault();
        setIsOpen(true);
      } else if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
        e.preventDefault();
        handleSelect(filteredOptions[highlightedIndex].value);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
      setSearchQuery("");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setHighlightedIndex((prev) => (prev < filteredOptions.length - 1 ? prev + 1 : 0));
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : filteredOptions.length - 1));
      }
    }
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs rounded-xl min-h-[34px]",
    md: "px-3.5 py-2 text-xs rounded-xl min-h-[38px]",
    lg: "px-4 py-2.5 text-sm rounded-xl min-h-[42px]",
  };

  return (
    <div
      ref={containerRef}
      className={cn("relative inline-block w-full min-w-[140px] text-left select-none", isOpen ? "z-50" : "z-auto", className)}
    >
      {/* Hidden Native Select for Form & Testing Accessibility */}
      <select
        name={name}
        id={selectId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        tabIndex={-1}
        className="sr-only"
        aria-label={ariaLabel}
      >
        <option value="">{placeholder}</option>
        {normalizedOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Interactive Liquid Glass Trigger Button */}
      <button
        type="button"
        id={id ? `${id}-trigger` : `${generatedId}-trigger`}
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel || selectedOption?.label || placeholder}
        className={cn(
          "w-full flex items-center justify-between gap-2 bg-[var(--surface)]/80 hover:bg-[var(--surface-hover)] border border-[var(--glass-border)] text-[var(--text)] transition-all duration-200 outline-none focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent-subtle)] focus-visible:shadow-[0_0_16px_-2px_var(--accent-glow)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed",
          sizeClasses[size],
          isOpen && "border-[var(--accent)] ring-2 ring-[var(--accent-subtle)] shadow-[0_0_16px_-2px_var(--accent-glow)]",
          triggerClassName,
        )}
      >
        <span className="flex items-center gap-2 truncate font-medium">
          {selectedOption?.icon && <span className="shrink-0 w-4 h-4 text-[var(--accent)]">{selectedOption.icon}</span>}
          <span className={cn("truncate", !selectedOption && "text-[var(--text-subtle)]")}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
        </span>
        <ChevronDown
          className={cn(
            "w-3.5 h-3.5 text-[var(--text-muted)] shrink-0 transition-transform duration-200",
            isOpen && "rotate-180 text-[var(--accent)]",
          )}
        />
      </button>

      {/* Animated Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -4 }}
            transition={SPRING_PRESETS.snappy}
            role="listbox"
            tabIndex={-1}
            className={cn(
              "absolute left-0 right-0 z-[80] mt-1.5 min-w-full rounded-2xl bg-[var(--surface-elevated)] backdrop-blur-2xl border border-[var(--glass-border)] shadow-2xl p-1.5 space-y-0.5 overflow-hidden",
              menuClassName,
            )}
          >
            {/* Top Specular Sheen */}
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-[1.5px] bg-[var(--glass-highlight)] pointer-events-none"
            />

            {/* Optional Search Filter Input */}
            {showSearch && (
              <div className="p-1 pb-1.5 border-b border-[var(--border)]">
                <div className="relative flex items-center">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 text-[var(--text-muted)] pointer-events-none" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Search options..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setHighlightedIndex(0);
                    }}
                    onKeyDown={handleKeyDown}
                    className="w-full pl-8 pr-2.5 py-1 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] placeholder:text-[var(--text-subtle)] outline-none focus:border-[var(--accent)]"
                  />
                </div>
              </div>
            )}

            {/* Scrollable Option Items List */}
            <div className="max-h-56 overflow-y-auto space-y-0.5 py-0.5 pr-0.5 custom-scrollbar">
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-2 text-xs text-[var(--text-muted)] text-center">
                  No matching options found.
                </div>
              ) : (
                filteredOptions.map((option, idx) => {
                  const isSelected = option.value === value;
                  const isHighlighted = idx === highlightedIndex;

                  return (
                    <button
                      key={option.value}
                      type="button"
                      disabled={option.disabled}
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => handleSelect(option.value)}
                      onMouseEnter={() => setHighlightedIndex(idx)}
                      className={cn(
                        "w-full flex items-center justify-between gap-2 px-3 py-2 text-xs rounded-xl font-medium transition cursor-pointer text-left",
                        isSelected
                          ? "bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold border border-[var(--accent-border)]"
                          : isHighlighted
                            ? "bg-[var(--surface-hover)] text-[var(--text)]"
                            : "text-[var(--text)] hover:bg-[var(--surface-hover)]",
                        option.disabled && "opacity-40 cursor-not-allowed",
                      )}
                    >
                      <span className="flex items-center gap-2 truncate">
                        {option.icon && <span className="w-3.5 h-3.5 shrink-0">{option.icon}</span>}
                        <span className="truncate">{option.label}</span>
                      </span>
                      {isSelected && (
                        <Check className="w-3.5 h-3.5 text-[var(--accent)] shrink-0 ml-auto" />
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
