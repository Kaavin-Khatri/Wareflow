"use client";

import React, { useEffect, useRef } from "react";
import anime from "animejs";

interface AnimeCheckIconProps {
  checked: boolean;
  size?: number;
  className?: string;
  strokeColor?: string;
}

/**
 * High-performance SVG path draw-in checkmark powered by anime.js strokeDashoffset animation.
 */
export function AnimeCheckIcon({
  checked,
  size = 20,
  className = "",
  strokeColor = "currentColor",
}: AnimeCheckIconProps) {
  const pathRef = useRef<SVGPathElement>(null);

  useEffect(() => {
    if (!pathRef.current) return;

    if (checked) {
      anime({
        targets: pathRef.current,
        strokeDashoffset: [anime.setDashoffset, 0],
        easing: "easeOutQuart",
        duration: 450,
        delay: 50,
      });
    } else {
      anime({
        targets: pathRef.current,
        strokeDashoffset: [0, anime.setDashoffset],
        easing: "easeInQuad",
        duration: 200,
      });
    }
  }, [checked]);

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={strokeColor}
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path ref={pathRef} d="M20 6L9 17l-5-5" />
    </svg>
  );
}

interface AnimeMicroPressProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  scaleDown?: number;
}

/**
 * Micro button/item press effect using anime.js elastic rebound.
 */
export function AnimeMicroPress({
  children,
  className = "",
  onClick,
  scaleDown = 0.94,
}: AnimeMicroPressProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const handlePointerDown = () => {
    if (!containerRef.current) return;
    anime.remove(containerRef.current);
    anime({
      targets: containerRef.current,
      scale: scaleDown,
      duration: 120,
      easing: "easeOutQuad",
    });
  };

  const handlePointerUp = () => {
    if (!containerRef.current) return;
    anime.remove(containerRef.current);
    anime({
      targets: containerRef.current,
      scale: 1,
      duration: 350,
      easing: "easeOutElastic(1, .5)",
    });
  };

  return (
    <div
      ref={containerRef}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      onClick={onClick}
      className={`inline-flex items-center justify-center cursor-pointer select-none ${className}`}
    >
      {children}
    </div>
  );
}

interface AnimeMorphIconProps {
  active: boolean;
  size?: number;
  className?: string;
}

/**
 * Geometric SVG morphing demonstration using anime.js numeric coordinate interpolation.
 */
export function AnimeMorphIcon({ active, size = 24, className = "" }: AnimeMorphIconProps) {
  const pathRef = useRef<SVGPathElement>(null);

  // Path 1: Square / Box shape
  const squarePath = "M4 4h16v16H4z";
  // Path 2: Diamond / Octagon morphed shape
  const diamondPath = "M12 2l10 10-10 10L2 12z";

  useEffect(() => {
    if (!pathRef.current) return;
    anime({
      targets: pathRef.current,
      d: [{ value: active ? diamondPath : squarePath }],
      easing: "easeInOutQuint",
      duration: 500,
    });
  }, [active]);

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path ref={pathRef} d={squarePath} />
    </svg>
  );
}
