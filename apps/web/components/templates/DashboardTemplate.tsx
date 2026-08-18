"use client";

import React, { ReactNode } from "react";
import { GlassCard } from "@/components/glass/GlassCard";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/GlassMotion";
import { PageHeader } from "@/components/PageHeader";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

export interface KpiMetric {
  id: string;
  title: string;
  value: ReactNode;
  change?: string;
  trend?: "up" | "down" | "neutral";
  subtitle?: string;
  icon?: ReactNode;
  badge?: ReactNode;
}

export interface DashboardTemplateProps {
  /** Dashboard title (e.g. Executive Overview, Warehouse Telemetry) */
  title: ReactNode;
  /** Subtitle or live sync status */
  description?: ReactNode;
  /** Live badge or status indicator */
  badge?: ReactNode;
  /** Filter slot (e.g. date-range picker, warehouse selector) */
  filters?: ReactNode;
  /** Primary dashboard action (e.g. + New Transaction, Export Report) */
  primaryAction?: ReactNode;
  /** Secondary actions (e.g. Export, Audit Log) */
  secondaryActions?: ReactNode;
  /** Top row of 4-6 KPI metrics */
  kpiMetrics?: KpiMetric[];
  /** Custom KPI slot if not using standard array */
  customKpiSlot?: ReactNode;
  /** 8-Column Main Chart or visual feed */
  mainContent: ReactNode;
  /** 4-Column Secondary breakdown or urgent alerts */
  sideContent?: ReactNode;
  /** Optional bottom full-width section (e.g. Recent transactions table) */
  bottomSection?: ReactNode;
}

export function DashboardTemplate({
  title,
  description,
  badge,
  filters,
  primaryAction,
  secondaryActions,
  kpiMetrics,
  customKpiSlot,
  mainContent,
  sideContent,
  bottomSection,
}: DashboardTemplateProps) {
  return (
    <FadeIn className="w-full space-y-6 pb-16">
      {/* 1. Header with Controls */}
      <PageHeader
        title={title}
        description={description}
        badge={badge}
        primaryAction={primaryAction}
        secondaryActions={
          filters || secondaryActions ? (
            <div className="flex items-center gap-2.5 flex-wrap">
              {filters}
              {secondaryActions}
            </div>
          ) : undefined
        }
      />

      {/* 2. Top KPI Metric Cards */}
      {customKpiSlot ? (
        <div>{customKpiSlot}</div>
      ) : kpiMetrics && kpiMetrics.length > 0 ? (
        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiMetrics.map((kpi) => (
            <StaggerItem key={kpi.id}>
              <GlassCard hoverable className="p-5 space-y-3 relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--text-muted)]">
                    {kpi.title}
                  </span>
                  {kpi.icon && (
                    <div className="w-8 h-8 rounded-xl bg-[var(--surface-hover)] text-[var(--accent)] flex items-center justify-center">
                      {kpi.icon}
                    </div>
                  )}
                </div>

                <div className="flex items-baseline justify-between gap-2">
                  <div className="text-2xl font-bold tracking-tight text-[var(--text)] font-mono">
                    {kpi.value}
                  </div>

                  {kpi.change && (
                    <span
                      className={`inline-flex items-center text-xs font-semibold ${
                        kpi.trend === "up"
                          ? "text-emerald-400"
                          : kpi.trend === "down"
                            ? "text-rose-400"
                            : "text-[var(--text-muted)]"
                      }`}
                    >
                      {kpi.trend === "up" && <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />}
                      {kpi.trend === "down" && <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
                      {kpi.change}
                    </span>
                  )}
                </div>

                {(kpi.subtitle || kpi.badge) && (
                  <div className="flex items-center justify-between text-[11px] text-[var(--text-subtle)] pt-1 border-t border-[var(--border)]">
                    <span>{kpi.subtitle}</span>
                    {kpi.badge}
                  </div>
                )}
              </GlassCard>
            </StaggerItem>
          ))}
        </StaggerContainer>
      ) : null}

      {/* 3. 12-Column Responsive Dashboard Body */}
      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Main 8-Column Content */}
        <div className={`${sideContent ? "col-span-12 lg:col-span-8" : "col-span-12"} space-y-6`}>
          {mainContent}
        </div>

        {/* 4-Column Side Content */}
        {sideContent && <div className="col-span-12 lg:col-span-4 space-y-6">{sideContent}</div>}
      </div>

      {/* 4. Optional Full-Width Bottom Section */}
      {bottomSection && <div className="pt-2">{bottomSection}</div>}
    </FadeIn>
  );
}
