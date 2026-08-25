import React from "react";
import { AppLayout } from "@/components/AppLayout";
import { PageHeader } from "@/components/PageHeader";
import { LeadDiscoveryView } from "@/components/leads/LeadDiscoveryView";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { Compass, Sparkles } from "lucide-react";

export const metadata = {
  title: "Retail Lead Discovery Map | WareFlow",
  description: "Interactive Google Places retail leads discovery map with new shop highlighting.",
};

export default function LeadMapPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          title="Retail Lead Discovery Map"
          description="Locate nearby gruh udyog units, snack shops, and kirana stores. Newly discovered shops are highlighted with priority badges for immediate outreach."
          badge={<GlassBadge variant="accent">Growth Radar</GlassBadge>}
          breadcrumbs={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Growth", href: "/admin/leads/map" },
            { label: "Lead Map" },
          ]}
        />

        <LeadDiscoveryView />
      </div>
    </AppLayout>
  );
}
