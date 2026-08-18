"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface PageHeaderProps {
  title: React.ReactNode;
  description?: React.ReactNode;
  badge?: React.ReactNode;
  backHref?: string;
  backLabel?: string;
  primaryAction?: React.ReactNode;
  secondaryActions?: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  className?: string;
  children?: React.ReactNode;
}

export function PageHeader({
  title,
  description,
  badge,
  backHref,
  backLabel,
  primaryAction,
  secondaryActions,
  breadcrumbs,
  className,
  children,
}: PageHeaderProps) {
  return (
    <div className={cn("space-y-4 pb-6 border-b border-[var(--border)]", className)}>
      {/* Back Link or Breadcrumbs */}
      {(backHref || (breadcrumbs && breadcrumbs.length > 0)) && (
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          {backHref ? (
            <Link
              href={backHref}
              className="inline-flex items-center gap-1.5 hover:text-[var(--text)] transition-colors group font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
              <span>{backLabel || "Back"}</span>
            </Link>
          ) : (
            breadcrumbs && (
              <nav aria-label="Breadcrumbs" className="flex items-center gap-1.5">
                {breadcrumbs.map((crumb, idx) => {
                  const isLast = idx === breadcrumbs.length - 1;
                  return (
                    <React.Fragment key={crumb.label}>
                      {idx > 0 && <ChevronRight className="w-3 h-3 text-[var(--text-subtle)]" />}
                      {crumb.href && !isLast ? (
                        <Link
                          href={crumb.href}
                          className="hover:text-[var(--text)] transition-colors"
                        >
                          {crumb.label}
                        </Link>
                      ) : (
                        <span className={isLast ? "font-semibold text-[var(--text)]" : ""}>
                          {crumb.label}
                        </span>
                      )}
                    </React.Fragment>
                  );
                })}
              </nav>
            )
          )}
        </div>
      )}

      {/* Main Row: Title + Badge + Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[var(--text)]">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-3xl leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {/* Action Controls */}
        {(primaryAction || secondaryActions) && (
          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            {secondaryActions}
            {primaryAction}
          </div>
        )}
      </div>

      {children && <div className="pt-2">{children}</div>}
    </div>
  );
}

export default PageHeader;
