"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { animate } from "motion/react";

export interface AnimatedNumberProps {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  formatter?: (val: number) => string;
  className?: string;
}

export function AnimatedNumber({
  value,
  duration = 1.2,
  prefix = "",
  suffix = "",
  decimals = 0,
  formatter,
  className,
}: AnimatedNumberProps) {
  const spanRef = useRef<HTMLSpanElement>(null);
  const previousValueRef = useRef<number>(0);
  const hasAnimatedRef = useRef<boolean>(false);

  const formatNumber = useCallback(
    (val: number) => {
      const formatted = formatter
        ? formatter(val)
        : decimals > 0
          ? val.toFixed(decimals)
          : Math.round(val).toLocaleString("en-IN");
      return `${prefix}${formatted}${suffix}`;
    },
    [formatter, decimals, prefix, suffix],
  );

  useEffect(() => {
    if (!spanRef.current) return;

    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      spanRef.current.textContent = formatNumber(value);
      previousValueRef.current = value;
      return;
    }

    const start = hasAnimatedRef.current ? previousValueRef.current : 0;
    hasAnimatedRef.current = true;
    previousValueRef.current = value;

    const controls = animate(start, value, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (latest) => {
        if (spanRef.current) {
          spanRef.current.textContent = formatNumber(latest);
        }
      },
    });

    return () => controls.stop();
  }, [value, duration, formatNumber]);

  return (
    <span ref={spanRef} className={className}>
      {formatNumber(value)}
    </span>
  );
}

export default AnimatedNumber;
