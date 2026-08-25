# WareFlow — Master Sitemap & Screen-to-Template Registry

> **Core Architectural Rule**: Every screen in WareFlow maps strictly to one of the **Four Locked Page Templates** (`ListViewTemplate`, `DetailViewTemplate`, `FormTemplate`, `DashboardTemplate`). No feature phase may invent an arbitrary or uncoordinated page layout from scratch.

---

## 1. Visual Benchmark & Layout Foundations

- **Visual Benchmarks**: Modeled on tier-1 B2B product dashboards (**Linear**, **Stripe Dashboard**, **Notion**) — dense, confident, functional, generous whitespace, clear visual hierarchy, true obsidian/paper contrast.
- **Grid System**: 12-column responsive layout grid (`grid grid-cols-12 gap-4 lg:gap-6`).
- **Base Spacing Scale**: 4px standard unit (e.g. `p-4` = 16px, `p-6` = 24px, `p-8` = 32px).
- **Surface Elevation**: Specular frosted liquid glass overlays (`GlassCard`, `GlassPanel`) over GPU-rendered liquid gradient backdrop.

---

## 2. Master Screen Registry by Domain

### A. Executive & Operational Dashboards

| Route                  | Screen Name                      | Template Assignment | Primary Components & Function                                                              |
| :--------------------- | :------------------------------- | :------------------ | :----------------------------------------------------------------------------------------- |
| `/dashboard`           | Executive Owner Dashboard        | `DashboardTemplate` | Top KPI row, revenue run-rate charts, urgent low-stock alerts, pending dispatch queue.     |
| `/analytics`           | Enterprise Business Intelligence | `DashboardTemplate` | Turnover velocity, gross margin breakdown, category heatmaps, supplier fulfillment rating. |
| `/inventory/analytics` | Stock Health & Expiry Forecast   | `DashboardTemplate` | Expiry timeline charts, dead-stock capital exposure, reorder point prediction.             |
| `/leads/map`           | Geographic B2B Retailer Map      | `DashboardTemplate` | Regional retailer density, regional quota metrics, territory sales leaderboard.            |
| `/portal/dashboard`    | Retailer Self-Service Portal     | `DashboardTemplate` | Order status tracking, outstanding credit balance, re-order quick actions.                 |

---

### B. Inventory & Warehousing

| Route                     | Screen Name                   | Template Assignment  | Primary Components & Function                                                               |
| :------------------------ | :---------------------------- | :------------------- | :------------------------------------------------------------------------------------------ |
| `/inventory`              | Wholesale Products Catalog    | `ListViewTemplate`   | Sticky search & category filters, SKU data table, stock health badges, bulk export/reorder. |
| `/inventory/[id]`         | Product Master Record         | `DetailViewTemplate` | 8-col batch/UOM/ledger tabs + 4-col sticky supplier summary & pricing controls.             |
| `/inventory/new`          | Product Creation Wizard       | `FormTemplate`       | Sectioned forms for SKU/HSN, pricing tiers, UOM conversion factors, sticky action bar.      |
| `/inventory/[id]/edit`    | Edit Product Details          | `FormTemplate`       | Update specs, category hierarchy, barcode assignment, reorder thresholds.                   |
| `/inventory/movements`    | Stock Movement Ledger         | `ListViewTemplate`   | Immutable append-only transaction audit table with source/destination filters.              |
| `/inventory/batches`      | FIFO Batch & Expiry Register  | `ListViewTemplate`   | Batch shelf-life tracker, days-to-expiry status indicators, warehouse filtering.            |
| `/inventory/recalls`      | Batch Recalls & Traceability  | `ListViewTemplate`   | Active recall campaigns, severity level filters, affected sales order summaries.            |
| `/inventory/recalls/[id]` | Recall Investigation & Action | `DetailViewTemplate` | 8-col affected retailer/batch timeline + 4-col quarantine action panel.                     |
| `/inventory/warehouses`   | Warehouse Locations & Bins    | `ListViewTemplate`   | Storage facility list, capacity utilization bars, bin assignment status.                    |

---

### C. Purchasing & Supplier Procurement

