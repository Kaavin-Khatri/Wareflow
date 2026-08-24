"use client";

import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface ComparisonBadgeProps {
  deltaPct?: number | null;
  currentValue?: number | null;
  priorValue?: number | null;
  higherIsBetter?: boolean;
  periodLabel?: string;
  size?: "xs" | "sm" | "md";
  showPeriodLabel?: boolean;
  showPriorValue?: boolean;
  formatter?: (val: number) => string;
  className?: string;
}

/**
 * Reusable KPI Comparison Badge
 *
 * Displays period-over-period or year-over-year percentage delta,
 * direction arrow, and contextual color-coding based on metric polarity.
 */
export function ComparisonBadge({
  deltaPct,
  currentValue,
  priorValue,
  higherIsBetter = true,
  periodLabel = "vs prior period",
  size = "sm",
  showPeriodLabel = false,
  showPriorValue = false,
  formatter,
  className = "",
}: ComparisonBadgeProps) {
  // If delta is unavailable or undefined
  if (deltaPct === undefined || deltaPct === null || isNaN(deltaPct)) {
    return (
      <span
        className={`inline-flex items-center gap-1 font-medium rounded-full bg-zinc-500/10 text-zinc-500 dark:text-zinc-400 border border-zinc-500/20 ${
          size === "xs"
            ? "px-1.5 py-0.5 text-[10px]"
            : size === "md"
            ? "px-2.5 py-1 text-xs"
            : "px-2 py-0.5 text-[11px]"
        } ${className}`}
        title={periodLabel}
      >
        <Minus className={size === "xs" ? "w-2.5 h-2.5" : "w-3 h-3"} />
        <span>0.0%</span>
        {showPeriodLabel && <span className="opacity-75 text-[10px]">{periodLabel}</span>}
      </span>
    );
  }

  const isFlat = Math.abs(deltaPct) < 0.05;
  const isPositiveDelta = deltaPct > 0;
  const isFavorable = isPositiveDelta ? higherIsBetter : !higherIsBetter;

  // Icon sizing
  const iconSize = size === "xs" ? "w-2.5 h-2.5" : size === "md" ? "w-3.5 h-3.5" : "w-3 h-3";
  const pillPadding =
    size === "xs"
      ? "px-1.5 py-0.5 text-[10px]"
      : size === "md"
      ? "px-2.5 py-1 text-xs"
      : "px-2 py-0.5 text-[11px]";

  // Badge Color Styles
  let colorClasses = "bg-zinc-500/10 text-zinc-500 dark:text-zinc-400 border-zinc-500/20";
  if (!isFlat) {
    if (isFavorable) {
      colorClasses =
        "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/25";
    } else {
      colorClasses = "bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/25";
    }
  }

  const formattedDelta = isFlat
    ? "0.0%"
    : `${isPositiveDelta ? "+" : ""}${deltaPct.toFixed(1)}%`;
  const formattedPrior =
    priorValue !== undefined && priorValue !== null
      ? formatter
        ? formatter(priorValue)
        : priorValue.toLocaleString()
      : null;

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full border transition-all duration-200 ${colorClasses} ${pillPadding} ${className}`}
      title={
        formattedPrior
          ? `${formattedDelta} ${periodLabel} (prior: ${formattedPrior})`
          : `${formattedDelta} ${periodLabel}`
      }
    >
      {isFlat ? (
        <Minus className={iconSize} />
      ) : isPositiveDelta ? (
        <TrendingUp className={iconSize} />
      ) : (
        <TrendingDown className={iconSize} />
      )}
      <span className="font-semibold tabular-nums">{formattedDelta}</span>
      {showPeriodLabel && (
        <span className="opacity-75 text-[10px] ml-0.5">{periodLabel}</span>
      )}
      {showPriorValue && formattedPrior && (
        <span className="opacity-60 text-[10px] ml-0.5 font-normal">({formattedPrior})</span>
      )}
    </span>
  );
}

export default ComparisonBadge;
