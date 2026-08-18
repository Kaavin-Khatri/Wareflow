"use client";

import React, { useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface GlassTiltCardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
  tiltMaxAngleX?: number;
  tiltMaxAngleY?: number;
  perspective?: number;
  scale?: number;
  children: React.ReactNode;
}

export function GlassTiltCard({
  className,
  glow = false,
  tiltMaxAngleX = 8,
  tiltMaxAngleY = 8,
  perspective = 1000,
  scale = 1.02,
  children,
  ...props
}: GlassTiltCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tiltStyle, setTiltStyle] = useState<React.CSSProperties>({});
  const [glarePosition, setGlarePosition] = useState<{ x: number; y: number; opacity: number }>({
    x: 50,
    y: 50,
    opacity: 0,
  });

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!cardRef.current) return;
      const rect = cardRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -tiltMaxAngleX;
      const rotateY = ((x - centerX) / centerX) * tiltMaxAngleY;

      setTiltStyle({
        transform: `perspective(${perspective}px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(${scale}, ${scale}, ${scale})`,
        transition: "transform 100ms ease-out",
      });

      setGlarePosition({
        x: (x / rect.width) * 100,
        y: (y / rect.height) * 100,
        opacity: 0.6,
      });
    },
    [perspective, scale, tiltMaxAngleX, tiltMaxAngleY],
  );

  const handleMouseLeave = useCallback(() => {
    setTiltStyle({
      transform: `perspective(${perspective}px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`,
      transition: "transform 400ms cubic-bezier(0.16, 1, 0.3, 1)",
    });
    setGlarePosition((prev) => ({ ...prev, opacity: 0 }));
  }, [perspective]);

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={tiltStyle}
      className={cn(
        "relative rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] shadow-[var(--glass-shadow)] transition-all duration-300 overflow-hidden transform-gpu will-change-transform group",
        glow && "shadow-[0_0_30px_-8px_var(--accent-glow)] border-[var(--accent-border)]",
        className,
      )}
      {...props}
    >
      {/* Light-Edge Specular Highlight Sheen */}
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-[1px] bg-[var(--glass-highlight)] pointer-events-none z-10"
      />

      {/* Dynamic Cursor Glare Spotlight */}
      <div
        aria-hidden="true"
        style={{
          background: `radial-gradient(circle 240px at ${glarePosition.x}% ${glarePosition.y}%, rgba(255,255,255,0.12), transparent 80%)`,
          opacity: glarePosition.opacity,
          transition: "opacity 300ms ease-out",
        }}
        className="absolute inset-0 pointer-events-none z-10"
      />

      {/* Perimeter Lens Refraction Gradient */}
      <div
        aria-hidden="true"
        className="absolute inset-0 rounded-[inherit] pointer-events-none opacity-40 group-hover:opacity-70 transition-opacity bg-gradient-to-b from-white/5 via-transparent to-black/5 dark:from-white/10 dark:to-transparent"
      />

      <div className="relative z-10">{children}</div>
    </div>
  );
}

export default GlassTiltCard;