| Route                     | Screen Name                   | Template Assignment  | Primary Components & Function                                                           |
| :------------------------ | :---------------------------- | :------------------- | :-------------------------------------------------------------------------------------- |
| `/suppliers`              | Supplier Directory            | `ListViewTemplate`   | Supplier list with FSSAI/GST compliance status, contact info, lead time rating.         |
| `/suppliers/[id]`         | Supplier Dossier              | `DetailViewTemplate` | 8-col PO history & catalog mapping + 4-col compliance documents & key contact panel.    |
| `/suppliers/new`          | Onboard Supplier              | `FormTemplate`       | Sectioned vendor profile, GSTIN/FSSAI details, bank account, payment terms.             |
| `/suppliers/[id]/edit`    | Edit Supplier Profile         | `FormTemplate`       | Compliance license renewal, contact update, default delivery address.                   |
| `/purchasing/orders`      | Purchase Orders (PO) Register | `ListViewTemplate`   | PO workflow pipeline (Draft -> Sent -> Confirmed -> Received), supplier search.         |
| `/purchasing/orders/[id]` | Purchase Order Detail         | `DetailViewTemplate` | 8-col line item receipt tracker & GRN logs + 4-col supplier magic link status & totals. |
| `/purchasing/orders/new`  | Create Purchase Order         | `FormTemplate`       | Supplier selector, batch line items, MOQ checks, expected delivery date picker.         |
| `/purchasing/returns`     | Supplier Purchase Returns     | `ListViewTemplate`   | Damaged / rejected stock debit note requests and supplier RMA status.                   |

---

### D. Sales & B2B Distribution

| Route                  | Screen Name                    | Template Assignment  | Primary Components & Function                                                              |
| :--------------------- | :----------------------------- | :------------------- | :----------------------------------------------------------------------------------------- |
| `/retailers`           | B2B Retailer Accounts          | `ListViewTemplate`   | Tiered buyers, credit limit health indicators, outstanding receivables, region filter.     |
| `/retailers/[id]`      | Retailer Account Dossier       | `DetailViewTemplate` | 8-col sales order history & payment ledger + 4-col credit limit adjuster & quick order.    |
| `/retailers/new`       | Onboard New Retailer           | `FormTemplate`       | KYC/GST verification, pricing tier assignment, authorized credit limit setting.            |
| `/retailers/[id]/edit` | Edit Retailer Profile          | `FormTemplate`       | Address update, credit terms renegotiation, assigned sales representative.                 |
| `/orders`              | Sales Orders Pipeline          | `ListViewTemplate`   | Order status filters (Draft -> Confirmed -> Packing -> Dispatched -> Paid).                |
| `/orders/[id]`         | Sales Order Fulfillment Detail | `DetailViewTemplate` | 8-col item picking/batch allocation + 4-col dispatch assignment & invoice generator.       |
| `/orders/new`          | Create Wholesale Sales Order   | `FormTemplate`       | Retailer/walk-in selector, live inventory lookup, credit limit validation, discount rules. |
| `/returns`             | Sales Returns & RMA            | `ListViewTemplate`   | Return authorization requests, inspection status, credit note issuance.                    |
| `/returns/[id]`        | Return Inspection Detail       | `DetailViewTemplate` | 8-col returned item condition review + 4-col restock/dispose decision panel.               |

---

### E. Invoicing & GST Billing

| Route                    | Screen Name                     | Template Assignment  | Primary Components & Function                                                            |
| :----------------------- | :------------------------------ | :------------------- | :--------------------------------------------------------------------------------------- |
| `/invoices`              | GST Tax Invoices Register       | `ListViewTemplate`   | Search by invoice no, GST slab breakdown, e-Invoice / IRN status, payment status.        |
| `/invoices/[id]`         | Tax Invoice & E-Way Bill Detail | `DetailViewTemplate` | 8-col immutable line snapshot & GST calculation + 4-col IRN/QR code & PDF print/send.    |
| `/invoices/new`          | Generate Invoice from Order     | `FormTemplate`       | Sales order conversion, HSN mapping, GST slab verification, e-Way bill parameters.       |
| `/invoices/payments`     | Payments & Collections          | `ListViewTemplate`   | Payment history, mode (NEFT/RTGS/UPI/Cheque), invoice reconciliation.                    |
| `/invoices/payments/new` | Record Payment Received         | `FormTemplate`       | Retailer selection, invoice allocation, payment proof attachment, ledger balance update. |

---

### F. Logistics & Dispatch

| Route                        | Screen Name                  | Template Assignment  | Primary Components & Function                                                           |
| :--------------------------- | :--------------------------- | :------------------- | :-------------------------------------------------------------------------------------- |
| `/logistics/dispatch`        | Live Dispatch Queue          | `ListViewTemplate`   | Ready-for-packing orders, carrier assignment, route grouping, dispatch status.          |
| `/logistics/deliveries/[id]` | Vehicle & Delivery Run Sheet | `DetailViewTemplate` | 8-col multi-stop delivery stops & sign-off logs + 4-col driver/vehicle info & map link. |
| `/logistics/dispatch/new`    | Schedule Vehicle Run         | `FormTemplate`       | Select orders, assign driver and vehicle registration, generate packing slip.           |

---

### G. Leads, Growth & CRM

| Route                   | Screen Name                   | Template Assignment  | Primary Components & Function                                                                |
| :---------------------- | :---------------------------- | :------------------- | :------------------------------------------------------------------------------------------- |
| `/leads`                | B2B Retailer Lead Pipeline    | `ListViewTemplate`   | Lead status (New -> Contacted -> Sample Sent -> Converted), location, estimated volume.      |
| `/leads/[id]`           | Lead Interaction Dossier      | `DetailViewTemplate` | 8-col call notes, sample orders & quotes + 4-col convert-to-retailer trigger & contact info. |
| `/leads/new`            | Add Prospective Retailer      | `FormTemplate`       | Shop name, market location, expected category demand, owner mobile number.                   |
| `/growth/campaigns`     | Wholesale Promotion Campaigns | `ListViewTemplate`   | Bulk WhatsApp / email alert broadcasts, target retailer segment, redemption metrics.         |
| `/growth/campaigns/new` | Broadcast Campaign Builder    | `FormTemplate`       | Segment filter (low-order frequency / high credit), message template, special discounts.     |

---

### H. Organization & System Administration

| Route                          | Screen Name                   | Template Assignment  | Primary Components & Function                                                         |
| :----------------------------- | :---------------------------- | :------------------- | :------------------------------------------------------------------------------------ |
| `/admin/settings/staff`        | Staff Directory & Access      | `ListViewTemplate`   | Active user list, role badges, 2FA status, last active timestamp, invite trigger.     |
| `/admin/settings/staff/invite` | Staff Invitation & Role Setup | `FormTemplate`       | Email, full name, assigned role, warehouse access restrictions.                       |
| `/admin/settings/permissions`  | Role-Permission Matrix        | `DetailViewTemplate` | 8-col interactive role capability grid + 4-col role creation & policy guidance panel. |
| `/admin/settings/security`     | 2FA & Authentication Policy   | `FormTemplate`       | TOTP configuration, QR code setup, backup code generator, session timeouts.           |
| `/admin/settings/appearance`   | Appearance & Theme Settings   | `FormTemplate`       | Light/Dark/System radio, 7-swatch accent picker, real-time glass preview pane.        |
| `/admin/settings/business`     | Legal Entity & GST Profile    | `FormTemplate`       | Business name, PAN/GSTIN, FSSAI license & renewal date, bank coordinates.             |
| `/admin/audit`                 | General Action Audit Timeline | `ListViewTemplate`   | Chronological audit log with entity type filters, before/after JSON diff inspector.   |
| `/styleguide`                  | Glass Design System Showcase  | Custom Showcase      | Primitives test bench, 4 template previews, physics animations, anime.js triggers.    |

---

### I. External Portals & Public Workflows

| Route                         | Screen Name                    | Template Assignment  | Primary Components & Function                                                            |
| :---------------------------- | :----------------------------- | :------------------- | :--------------------------------------------------------------------------------------- |
| `/portal/catalog`             | Retailer Wholesale Order Sheet | `ListViewTemplate`   | Fast SKU quantity stepper, unit pricing, real-time stock availability, instant checkout. |
| `/portal/invoices`            | Retailer Invoice History       | `ListViewTemplate`   | Downloadable GST invoices, payment status, credit limit usage breakdown.                 |
| `/portal/inquiries/new`       | Product Inquiry / Custom Quote | `FormTemplate`       | Custom volume inquiries, price negotiation requests, expected dispatch date.             |
| `/portal/supplier/po/[token]` | Supplier Magic Link PO Portal  | `DetailViewTemplate` | 8-col PO item acceptance & delivery date commitment + 4-col dispatch confirmation.       |

---

## 3. Four Core Template Specifications

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. ListViewTemplate                                                         │
│    [PageHeader: Title, Description, Stats, Primary Action]                 │
│    [Sticky Search & Filter Toolbar with View Toggles]                       │
│    [GlassCard: Data Table / Grid with Selectable Rows & Bulk Actions]       │
│    [Pagination & Row Count Bar]                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DetailViewTemplate                                                       │
│    [PageHeader: Title, StatusBadge, Back Link, Quick Actions]               │
│    ┌───────────────────────────────────┬─────────────────────────────────┐  │
│    │ 8-Column Main Content             │ 4-Column Sticky Side Panel      │  │
│    │ (Tabs, Overview Cards, History)   │ (Metadata, Actions, Audit Info) │  │
│    └───────────────────────────────────┴─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. FormTemplate                                                             │
│    [PageHeader: Title, Description, Back Link]                              │
│    [Grouped Form Sections (GlassCards with Headings & Clear Field Grid)]    │
│    [Sticky Bottom Bar: Discard, Status Feedback, Save Changes (Always Vis)] │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. DashboardTemplate                                                        │
│    [PageHeader: Welcome / Title, Global Filters (Date/Warehouse), Action]   │
│    [KPI Metric Row (4-6 GlassCards with Trends & Sparklines)]               │
│    [Responsive Grid: Main Chart/Feed (8-col) + Quick Insights (4-col)]      │
└─────────────────────────────────────────────────────────────────────────────┘
```
