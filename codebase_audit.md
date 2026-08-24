# WareFlow — Codebase Audit

> Auto-maintained by coding agents. Do not delete.
> This file is **rewritten in-place** — it reflects the system as it is NOW.
> History belongs in `memory.md`.

## Environment

| Property | Value                        |
| -------- | ---------------------------- |
| OS       | Windows 11 (NT 10.0.26200.0) |
| Shell    | PowerShell 5.1               |
| Node.js  | v24.16.0                     |
| pnpm     | 11.8.0                       |
| Python   | 3.14.6                       |
| Git      | 2.55.0.windows.4             |
| AI Agent | Antigravity IDE              |

## Stack & Versions

| Layer              | Technology                | Version   |
| ------------------ | ------------------------- | --------- |
| Frontend framework | Next.js (App Router)      | 16.3.1    |
| Frontend language  | TypeScript                | 5.9.3     |
| UI library         | React                     | 19.2.8    |
| CSS framework      | Tailwind CSS              | 4.3.3     |
| 3D WebGL Engine    | @react-three/fiber, three | 9.6.0     |
| 3D Helpers & Drei  | @react-three/drei         | 10.7.7    |
| Motion Stack (UI)  | motion (Framer Motion)    | 13.1.0    |
| Motion (Timelines) | gsap + ScrollTrigger      | 3.15.0    |
| Motion (Physics)   | @react-spring/web         | 10.1.2    |
| Motion (Lists)     | @formkit/auto-animate     | 0.10.0    |
| Motion (Micro SVG) | animejs                   | 3.2.2     |
| Icons & Utility    | lucide-react, clsx, cva   | latest    |
| Auth client        | Firebase Web SDK          | 12.17.1   |
| Test Runner (web)  | Vitest                    | 4.1.10    |
| Backend framework  | FastAPI                   | >=0.115.0 |
| Backend language   | Python                    | 3.14.6    |
| ORM                | SQLAlchemy                | >=2.0.0   |
| Migrations         | Alembic                   | >=1.13.0  |
| Validation         | Pydantic                  | >=2.0.0   |
| Auth (backend)     | Firebase Admin SDK        | >=6.0.0   |
| 2FA (TOTP & QR)    | pyotp + qrcode            | >=2.9.0   |
| Encryption         | cryptography              | >=42.0.0  |
| PDF Engine (api)   | ReportLab (platypus)      | >=4.0.0   |
| Excel Engine (api) | openpyxl                  | >=3.1.0,<4.0.0 |
| Background Worker  | APScheduler               | >=3.10.0,<4.0.0 |
| Test Runner (api)  | Pytest + pytest-cov       | >=8.0.0   |

## Services

| Service  | Role                              | Project/ID           | Region                 | Tier            | Connection Mode                                                                                 |
| -------- | --------------------------------- | -------------------- | ---------------------- | --------------- | ----------------------------------------------------------------------------------------------- |
| Supabase | Postgres DB (system of record)    | yappumzftktliybmztgg | Seoul (ap-northeast-2) | Free (t3a.nano) | **Split**: Port 6543 (transaction pooler) at runtime, Port 5432 (session pooler) for migrations |
| Firebase | Auth + Firestore (realtime push only) | wareflow-d17a4       | —                      | Free (Spark)    | Client SDK + Server Admin SDK                                                                   |
| Resend   | Email alerts (low-stock, reorder) | —                    | —                      | Free (3k/mo)    | HTTPS API                                                                                       |
| WhatsApp | Outbound B2B message alerts (Meta Cloud API) | —         | —                      | Free (1k convs/mo) | Meta Graph API (v21.0)                                                                          |
| SMS Provider | Outbound SMS fallback & critical alerts (Twilio / Indian Gateway) | — | — | Free (Trial credit) | Twilio REST API / HTTPS                                                                         |
| Groq     | LLM API (AI features)             | —                    | —                      | Free            | HTTPS API                                                                                       |
| Vercel   | Frontend hosting (Next.js)        | pending              | —                      | Free (Hobby)    | —                                                                                               |
| Render   | Backend hosting (FastAPI)         | pending              | —                      | Free            | —                                                                                               |

### Supabase Connection Modes Explained:

1. **Runtime (`DATABASE_URL`, Port 6543)**: Connects to Supavisor transaction pooler with SQLAlchemy `NullPool` and `connect_args={"prepare_threshold": None}`. Because Supabase handles pooling on the server, client-side pooling causes double-pooling and connection limits exhaustion. `NullPool` opens connections on demand and returns them immediately. Disabling prepared statement caching avoids named statement collisions across pooled connections.
2. **Migrations (`DIRECT_DATABASE_URL`, Port 5432)**: Connects to the session mode pooler (IPv4 compatible) to execute DDL operations and hold schema locks during Alembic migrations.

## Env Var Registry

### apps/web (Next.js Frontend) → `.env.local`

| Variable                                   | Description                       | Public?      |
| ------------------------------------------ | --------------------------------- | ------------ |
| `NEXT_PUBLIC_FIREBASE_API_KEY`             | Firebase web API key              | Yes (client) |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`         | Firebase auth domain              | Yes (client) |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID`          | Firebase project ID               | Yes (client) |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`      | Firebase storage bucket           | Yes (client) |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase messaging sender         | Yes (client) |
| `NEXT_PUBLIC_FIREBASE_APP_ID`              | Firebase app ID                   | Yes (client) |
| `NEXT_PUBLIC_SUPABASE_URL`                 | Supabase project URL              | Yes (client) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`            | Supabase anon key (RLS protected) | Yes (client) |
| `NEXT_PUBLIC_API_URL`                      | FastAPI backend URL               | Yes (client) |

### apps/api (FastAPI Backend) → `.env`

| Variable                            | Description                                   | Public?     |
| ----------------------------------- | --------------------------------------------- | ----------- |
| `DEBUG`                             | Enable debug mode                             | No          |
| `ALLOW_FIRST_SIGNUP`                | Allow first user to become Owner              | No          |
| `ALLOWED_ORIGINS`                   | CORS allowed origins list/csv                 | No          |
| `DATABASE_URL`                      | Supabase transaction pooler (port 6543)       | No (secret) |
| `DIRECT_DATABASE_URL`               | Supabase migration session pooler (port 5432) | No (secret) |
| `SUPABASE_URL`                      | Supabase project URL                          | No          |
| `SUPABASE_SERVICE_ROLE_KEY`         | Supabase admin secret key                     | No (secret) |
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Path to Firebase Admin SDK JSON               | No (secret) |
| `TOTP_ENCRYPTION_KEY`               | Secret encryption key for TOTP secrets/backup | No (secret) |
| `RESEND_API_KEY`                    | Resend email API key                          | No (secret) |
| `WHATSAPP_ACCESS_TOKEN`             | Meta WhatsApp Business Cloud API access token | No (secret) |
| `WHATSAPP_PHONE_NUMBER_ID`          | Meta WhatsApp registered phone number ID      | No          |
| `WHATSAPP_BUSINESS_ACCOUNT_ID`      | Meta WhatsApp Business Account ID (WABA)      | No          |
| `SMS_PROVIDER`                      | SMS provider name ('twilio')                  | No          |
| `SMS_PROVIDER_API_KEY`              | Generic SMS provider API key                  | No (secret) |
| `TWILIO_ACCOUNT_SID`                | Twilio Account SID                            | No (secret) |
| `TWILIO_AUTH_TOKEN`                 | Twilio Auth Token                             | No (secret) |
| `TWILIO_FROM_NUMBER`                | Twilio registered From phone number           | No          |
| `GROQ_API_KEY`                      | Groq LLM API key                              | No          |

## Layout & Shell Inventory (Step 4.6)

| Component        | File                                            | Surface & Treatment                                        | Motion Stack Behavior                                                                           |
| ---------------- | ----------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `AppLayout`      | `apps/web/components/AppLayout.tsx`             | Responsive shell, 360px viewport support, no x-scroll      | `AnimatePresence mode="wait"` + `PageTransition` wrapping route changes                         |
| `Sidebar`        | `apps/web/components/Sidebar.tsx`               | Frosted `GlassNav` floating above gradient mesh            | `layoutId="active-sidebar-pill"` active link glider, spring-driven mobile drawer slide-over     |
| `Topbar`         | `apps/web/components/Topbar.tsx`                | Frosted `GlassPanel` header with telemetry & notifications | `@formkit/auto-animate` for notification list item mutations, popover fade/scale                |
| `PageHeader`     | `apps/web/components/PageHeader.tsx`            | Standardized header with breadcrumb, badge & actions slot  | Static crisp layout, responsive flex-wrap for buttons                                           |
| `AnimatedNumber` | `apps/web/components/motion/AnimatedNumber.tsx` | Direct DOM node text tweening for numeric metrics          | Motion `animate()` tween on mount with snappy curve, instant render on `prefers-reduced-motion` |

## File Tree

```
wareflow/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI pipeline (lint, test, build)
├── docs/
│   ├── SITEMAP.md                  # Master screen-to-template registry across all 19 phases
│   ├── GLASS_GUIDE.md              # Liquid Glass & Specular Refraction architecture spec
│   └── ANIMATION_GUIDE.md          # 5-Engine motion layer domain & spring physics spec
├── package.json                    # Root monorepo config (pnpm workspaces)
├── pnpm-workspace.yaml             # Workspace definition
├── .prettierrc                     # Prettier config (line-length 100)
├── .prettierignore                 # Prettier ignore (skip api/, lockfiles)
├── .gitignore                      # Git ignore rules
├── docker-compose.yml              # Optional local Postgres (port 5433)
├── README.md                       # Quick-start guide
├── memory.md                       # Append-only project history
├── codebase_audit.md               # Living system state (this file)
├── scripts/
│   └── seed.py                     # Idempotent wholesale database seeding script
├── apps/
│   ├── web/                        # Next.js frontend (:3000)
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.ts
│   │   ├── postcss.config.mjs
│   │   ├── eslint.config.mjs       # ESLint + eslint-config-prettier
│   │   ├── vitest.config.mts       # Vitest unit test configuration
│   │   ├── middleware.ts           # Route guard and session cookie verification
│   │   ├── .env.example
│   │   ├── components/
│   │   │   ├── AppLayout.tsx       # Modern layout composing Sidebar, Topbar & PageTransitions
│   │   │   ├── Sidebar.tsx         # Liquid glass floating nav with layoutId active pill & mobile sheet
│   │   │   ├── Topbar.tsx          # Frosted GlassPanel header with telemetry & AutoAnimate notifications
│   │   │   ├── PageHeader.tsx      # Standardized title/description/badge/action slot header
│   │   │   ├── GradientBackdrop.tsx# Multi-orb GPU-accelerated animated gradient backdrop
│   │   │   ├── ThemeProvider.tsx   # React 19 useSyncExternalStore theme + accent context
│   │   │   ├── ThemeToggle.tsx     # Animated sun/moon liquid glass toggle button
│   │   │   ├── marketing/          # 3D & Animated Public Landing Page
│   │   │   │   ├── HeroScene.tsx      # Safe dynamic loader with reduced-motion bypass
│   │   │   │   ├── Hero3DCanvas.tsx   # React Three Fiber low-poly floating node scene
│   │   │   │   ├── Hero3DFallback.tsx # Accessible specular glass schematic fallback
│   │   │   │   ├── AceternityBeams.tsx# Dynamic light rays & ambient radiant grid
│   │   │   │   ├── BentoGrid.tsx      # GSAP ScrollTrigger 5-cell feature showcase
│   │   │   │   ├── MarketingNav.tsx   # Floating liquid glass navbar with CTAs
│   │   │   │   └── MarketingFooter.tsx# Clean luxury B2B footer
│   │   │   ├── motion/             # Layered motion stack infrastructure
│   │   │   │   ├── MotionProvider.tsx # Shared spring presets (snappy, glassMorph, gentle)
│   │   │   │   ├── GlassMotion.tsx    # Reusable wrappers (PageTransition, FadeIn, Stagger)
│   │   │   │   ├── AnimatedNumber.tsx # Direct-ref DOM numeric counter ticker
│   │   │   │   └── AnimeMicro.tsx     # anime.js SVG path morphing & micro-press engine
│   │   │   ├── templates/          # Four Locked Page Template System
│   │   │   │   ├── ListViewTemplate.tsx   # Sticky filter bar, data table, bulk actions, pagination
│   │   │   │   ├── DetailViewTemplate.tsx # 8-col main area + 4-col sticky metadata side panel
│   │   │   │   ├── FormTemplate.tsx       # Sectioned cards + sticky bottom action bar (⌘S)
│   │   │   │   ├── DashboardTemplate.tsx  # Top KPI metrics row + responsive 8/4 analytics grid
│   │   │   │   └── index.ts               # Barrel export for all templates
│   │   │   └── glass/              # Liquid Glass Component Primitives
│   │   │       ├── GlassButton.tsx # Flagship button with shifting specular refraction
│   │   │       ├── GlassCard.tsx   # Light-edge frosted card with header/content/footer
│   │   │       ├── GlassPanel.tsx  # Light-edge frosted container panel
│   │   │       ├── GlassModal.tsx  # Elevated glass dialog with motion choreography
│   │   │       ├── GlassDropdown.tsx# Floating elevated glass popover
│   │   │       ├── GlassInput.tsx  # Frosted input with glowing focus ring
│   │   │       ├── GlassBadge.tsx  # Luminous status badge / chip
│   │   │       └── index.ts        # Barrel export for all glass primitives
│   │   ├── lib/
│   │   │   ├── utils.ts            # cn() class merge helper (clsx + tailwind-merge)
│   │   │   ├── theme-accents.ts    # Curated 7-swatch WCAG AA calibrated palette
│   │   │   ├── api-client.ts       # Typed fetch wrapper with ApiError
│   │   │   ├── firebase-client.ts  # Safe Firebase Web SDK singleton (Google + Apple + Password)
│   │   │   ├── nav.ts              # Data-driven navigation schema & permission filter
│   │   │   └── __tests__/
│   │   │       ├── api-client.test.ts
│   │   │       ├── appearance.test.ts
│   │   │       ├── firebase-client.test.ts
│   │   │       ├── nav.test.ts
│   │   │       ├── theme.test.ts
│   │   │       ├── glass-primitives.test.tsx
│   │   │       ├── templates.test.tsx
│   │   │       ├── marketing.test.tsx
│   │   │       ├── products.test.tsx
│   │   │       ├── uom.test.tsx
│   │   │       ├── stock.test.tsx
│   │   │       ├── stock-analytics.test.tsx
│   │   │       ├── suppliers.test.tsx
│   │   │       ├── purchase-orders.test.tsx
│   │   │       ├── owner-dashboard-ui.test.tsx
│   │   │       ├── ar-aging-ui.test.tsx
│   │   │       └── dashboard-shell.test.tsx
│   │   └── app/                    # App Router pages
│   │       ├── layout.tsx          # Root layout with anti-flash script & ThemeProvider
│   │       ├── page.tsx            # Public-facing 3D animated marketing landing page
│   │       ├── globals.css         # Liquid glass design tokens & animations
│   │       ├── styleguide/page.tsx # Interactive glass primitives, templates & motion showcase
│   │       ├── (auth)/             # Authentication route group
│   │       │   ├── login/
│   │       │   │   ├── page.tsx    # Primary login (Google/Apple/Email) + 2FA redirect
│   │       │   │   └── 2fa/
│   │       │   │       └── page.tsx# 6-digit TOTP challenge + backup recovery code
│   │       │   └── logout/route.ts # Server-side logout & cookie clear
│   │       ├── api/auth/session/   # Session cookie handler (POST, PATCH for 2FA, DELETE)
│   │       │   └── route.ts
│   │       ├── dashboard/          # Authenticated workspace dashboard with live telemetry
│   │       │   └── page.tsx
│   │       ├── admin/
│   │       │   ├── analytics/
│   │       │   │   ├── stock/page.tsx # Stock Valuation & Composition Analytics dashboard
│   │       │   │   └── ar-aging/page.tsx # Accounts-Receivable Aging Report in 30/60/90+ day buckets
│   │       │   ├── inventory/page.tsx # Multi-warehouse inventory overview & batch inspector
│   │       │   ├── products/page.tsx  # Product catalog management
│   │       │   ├── categories/page.tsx# Category hierarchy editor
│   │       │   ├── suppliers/page.tsx # Vendor & Supplier CRUD management
│   │       │   ├── purchase-orders/page.tsx # Purchase Orders & Inbound Goods Receiving
│   │       │   ├── audit/page.tsx  # General Action Audit Log timeline & diff inspector
│   │       │   └── settings/
│   │       │       ├── appearance/page.tsx  # Theme mode (Light/Dark/System) + Accent picker
│   │       │       ├── audit-log/page.tsx   # Alias route for audit timeline
│   │       │       ├── staff/page.tsx       # Staff invite & role management UI
│   │       │       ├── permissions/page.tsx # Live role-permission matrix editor
│   │       │       └── security/page.tsx    # 2FA enrollment, QR code, backup codes
│   │       ├── portal/settings/
│   │       │   └── appearance/page.tsx      # Portal appearance settings alias
│   │       └── debug/              # Temporary handshake probe
│   │           └── page.tsx
│   └── api/                        # FastAPI backend (:8000)
│       ├── alembic.ini             # Alembic migration configuration
│       ├── alembic/                # Migration scripts
│       │   ├── env.py              # Migration runner with DIRECT_DATABASE_URL
│       │   ├── script.py.mako
│       │   └── versions/
│       │       ├── 0001_initial_schema_probe.py
│       │       ├── 0002_core_wholesale_schema.py
│       │       ├── 0003_extended_wholesale_schema.py
│       │       ├── 0004_user_profiles.py
│       │       ├── 0005_two_factor_auth.py
│       │       └── 0006_profile_appearance.py
│       ├── requirements.txt
│       ├── requirements-dev.txt    # ruff, pytest, pytest-cov, httpx
│       ├── pyproject.toml          # ruff & pytest config
│       ├── .env.example
│       ├── tests/                  # Pytest test suite (205 tests, 100% green)
│       │   ├── test_appearance_preferences.py
│       │   ├── test_di_and_health.py
│       │   ├── test_models.py
│       │   ├── test_extended_models.py
│       │   ├── test_seed.py
│       │   ├── test_profiles.py
│       │   ├── test_auth_and_guards.py
│       │   ├── test_staff_and_roles.py
│       │   ├── test_2fa.py
│       │   ├── test_audit_log.py
│       │   ├── test_products.py
│       │   ├── test_uom.py
│       │   ├── test_stock.py
│       │   ├── test_analytics_stock.py
│       │   ├── test_suppliers.py
│       │   ├── test_purchase_orders.py
│       │   ├── test_whatsapp_channel.py
│       │   └── test_stock_subscriptions_and_restock.py
│       └── app/
│           ├── main.py             # Application factory + ASGI entry
│           ├── api/
│           │   └── routers/        # HTTP layer (request/response only)
│           │       ├── health.py   # Liveness & DB connectivity (/health, /health/db)
│           │       ├── me.py       # Caller profile & permissions (/me)
│           │       ├── profiles.py # User profile, bootstrapping & preferences (/profiles/*)
│           │       ├── staff.py    # Staff invitation & roles (/staff/invite, /staff)
│           │       ├── roles.py    # Role permissions matrix (/roles, /permissions)
│           │       ├── two_factor.py# 2FA endpoints (/auth/2fa/*)
│           │       ├── audit.py    # Admin Audit Log endpoint (/admin/audit-log)
│           │       ├── categories.py# Product Category taxonomy (/categories)
│           │       ├── products.py # Wholesale Products & Pricing (/products)
│           │       ├── uom.py      # Unit of Measure & Conversions (/uom, /products/{id}/conversions)
│           │       ├── stock.py    # Multi-Warehouse Stock Overview, Adjustments, Ledger, Transfers, Recalls & Excel Exports (/stock/*, /stock/overview.xlsx, /stock/movements.xlsx)
│           │       ├── stock_analytics.py # Stock Valuation & Composition Analytics (/analytics/stock/*)
│           │       ├── analytics.py# Owner Dashboard, AR Aging, Weekly Insight & Excel Export (/analytics/owner-dashboard, /analytics/ar-aging, /analytics/ar-aging.xlsx, /analytics/weekly-insight)
│           │       ├── suppliers.py# Vendor / Supplier profiles (/suppliers)
│           │       ├── purchase_orders.py # Purchase Orders, Receiving & PDF Export (/purchase-orders, /purchase-orders/{id}/pdf)
│           │       ├── purchase_returns.py# Supplier Returns (/purchase-returns)
│           │       ├── retailers.py# Retailer accounts & credit limits (/retailers)
│           │       ├── customers.py# Direct end-customers & walk-in buyers (/customers)
│           │       ├── sales_orders.py# Sales Orders, Fulfillment & PDF Export (/sales-orders, /sales-orders/{id}/pdf, /sales-orders/{id}/pick-list.pdf, /sales-orders/{id}/packing-slip.pdf)
│           │       └── invoices.py # Tax Invoices, E-Invoicing & PDF Export (/invoices, /invoices/{id}/pdf)
│           ├── db/
│           │   ├── base.py         # SQLAlchemy DeclarativeBase
│           │   └── session.py      # Engine (NullPool) + get_db_session dependency
│           ├── models/             # Domain ORM models
│           │   ├── __init__.py
│           │   ├── profile.py      # Staff & Admin user profiles with 2FA & theme prefs
│           │   ├── uom.py          # Units of Measure & Conversions
│           │   ├── catalog.py      # Categories & Products
│           │   ├── warehouse.py    # Warehouses & StockBatches
│           │   ├── supplier.py     # Suppliers & PurchaseOrders
│           │   ├── retailer.py     # Retailers, SalesOrders (with buyer_type)
│           │   ├── billing.py      # Invoices, InvoiceItems, Payments
│           │   ├── returns.py      # SalesReturns, PurchaseReturns
│           │   ├── delivery.py     # Deliveries
│           │   ├── auth_rbac.py    # Roles, Permissions, RolePermissions
│           │   ├── portal.py       # Customers, Subscriptions, Magic Tokens, Inquiries
│           │   ├── recalls.py      # BatchRecalls, RecallAffectedOrders (in active use)
│           │   ├── inventory.py    # StockMovements (Append-only Ledger)
│           │   ├── notification.py # Alert Notifications
│           │   └── audit_and_settings.py # AdminAuditLog, BusinessSettings
│           ├── services/           # Business logic (depends on abstractions)
│           │   ├── alert_engine_service.py
│           │   ├── ar_aging_service.py
│           │   ├── audit_service.py
│           │   ├── business_settings_service.py
│           │   ├── customer_service.py
│           │   ├── export_service.py   # PDF & Excel generator (Pick Lists, Packing Slips, PO/SO/Invoice PDFs, Stock/Ledger/AR-Aging Excel workbooks)
│           │   ├── owner_dashboard_service.py
│           │   ├── pricing_strategy.py
│           │   ├── product_service.py
│           │   ├── profile_service.py
│           │   ├── purchase_order_service.py
│           │   ├── purchase_return_service.py
│           │   ├── retailer_service.py
│           │   ├── sales_order_service.py
│           │   ├── sales_return_service.py
│           │   ├── staff_service.py
│           │   ├── stock_service.py
│           │   ├── stock_analytics_service.py
│           │   ├── storage_service.py
│           │   ├── supplier_service.py
│           │   ├── transfer_service.py
│           │   ├── two_factor_service.py
│           │   └── uom_service.py
│           ├── repositories/
│           │   ├── interfaces/     # Protocol/ABC contracts
│           │   │   ├── alert_repository.py
│           │   │   ├── audit_repository.py
│           │   │   ├── business_settings_repository.py
│           │   │   ├── customer_repository.py
│           │   │   ├── product_repository.py
│           │   │   ├── profile_repository.py
│           │   │   ├── purchase_order_repository.py
│           │   │   ├── purchase_return_repository.py
│           │   │   ├── retailer_repository.py
│           │   │   ├── sales_order_repository.py
│           │   │   ├── sales_return_repository.py
│           │   │   ├── stock_analytics_repository.py
│           │   │   ├── stock_repository.py
│           │   │   ├── supplier_repository.py
│           │   │   ├── transfer_repository.py
│           │   │   └── uom_repository.py


│           │   │   ├── stock_analytics_repository.py
│           │   │   ├── supplier_repository.py
│           │   │   ├── purchase_order_repository.py
│           │   │   └── uom_repository.py
│           │   └── impl/           # Concrete implementations
│           │       ├── audit_repository.py
│           │       ├── product_repository.py
│           │       ├── profile_repository.py
│           │       ├── retailer_repository.py
│           │       ├── stock_repository.py
│           │       ├── stock_analytics_repository.py
│           │       ├── supplier_repository.py
│           │       ├── purchase_order_repository.py
│           │       └── uom_repository.py
│           ├── schemas/            # Pydantic request/response models
│           │   ├── audit.py
│           │   ├── categories.py
│           │   ├── products.py
│           │   ├── profile.py
│           │   ├── retailers.py
│           │   ├── staff.py
│           │   ├── stock.py
│           │   ├── stock_analytics.py
│           │   ├── suppliers.py
│           │   ├── purchase_orders.py
│           │   ├── two_factor.py
│           │   └── uom.py
│           └── core/
│               ├── config.py       # pydantic-settings configuration
│               ├── crypto.py       # Symmetric Fernet secret encryption at rest
│               ├── firebase.py     # Firebase Admin SDK singleton management
│               ├── security.py     # Firebase ID verification & require_permission guards
│               └── di.py           # Dependency injection wiring

```

## Database Schema (28 Tables Live)

| Table                     | Purpose                            | Columns                                                                                                                                                                                                                                                       | Indexes / Constraints                                                                   |
| ------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `admin_audit_log`         | Sensitive operation change audit   | `id` (PK, str), `actor_id`, `action`, `entity_type`, `entity_id`, `before_value` (JSON), `after_value` (JSON), `created_at`                                                                                                                                   | `INDEX(actor_id)`, `INDEX(entity_type)`, `INDEX(entity_id)`, `INDEX(created_at)`        |
| `profiles`                | User profiles with 2FA & theme     | `id` (PK, str), `email`, `display_name`, `avatar_url`, `phone`, `role_id` (FK), `is_active`, `totp_secret_encrypted`, `totp_enabled`, `backup_codes_encrypted`, `totp_enrolled_at`, `theme_preference`, `accent_color`, `created_at`, `updated_at`            | `UNIQUE(email)`, `INDEX(email)`, `INDEX(role_id)`, `FK(role_id -> roles.id RESTRICT)`   |
| `units_of_measure`        | Measurement units (pcs, box, kg)   | `id` (PK, str), `name`, `abbreviation`, `created_at`                                                                                                                                                                                                          | `UNIQUE(abbreviation)`                                                                  |
| `categories`              | Product hierarchy                  | `id` (PK, str), `name`, `parent_id` (FK), `created_at`                                                                                                                                                                                                        | `FK(parent_id -> categories.id)`                                                        |
| `products`                | Core product catalog               | `id` (PK, str), `sku`, `name`, `description`, `content_details`, `image_url`, `hsn_code`, `category_id` (FK), `base_uom_id` (FK), `unit`, `cost_price`, `wholesale_price`, `reorder_point`, `reorder_qty`, `barcode`, `is_active`, `created_at`, `updated_at` | `UNIQUE(sku)`, `INDEX(sku)`, `INDEX(barcode)`                                           |
| `product_uom_conversions` | Conversion factors per product     | `id` (PK, str), `product_id` (FK), `from_uom_id` (FK), `to_uom_id` (FK), `factor`, `created_at`                                                                                                                                                               | `UNIQUE(product_id, from_uom_id, to_uom_id)`                                            |
| `warehouses`              | Storage facilities                 | `id` (PK, str), `name`, `location`, `is_active`, `created_at`                                                                                                                                                                                                 | —                                                                                       |
| `stock_batches`           | FIFO batch tracking & expiry       | `id` (PK, str), `product_id` (FK), `warehouse_id` (FK), `batch_no`, `quantity`, `expiry_date`, `received_at`                                                                                                                                                  | `INDEX(product_id, warehouse_id)`                                                       |
| `suppliers`               | Manufacturers / vendors            | `id` (PK, str), `name`, `contact_person`, `phone`, `email`, `address`, `gstin`, `fssai_license_no`, `fssai_expiry_date`, `is_active`, `created_at`                                                                                                            | —                                                                                       |
| `purchase_orders`         | Procurement orders                 | `id` (PK, str), `po_number`, `supplier_id` (FK), `status` (enum), `order_date`, `expected_date`, `total_amount`, `created_at`                                                                                                                                 | `UNIQUE(po_number)`, `INDEX(po_number)`                                                 |
| `purchase_order_items`    | PO line items                      | `id` (PK, str), `po_id` (FK), `product_id` (FK), `qty_ordered`, `qty_received`, `unit_cost`, `uom_id` (FK)                                                                                                                                                    | `FK(po_id -> purchase_orders.id CASCADE)`                                               |
| `retailers`               | B2B wholesale buyers               | `id` (PK, str), `name`, `contact_person`, `phone`, `email`, `address`, `gstin`, `pricing_tier`, `credit_limit`, `credit_balance`, `is_active`, `created_at`                                                                                                   | —                                                                                       |
| `customers`               | Direct walk-in buyers              | `id` (PK, str), `name`, `phone`, `email`, `address`, `notes`, `created_at`                                                                                                                                                                                    | —                                                                                       |
| `sales_orders`            | Sales orders (retailer + customer) | `id` (PK, str), `so_number`, `buyer_type` (enum), `retailer_id` (FK), `customer_id` (FK), `status` (enum), `order_date`, `total_amount`, `created_at`                                                                                                         | `UNIQUE(so_number)`, `INDEX(so_number)`, `INDEX(retailer_id)`, `INDEX(customer_id)`     |
| `sales_order_items`       | SO line items                      | `id` (PK, str), `so_id` (FK), `product_id` (FK), `qty`, `unit_price`, `uom_id` (FK)                                                                                                                                                                           | `FK(so_id -> sales_orders.id CASCADE)`                                                  |
| `invoices`                | GST tax invoices                   | `id` (PK, str), `sales_order_id` (FK), `invoice_no`, `invoice_date`, `gst_rate`, `subtotal`, `tax_amount`, `total_amount`, `status` (enum), `e_invoice_irn`, `e_invoice_ack_no`, `e_invoice_qr_code`, `e_way_bill_no`, `created_at`                           | `UNIQUE(invoice_no)`, `INDEX(invoice_no)`, `INDEX(sales_order_id)`                      |
| `invoice_items`           | Frozen line items at invoice time  | `id` (PK, str), `invoice_id` (FK), `product_id` (FK), `product_name`, `hsn_code`, `qty`, `unit_price`, `tax_rate`, `tax_amount`, `total`, `uom_id` (FK)                                                                                                       | `INDEX(invoice_id)`, `INDEX(product_id)`                                                |
| `payments`                | Customer/Retailer payments         | `id` (PK, str), `invoice_id` (FK), `retailer_id` (FK), `customer_id` (FK), `amount`, `method` (enum), `paid_at`, `note`, `created_at`                                                                                                                         | `INDEX(invoice_id)`, `INDEX(retailer_id)`, `INDEX(customer_id)`                         |
| `sales_returns`           | Retailer goods returns             | `id` (PK, str), `sales_order_id` (FK), `retailer_id` (FK), `status` (enum), `reason`, `requested_at`                                                                                                                                                          | `INDEX(sales_order_id)`, `INDEX(retailer_id)`                                           |
| `sales_return_items`      | Sales return line items            | `id` (PK, str), `return_id` (FK), `product_id` (FK), `qty`, `batch_id` (FK), `condition` (enum)                                                                                                                                                               | `INDEX(return_id)`, `INDEX(product_id)`                                                 |
| `purchase_returns`        | Supplier goods returns             | `id` (PK, str), `purchase_order_id` (FK), `supplier_id` (FK), `status` (enum), `reason`, `requested_at`                                                                                                                                                       | `INDEX(purchase_order_id)`, `INDEX(supplier_id)`                                        |
| `purchase_return_items`   | Purchase return line items         | `id` (PK, str), `return_id` (FK), `product_id` (FK), `qty`, `batch_id` (FK), `reason`                                                                                                                                                                         | `INDEX(return_id)`, `INDEX(product_id)`                                                 |
| `deliveries`              | Dispatch and vehicle tracking      | `id` (PK, str), `sales_order_id` (FK), `driver_name`, `vehicle_no`, `status` (enum), `dispatched_at`, `delivered_at`, `notes`, `created_at`                                                                                                                   | `INDEX(sales_order_id)`                                                                 |
| `roles`                   | System roles                       | `id` (PK, str), `name`, `description`, `created_at`                                                                                                                                                                                                           | `UNIQUE(name)`, `INDEX(name)`                                                           |
| `permissions`             | Granular permission definitions    | `id` (PK, str), `code`, `description`, `created_at`                                                                                                                                                                                                           | `UNIQUE(code)`, `INDEX(code)`                                                           |
| `role_permissions`        | Role-to-permission mapping         | `role_id` (PK, FK), `permission_id` (PK, FK)                                                                                                                                                                                                                  | `PK(role_id, permission_id)`                                                            |
| `stock_subscriptions`     | Back-in-stock alert requests       | `id` (PK, str), `retailer_id` (FK), `product_id` (FK), `channel_preference` (enum), `is_active`, `notified_at`, `created_at`                                                                                                                                  | `INDEX(retailer_id)`, `INDEX(product_id)`                                               |
| `supplier_access_tokens`  | Single-purpose magic link tokens   | `id` (PK, str), `supplier_id` (FK), `purchase_order_id` (FK), `token`, `expires_at`, `created_at`                                                                                                                                                             | `UNIQUE(token)`, `INDEX(token)`, `INDEX(supplier_id)`, `INDEX(purchase_order_id)`       |
| `product_inquiries`       | Portal inquiries & quotes          | `id` (PK, str), `product_id` (FK), `retailer_id` (FK), `customer_id` (FK), `message`, `status` (enum), `response`, `created_at`, `responded_at`                                                                                                               | `INDEX(product_id)`, `INDEX(retailer_id)`, `INDEX(customer_id)`                         |
| `batch_recalls`           | Batch defect & recall records      | `id` (PK, str), `batch_id` (FK), `product_id` (FK), `reason`, `severity` (enum), `status` (enum), `initiated_at`, `resolved_at`                                                                                                                               | `INDEX(batch_id)`, `INDEX(product_id)`                                                  |
| `recall_affected_orders`  | Traceability for recalled orders   | `id` (PK, str), `recall_id` (FK), `sales_order_id` (FK), `retailer_id` (FK), `customer_id` (FK), `notified_at`                                                                                                                                                | `INDEX(recall_id)`, `INDEX(sales_order_id)`, `INDEX(retailer_id)`, `INDEX(customer_id)` |
| `stock_movements`         | Append-only inventory ledger       | `id` (PK, str), `product_id` (FK), `warehouse_id` (FK), `batch_id` (FK), `type` (enum), `quantity`, `reference_type`, `reference_id`, `created_by`, `created_at`                                                                                              | `INDEX(product_id)`, `INDEX(warehouse_id)`, `INDEX(created_at)`                         |
| `notifications`           | System alerts & notices            | `id` (PK, str), `user_id`, `type`, `title`, `body`, `is_read`, `created_at`                                                                                                                                                                                   | `INDEX(user_id)`                                                                        |
| `business_settings`       | Single-row business profile & GST  | `id` (PK, str), `business_name`, `gstin`, `fssai_license_no`, `fssai_expiry_date`, `address`, `phone`, `email`, `updated_at`                                                                                                                                  | —                                                                                       |

## API Endpoints

| Method | Path                                   | Description                                         | Auth Required                   |
| ------ | -------------------------------------- | --------------------------------------------------- | ------------------------------- |
| GET    | `/health`                              | Liveness probe returning status: "ok"               | No                              |
| GET    | `/health/db`                           | Database probe executing `SELECT 1` via connection  | No                              |
| GET    | `/me`                                  | Get caller identity, role, permissions & theme      | Yes (Bearer / Cookie)           |
| POST   | `/profiles/bootstrap`                  | Bootstrap/retrieve authenticated Firebase profile   | Yes (Bearer / Cookie)           |
| GET    | `/profiles/me`                         | Get current user profile and role permissions       | Yes (Bearer / Cookie)           |
| PATCH  | `/profiles/preferences`                | Update user theme mode and accent color             | Yes (Bearer / Cookie)           |
| POST   | `/staff/invite`                        | Invite new staff member with assigned role          | Yes (`staff:manage` / Owner)    |
| GET    | `/staff`                               | List all staff members and active roles             | Yes (`staff:view`)              |
| PATCH  | `/staff/{id}/role`                     | Update a staff member's assigned role               | Yes (`staff:manage`)            |
| PATCH  | `/staff/{id}/status`                   | Toggle staff account active/suspended state         | Yes (`staff:manage`)            |
| GET    | `/roles`                               | List all defined roles with permission codes        | Yes (Authenticated)             |
| GET    | `/permissions`                         | List all defined system permissions                 | Yes (Authenticated)             |
| PATCH  | `/roles/{id}/permissions`              | Update permission matrix mapping for a role         | Yes (`settings:manage` / Owner) |
| GET    | `/auth/2fa/status`                     | Get 2FA status, requirement policy, backup count    | Yes (Authenticated)             |
| POST   | `/auth/2fa/enroll`                     | Generate TOTP secret, QR code, and 10 backup codes  | Yes (Authenticated)             |
| POST   | `/auth/2fa/verify-enrollment`          | Confirm 6-digit TOTP code and activate 2FA          | Yes (Authenticated)             |
| POST   | `/auth/2fa/verify`                     | Verify 2FA challenge via TOTP or single-use backup  | Yes (Authenticated)             |
| POST   | `/auth/2fa/disable`                    | Disable 2FA after verifying code confirmation       | Yes (Authenticated)             |
| POST   | `/auth/2fa/regenerate-backup-codes`    | Regenerate 10 fresh recovery backup codes           | Yes (Authenticated)             |
| GET    | `/admin/audit-log`                     | Get paginated admin action audit logs with diffs    | Yes (`audit:view` / Owner)      |
| GET    | `/categories`                          | List all product categories                         | Yes (Authenticated)             |
| GET    | `/categories/{id}`                     | Get product category by ID                          | Yes (Authenticated)             |
| POST   | `/categories`                          | Create new product category                         | Yes (`inventory:manage`)        |
| PATCH  | `/categories/{id}`                     | Update product category metadata                    | Yes (`inventory:manage`)        |
| DELETE | `/categories/{id}`                     | Delete product category                             | Yes (`inventory:manage`)        |
| GET    | `/products`                            | List all wholesale products with pricing & filters  | Yes (Authenticated)             |
| POST   | `/products`                            | Create wholesale product entity (SKU unique)        | Yes (`inventory:manage`)        |
| GET    | `/products/{id}`                       | Get wholesale product details                       | Yes (Authenticated)             |
| PATCH  | `/products/{id}`                       | Update product metadata and pricing                 | Yes (`inventory:manage`)        |
| PATCH  | `/products/{id}/price`                 | Update product selling/cost prices (audited)        | Yes (`inventory:manage`)        |
| POST   | `/products/{id}/deactivate`            | Deactivate product (guarded against open orders)    | Yes (`inventory:manage`)        |
| POST   | `/products/{id}/image`                 | Upload product image (JPEG/PNG/WebP <=5MB)          | Yes (`inventory:manage`)        |
| DELETE | `/products/{id}`                       | Permanently delete product record                   | Yes (`inventory:manage`)        |
| GET    | `/uom`                                 | List all registered units of measure                | Yes (Authenticated)             |
| POST   | `/uom`                                 | Create new unit of measure                          | Yes (`inventory:manage`)        |
| GET    | `/products/{id}/conversions`           | List packaging conversion ratios for a product      | Yes (Authenticated)             |
| POST   | `/products/{id}/conversions`           | Create packaging conversion factor                  | Yes (`inventory:manage`)        |
| DELETE | `/products/{id}/conversions/{cid}`     | Remove packaging conversion factor                  | Yes (`inventory:manage`)        |
| GET    | `/products/{id}/convert`               | Convert quantity across packaging units             | Yes (Authenticated)             |
| GET    | `/stock/overview`                      | Multi-warehouse inventory overview & health badges  | Yes (Authenticated)             |
| GET    | `/stock/warehouses`                    | List active storage facilities & warehouses         | Yes (Authenticated)             |
| GET    | `/stock/expiring`                      | List batches expiring within specified horizon      | Yes (Authenticated)             |
| GET    | `/products/{id}/stock`                 | Product stock breakdown across warehouses & batches | Yes (Authenticated)             |
| GET    | `/analytics/stock/value-summary`       | Total stock valuation, category & warehouse share   | Yes (Authenticated)             |
| GET    | `/analytics/stock/health-distribution` | Count of products in each stock health band         | Yes (Authenticated)             |
| GET    | `/analytics/stock/top-value-products`  | Top products by capital tied-up and quantity        | Yes (Authenticated)             |
| GET    | `/analytics/stock/expiry-timeline`     | Forward-looking 6-window batch expiry breakdown     | Yes (Authenticated)             |
| GET    | `/analytics/stock/spend-trend`         | Monthly total spend on received stock (12M horizon) | Yes (Authenticated)             |
| GET    | `/analytics/stock/spend-by-supplier`   | Ranked procurement spend by vendor / supplier       | Yes (Authenticated)             |
| GET    | `/analytics/stock/spend-by-category`   | Ranked procurement spend by product category        | Yes (Authenticated)             |
| GET    | `/analytics/stock/avg-cost-trend`      | Product cost price movement and price creep tracker | Yes (Authenticated)             |
| GET    | `/retailers`                           | List all wholesale retailers                        | Yes (Authenticated)             |
| POST   | `/retailers`                           | Create wholesale retailer profile with pricing tier | Yes (`inventory:manage`)        |
| GET    | `/retailers/{id}`                      | Get single retailer profile details                 | Yes (Authenticated)             |
| PATCH  | `/retailers/{id}`                      | Update retailer information or status               | Yes (`inventory:manage`)        |
| PATCH  | `/retailers/{id}/credit-limit`         | Update retailer credit limit (audited)              | Yes (`settings:manage`)         |
| POST   | `/retailers/{id}/calculate-pricing`    | Calculate tier-discounted price per quantity        | Yes (Authenticated)             |
| GET    | `/sales-orders`                        | List sales orders with status/retailer filters      | Yes (`orders:view`)             |
| POST   | `/sales-orders`                        | Create new draft sales order                        | Yes (`orders:create`)           |
| GET    | `/sales-orders/{id}`                   | Get sales order detail with line items & tier prices| Yes (`orders:view`)             |
| POST   | `/sales-orders/{id}/confirm`           | Credit check + FIFO stock deduction confirmation    | Yes (`orders:create`)           |
| PATCH  | `/sales-orders/{id}/status`            | Advance order fulfillment (packed, shipped, etc.)   | Yes (`orders:create`)           |
| GET    | `/sales-returns`                       | List retailer sales returns (RMA In) with filters   | Yes (`orders:view`)             |
| POST   | `/sales-returns`                       | Request retailer sales return (RMA In)              | Yes (`orders:create`)           |
| GET    | `/sales-returns/{id}`                  | Get sales return record with condition assessment   | Yes (`orders:view`)             |
| PATCH  | `/sales-returns/{id}/approve`          | Approve return & restock resellable items (RETURN_IN)| Yes (`inventory:manage`)       |
| GET    | `/customers`                           | List registered walk-in and direct buyers           | Yes (Authenticated)             |
| POST   | `/customers`                           | Register new direct customer (standard pricing)     | Yes (`orders:create`)           |
| GET    | `/customers/{id}`                      | Get customer profile details                        | Yes (Authenticated)             |
| PATCH  | `/customers/{id}`                      | Update customer profile and contact info            | Yes (`orders:create`)           |
| DELETE | `/customers/{id}`                      | Delete customer (guarded against active orders)     | Yes (`orders:create`)           |
| GET    | `/suppliers`                           | List goods suppliers with search & active filters   | Yes (Authenticated)             |
| POST   | `/suppliers`                           | Register new supplier with GSTIN validation         | Yes (`inventory:manage`)        |
| GET    | `/suppliers/{id}`                      | Retrieve details for a single supplier              | Yes (Authenticated)             |
| PATCH  | `/suppliers/{id}`                      | Update supplier details, contacts, or active status | Yes (`inventory:manage`)        |
| POST   | `/retailers/{id}/invite-portal-access` | Generate invite link and token for retailer portal  | Yes (`retailers:manage` / Owner)|
| POST   | `/portal/auth/bootstrap`               | Bind Firebase token & invite to retailer user       | Yes (Firebase Token)            |
| GET    | `/portal/me`                           | Get authenticated retailer identity & credit line   | Yes (Retailer Portal Only)      |
| GET    | `/portal/catalog`                      | List catalog with tier pricing & privacy stock bands| Yes (Retailer Portal Only)      |
| GET    | `/portal/categories`                   | List categories for wholesale catalog filters       | Yes (Retailer Portal Only)      |
| POST   | `/portal/orders`                       | Submit wholesale sales order (auto-confirm/draft)   | Yes (Retailer Portal Only)      |
| GET    | `/portal/orders`                       | List sales orders strictly scoped to caller retailer| Yes (Retailer Portal Only)      |
| GET    | `/portal/orders/{id}`                  | Get order details (strictly scoped data wall)       | Yes (Retailer Portal Only)      |
| GET    | `/portal/invoices`                     | List invoices strictly scoped to caller retailer    | Yes (Retailer Portal Only)      |
| GET    | `/portal/invoices/{id}`                | Get invoice details (strictly scoped data wall)     | Yes (Retailer Portal Only)      |
| GET    | `/portal/ledger`                       | Get AR ledger statement strictly scoped to retailer | Yes (Retailer Portal Only)      |
| POST   | `/portal/inquiries`                    | Submit product inquiry or bulk quote request        | Yes (Retailer Portal Only)      |
| GET    | `/portal/inquiries`                    | List inquiries strictly scoped to caller retailer   | Yes (Retailer Portal Only)      |
| GET    | `/inquiries`                           | List all product inquiries with status/product filter| Yes (Staff Only)                |
| PATCH  | `/inquiries/{id}/respond`              | Respond to inquiry & dispatch notification to buyer | Yes (Staff Only)                |
| POST   | `/sales-orders/{id}/delivery`          | Assign driver & vehicle to packed sales order       | Yes (`orders:create`)           |
| GET    | `/sales-orders/{id}/delivery`          | Get delivery dispatch record for sales order        | Yes (`orders:view`)             |
| GET    | `/deliveries`                          | List dispatch records with status/driver filters    | Yes (`orders:view`)             |
| GET    | `/deliveries/{id}`                     | Get delivery detail with buyer & address context    | Yes (`orders:view`)             |
| PATCH  | `/deliveries/{id}/status`              | Update delivery transit status & auto-advance SO    | Yes (`orders:create`)           |
| GET    | `/sales-orders/{id}/packing-slip.pdf`  | Customer-facing delivery manifest PDF (zero prices) | Yes (`orders:view`)             |
| GET    | `/sales-orders/{id}/pick-list.pdf`     | Warehouse staff checkbox pick list PDF (zero prices)| Yes (`orders:view`)             |
| GET    | `/notifications`                       | List paginated notifications with unread count      | Yes (Authenticated User)        |
| PATCH  | `/notifications/{id}/read`             | Mark single notification as read                    | Yes (Authenticated User)        |
| PATCH  | `/notifications/read-all`              | Mark all unread notifications as read               | Yes (Authenticated User)        |
| GET    | `/products/{id}/forecast`              | Statistical demand forecast for a product (24h cache)| Yes (Authenticated User)       |
| GET    | `/analytics/forecast-summary`          | Catalog-wide demand forecast summary & top/slow movers| Yes (`inventory:view`)         |
| GET    | `/analytics/reorder-suggestions`       | Actionable low-stock suggestions with lead time buffer| Yes (Authenticated User)       |
| POST   | `/analytics/reorder-suggestions/create-po` | Auto-generate pre-filled draft PO from suggestions  | Yes (Authenticated User)       |
| GET    | `/analytics/dead-stock`                | Stagnant/dead stock detection ranked by tied-up capital| Yes (Authenticated User)       |
| GET    | `/analytics/anomalies/order/{order_id}`| Detect 3σ statistical anomalies for sales order lines | Yes (Authenticated User)        |
| GET    | `/analytics/weekly-insight`            | 7-day executive AI intelligence narrative (7d cache)  | Yes (Authenticated User)        |
| GET    | `/analytics/dashboard`                 | Single round-trip owner KPI metrics, movement & queues| Yes (Authenticated User)        |
| GET    | `/analytics/ar-aging`                  | Bucketed accounts receivable aging (Current, 30/60/90+)| Yes (`invoices:view`)           |

## Architecture Layers

```
┌──────────────────────────────────────────────────┐
│  Routers (app/api/routers/)                       │
│  HTTP concerns only: parse request, return response│
│  ↓ calls                                          │
├──────────────────────────────────────────────────┤
│  Services (app/services/)                         │
│  Business logic, orchestration, validation        │
│  ↓ depends on (interfaces)                        │
├──────────────────────────────────────────────────┤
│  Repository Interfaces (app/repositories/interfaces/) │
│  Protocol/ABC contracts — what data ops exist      │
│  ↑ implemented by                                 │
├──────────────────────────────────────────────────┤
│  Repository Impls (app/repositories/impl/)         │
│  Concrete data access (SQLAlchemy, InMemory, etc.) │
│  Wired via core/di.py                              │
├──────────────────────────────────────────────────┤
│  Schemas & Models (app/schemas/, app/models/)     │
│  Pydantic request/response & SQLAlchemy ORM models │
├──────────────────────────────────────────────────┤
│  Core & DB (app/core/, app/db/)                    │
│  Config, crypto, security, DI wiring, DB session   │
└──────────────────────────────────────────────────┘
```

**Rule:** Routers NEVER import repositories directly. Only services.

## Decisions

| Decision                                | Rationale                                                                                                                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Graph BFS Packaging Traversal           | `UomService` resolves multi-level packaging hierarchies (Pallet->Case->Pack->Piece) & inverses using graph traversal                                                                              |
| Strict Base UoM Stock Ledger            | `stock_movements` and `stock_batches` strictly store quantities in product's `base_uom_id` via `convert_to_base_uom`                                                                              |
| Graceful 1:1 Base Fallback              | Products with no custom packaging conversion defined trade 1:1 in base unit gracefully without runtime error                                                                                      |
| Stock Analytics Calculation Engine      | `StockAnalyticsService` computes live balance valuations, category allocations, warehouse holdings, and 6-window expiry horizons with full parity between SQLAlchemy and InMemory implementations |
| UomRepository Protocol (DIP)            | `UomService` depends exclusively on `UomRepositoryInterface` Protocol, allowing seamless in-memory testing                                                                                        |
| ProductRepository Protocol (DIP)        | `ProductService` depends exclusively on `ProductRepositoryInterface` (Protocol), never importing DB sessions                                                                                      |
| SupplierRepository Protocol (DIP)       | `SupplierService` depends exclusively on `SupplierRepositoryInterface` Protocol, enforcing unique company names & 15-char Indian GSTIN verification                                               |
| Natural Key SKU Uniqueness              | Enforced at both database layer and domain service layer with friendly 409 Conflict error details                                                                                                 |
| Single Door Rule for Inbound Stock      | Receiving a Purchase Order (`POST /purchase-orders/{id}/receive`) is the sole entry point for new batch stock and `stock_movements(type=in)` ledger entries                                       |
| Immediate Return Stock Deduction        | Requesting a supplier return (`POST /purchase-returns`) immediately decrements on-hand stock via `stock_movements(type=return_out)` as physical goods depart the warehouse                        |
| Vendor Credit Note Settlement           | Transitioning a supplier return to `credited` requires `credit_note_ref` to link physical outbound RMA goods to vendor financial credits                                                          |
| PurchaseReturnRepository Protocol (DIP) | `PurchaseReturnService` depends exclusively on `PurchaseReturnRepositoryInterface` Protocol, guaranteeing zero DB coupling                                                                        |
| Open Orders Deactivation Guard          | Products linked to open Purchase Orders or Sales Orders cannot be deactivated to prevent broken fulfillment pipelines                                                                             |
| Business Settings Protocol (DIP)        | `BusinessSettingsService` depends exclusively on `BusinessSettingsRepositoryInterface` Protocol, guaranteeing complete database abstraction                                                         |
| Open/Closed Alert Engine (OCP)          | `AlertEngineService` consumes extensible `AlertRule` strategies (such as `ExpiringLicenseRule`), allowing new compliance rules without modifying core engine logic                                |
| Human Decision Guard for Expired FSSAI  | Expired supplier licenses trigger a non-blocking confirmation dialog requiring explicit user risk acknowledgment before PO creation, balancing regulatory safety with practical operations        |
| RetailerRepository Protocol (DIP)       | `RetailerService` depends exclusively on `RetailerRepository` Protocol, enforcing unique retailer naming, phone/email validation, and complete mockability                                          |
| Pluggable Pricing Strategy (OCP)        | `PricingEngineService` coordinates extensible `PricingStrategy` implementations (`Standard`, `Silver`, `Gold`, `TieredDiscount`), allowing custom tiers with zero sales order engine modifications |
| Credit Check Order of Operations        | Credit verification (`credit_balance + order_total <= credit_limit`) strictly executes before inventory inspection; shortfalls abort with zero batch alterations    |
| FIFO Oldest-Expiry Stock Deduction      | Confirming an order is the sole outbound path, consuming batches oldest-expiry-first (`expiry_date ASC nulls last, received_at ASC`) with atomic `StockMovement(type=out)` |
| Compensating Cancellation Adjustments   | Cancelling a confirmed sales order creates `StockMovement(type=adjustment, reference_type="sales_order_cancellation")` rows and refunds credit, preserving ledger  |
| Condition-Based Return Restocking       | `SalesReturnService` enforces that resellable items restock batches with `RETURN_IN` movements, while damaged items are tracked for loss/credit without altering sellable inventory batches |
| CustomerRepository Protocol (DIP)       | `CustomerService` depends exclusively on `CustomerRepositoryInterface` Protocol, guaranteeing complete database abstraction and zero ORM coupling in unit tests |
| Shared Sales Order Pipeline for Buyers  | Direct customers reuse the exact same order pipeline (`buyer_type=customer`), bypassing credit checks (assumed cash/UPI immediate settlement) while honoring standard pricing and FIFO stock deductions |
| Single Legitimate Manual Stock Path     | Manual stock adjustments (`POST /stock/adjustments`) require mandatory reason taxonomy (`damage`, `loss`, `recount`, `other`) and are the sole direct stock modification write path |
| Recount Permission Role Gate (RBAC)     | The `recount` adjustment reason strictly enforces `stock.recount` permission code or `Owner` role, preventing unauthorized floor staff from adding arbitrary inventory balances |
| Human Label Ledger Synthesis            | `StockService.list_movements` enriches append-only movements with contextual activity labels (PO receipt, SO dispatch, return, recount, damage note) directly in the API |
| Atomic Paired-Movement Transfers        | `TransferService` executes inter-warehouse stock relocation as a single atomic transaction: source `StockMovement(type=out)` paired with destination `StockMovement(type=in)`, preserving batch identity and rollback safety |
| Dynamic Lead-Time Buffered Reordering   | `ReorderSuggestionService` calculates optimal PO batches `max(reorder_qty, ceil(daily_demand * lead_time_days))` integrated with Step 14.1 forecasting and classifies urgency tiers (`critical`, `high`, `medium`) |
| Pre-filled PO from AI Suggestions       | `POST /analytics/reorder-suggestions/create-po` directly bridges analytics insights to pre-filled draft Purchase Orders with zero manual item re-entry |
| Dead Stock Capital Prioritization       | `DeadStockService` scans inactive catalog inventory over configurable trailing windows ($N$ days) and ranks stagnant stock descending by locked working capital ($Q \times \text{cost}$) |
| Recall Outbound Ledger Traceability     | `RecallService` automatically traces every affected sales order and buyer via `stock_movements(type=out, reference_type='sales_order')` references, eliminating separate manual recall tracking logs |
| Unsellable Recalled Stock Isolation     | Recalled batches are dynamically excluded from FIFO sales deductions without deleting historical batch records, keeping complete compliance auditability intact |
| Notification Engine Zero-Duplication   | Recall broadcasts reuse the existing notification engine / audit log infrastructure with zero new messaging channel code |
| Availability Band Privacy Rule          | Exact warehouse stock counts are strictly obscured from retailers; `PortalCatalogProductResponse.availability` returns `"Available" \| "Low" \| "Out"` to preserve warehouse confidentiality |
| Zero Duplicate Catalog Pricing Logic    | `PortalAuthService` reuses `PricingEngineService.calculate_line_price` with the retailer's tier claim directly, guaranteeing identical price computation between catalog browsing and sales order checkout |
| Invoice Numbering Verbatim Sequence     | Indian financial-year prefixed sequential gap-free numbering (`INV/YYYY-YY/0001`, e.g. `INV/2026-27/0001`) enforced via repository regex sequence parser |
| Frozen Invoicing Accounting Document    | Invoice is a frozen snapshot where line prices, HSN codes, product names, GST rates (18%), and totals are permanently locked at issuance time, immune to later catalog edits |
| Idempotent Order Invoicing              | Re-requesting invoice generation for an already-invoiced sales order returns the existing invoice without duplicate creation or sequence number gaps |
| Invoice Status Guardrail                | Invoicing is strictly limited to sales orders in status `confirmed` or later (`confirmed`, `packed`, `shipped`, `delivered`). Draft or cancelled orders are rejected |
| InvoiceRepository Protocol (DIP)        | `InvoiceService` depends exclusively on `InvoiceRepositoryInterface` Protocol, guaranteeing zero DB coupling |
| Non-Blocking Advisory 3σ Anomaly Guard  | `AnomalyDetectionService` flags unusual sales order line quantities exceeding historical $\text{mean} + 3\sigma$ as an advisory warning badge for staff review, but never automatically blocks order creation or confirmation |
| Grounded Weekly AI Insight & Fallback   | `InsightNarratorService` generates 2-3 sentence executive summaries grounded strictly on verified trailing numbers with 7-day cache and a deterministic rule-based template fallback when `GROQ_API_KEY` is unset |
| Cloud Storage Validation & Upload | Supabase Storage `product-images` bucket handles catalog media with strict <=5MB and JPEG/PNG/WebP validation |
| Universal DataTable Rule | All future list and ledger screens must use `DataTable`; responsive mobile card-view is automatic below 768px |
| Low-Power Glass Degradation | Low memory (<4GB), cores (<=4), or reduced-transparency drops expensive blurs to flat translucency at 60fps |
| Motion Signals State Change | Motion is strictly reserved to draw attention to STATE CHANGES (active link shift, number count-up, table mutation) |
| Direct-Ref Numeric Tickers | Direct DOM node mutation during number count-up guarantees 60fps performance without React re-render cascades |
| Single Standard PageHeader | Every page consumes standard `PageHeader` for typographic consistency, breadcrumbs, and responsive action layout |
| Performance-Budget Gates Motion | 3D scenes lazy-load dynamically with zero SSR, cap DPR to 1.5, and degrade immediately on low-power devices |
| First-Class Reduced Motion | Every animation (R3F, GSAP ScrollTrigger, CSS keyframes, motion springs) honors `prefers-reduced-motion: reduce` |
| Dynamic Site-Wide Background | 4-orb GPU-accelerated animated gradient mesh with anti-banding noise provides alive visual backdrop to all pages |
| Locked Four Page Templates | Every screen across all 19 phases must map strictly to ListView, DetailView, Form, or DashboardTemplate |
| 12-Column Responsive Grid System | Strict 12-col grid + 4px base spacing scale modeled on Linear, Stripe Dashboard, and Notion benchmarks |
| Narrowly Scoped anime.js Motion | `animejs` added as 5th motion engine strictly for SVG path draw/morph and micro-press physics (0 library overlap) |
| Theme Mode + Accent Locked Tokens | Theme mode (Light/Dark/System) + Accent are the ONLY customizable tokens; the black/white glass foundation stays |
| Curated Pre-Tested Swatches | Scoped to 7 verified swatches to guarantee WCAG AA contrast against both true black and white backgrounds |
| Dual-Storage Persistence | Preferences stored in `localStorage` for 0-latency paint and in Postgres `profiles` to follow users on login |
| Liquid Glass Default Primitives | Real specular edge refraction & tactile spring compression as DEFAULT for all buttons and interactive controls |
| Surface-Area Inverted Refraction | Refraction strength scales inversely with element size: full refraction for buttons/modals, light-edge for panels |
| Segregated Motion Stack Ownership | `motion` for UI transitions, `gsap` for marketing timelines, `@formkit/auto-animate` for lists, `@react-spring` |
| Liquid Glass Visual Identity | Black/white foundation + single Electric Violet (`#7C3AED`/`#8B5CF6`) accent + frosted glass overlays & blooms |
| Real Persisted Theme Toggle | Explicit user choice stored in `localStorage` (`wareflow-theme`), defaulting to OS preference on 1st visit |
| GPU Gradient Backdrop | Fixed multi-orb CSS backdrop drifting smoothly over noise grain layer, eliminating OLED banding |
| Supabase = DB only | Need SQL joins, transactions, referential integrity for accounting |
| Firebase = Auth only | Best-in-class free Google/Apple Sign-In with minimal setup |
| In-House RFC 6238 TOTP 2FA | Standard TOTP avoids paid Firebase SMS MFA costs while delivering universal Google Authenticator/Authy support |
| Symmetric Secret Encryption | TOTP secrets and backup codes encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256) |
| Single-Use Atomic Backup Codes | 10 backup codes generated at enrollment, permanently consumed upon single use |
| Operational Staff Exemption | Warehouse/Sales staff exempt from mandatory 2FA to prevent delays during high-speed packing and shop-floor runs |
| Paired AR Ledger Invariant | Invoice confirmation increases `retailers.credit_balance` by total; payment decreases `retailers.credit_balance` by payment amount (`credit_balance` is balance owed) |
| Chronological Statement | `LedgerService` dynamically builds statement with running balances matching stored `retailers.credit_balance` |
| Overdue Detection Window | Configurable due-date window (default 30 days) scans and transitions unpaid/partially paid invoices past due date to `overdue` |
| Mandatory HSN Pre-flight | Generating an invoice blocks with HTTP 422 if any product lacks a valid HSN code, preventing GST filing rejections |
| Statutory E-Invoice (IRN) | Generates 64-hex SHA-256 IRN, 16-digit Ack No, and signed QR code via authorized GSP/IRP sandbox provider |
| Statutory E-Way Bill | Generates 12-digit E-Way Bill for road transit with distance-based validity (1 day per 200 km) for goods movement |
| Turnover Threshold Deferral | E-invoicing applies to businesses above ₹5 Cr turnover; full sandbox & zero-cost deferred mode available for smaller businesses |
| General Admin Action Audit Log | `admin_audit_log` records immutable before/after diffs for sensitive actions (price, credit, permissions, staff, payments, e-invoicing) |
| Humanized Audit Narratives | `AuditService` synthesizes readable business sentences from raw diffs while preserving JSON diff inspection |
| SOLID from day one | Prevents spaghetti; makes testing and swapping implementations easy |
| Application factory | Testable app creation, supports different configs per environment |
| pydantic-settings | Single source of truth for env vars, validates on startup |
| Prettier (web) | Consistent formatting, 100 char line width matching ruff |
| Ruff (api) | Fast Python linter+formatter, line-length 100, rules: E/W/F/I/B/UP/SIM/N |
| eslint-config-prettier | Disables ESLint rules that conflict with Prettier |
| Local PG on 5433 | Avoid conflicts with system Postgres; Supabase stays primary |
| Typed API Client | Type-safe fetch wrapper with ApiError extracting status & server message |
| DIP Container | Services receive repository Protocol interfaces via FastAPI Depends() |
| CI on Day One | GitHub Actions pipeline runs lint + format + test + build on every push |
| Automated QA | QA checklist items written as automated tests, enforced by CI |
| Connection Split (Supabase) | Port 6543 (transaction pooler) + NullPool for runtime; port 5432 (session pooler) for Alembic migrations |
| Prepared Statement Disabling | `connect_args={"prepare_threshold": None}` prevents named prepared statement errors with Supavisor pooler |
| Schema v1 Completeness | Core tables (UOM conversions, batch tracking, supplier FSSAI, retailer credit) created upfront |
| Append-only Stock Ledger | `stock_movements` is single source of truth for inventory balances |
| Frozen Invoicing Snapshot | `invoice_items` freezes prices, taxes, and names at issuance time to ensure immutable accounting records |
| Single-Path Sales Orders | `buyer_type` discriminator allows single order fulfillment engine to serve both B2B retailers and customers |
| Supplier Magic Links | `supplier_access_tokens` provides no-login dispatch confirmations for suppliers |
| Distributor Identity Model | `business_settings` provides single source of truth for distributor's legal/FSSAI profile |
| Natural-Key Upsert Seed | `scripts/seed.py` matches on unique natural keys to guarantee complete idempotency across repeated runs |
| Deliberate Low-Stock Seed Data | Seed includes 4 products below reorder point to prove alert and notification engines |
| Server-Side Session Cookies | Next.js route handler sets `httpOnly` cookie on auth to allow Next.js middleware protection without waterfalls |
| First-User Owner Assignment | Bootstrap assigns `Owner` role to 1st signed-in user; subsequent uninvited registrations receive 403 Forbidden |
| Data-Driven Permission Guards | `require_permission(code)` enforces DB permission codes from `role_permissions` rather than hardcoded roles |
| Dual-Inbound Auth Support | `get_current_user` extracts and verifies either Bearer tokens or `httpOnly` session cookies transparently |
| Dynamic RBAC Navigation | Navigation menus filter items strictly against user's active permissions without hardcoded role branches |
| Server-Side User Provisioning | Firebase Admin SDK creates users server-side only; service keys are never exposed to client bundles |
| Zero-Duplicated Portal Orders | `PortalAuthService.place_retailer_order` reuses `SalesOrderService` domain logic verbatim (OCP/DIP proof for external portal) |
| Read-Only Portal Accounting | Invoices and ledger views in self-service portal are strictly read-only; payment recording remains staff-only |
| Delivery Status Order Sync | `DeliveryService` auto-advances parent sales order to `DELIVERED` when delivery is marked `delivered`; keeps order at `SHIPPED` if `failed` |
| Delivery Assignment Guard | `DeliveryService.assign_delivery` requires sales order status `PACKED` (or `SHIPPED`), advancing it to `SHIPPED` upon driver assignment |
| Mandatory Delivery Failure Notes | Failing a delivery requires explanatory failure notes for warehouse operations and triggers an operational alert |
| Staff Pick List Document Standard | `ExportService.generate_pick_list` renders large-print checkbox list grouped by warehouse location with SKU, name, qty, UoM, and bin location, strictly omitting all pricing info |
| Notification Channel Strategy (OCP) | `NotificationService` coordinates pluggable `BaseNotificationChannel` implementations (`InAppChannel`, `EmailChannel`, `WhatsAppChannel`, `SmsChannel`), allowing new delivery channels with zero modifications to calling code |
| WhatsApp Cloud API Channel (Meta) | Meta Cloud API provides outbound B2B messaging with pre-approved message templates (`wareflow_stock_available`, `wareflow_goods_ready`); free tier capped at 1,000 service conversations/month with always-free email fallback |
| SMS Channel Fallback & Opt-In Policy | Outbound SMS via `SmsChannel` is strictly opt-in per contact and disciplined to 160-character single-segment messages, reserved for the most critical operational alerts (critical stock depletion, order confirmation) to eliminate carrier spam and overhead |
| Narrow-Scope Firestore Realtime Mirror | Firestore is used narrowly for realtime notification delivery only (`notifications/{uid}/items/{id}`) with `onSnapshot` in Topbar bell, while Postgres stays the system of record for everything, including history & pagination |
| Smart Alert Rule Engine (OCP) | `BaseAlertRule` strategy implementations (`LowStockRule`, `CriticalStockRule`, `ExpiringBatchRule`, `OverdueInvoiceRule`, `RestockAlertRule`) can be added independently without modifying `AlertEngineService` |
| 24-Hour Alert Deduplication Guard | `AlertLog` table and `AlertLogRepository.has_recent_alert` suppress repeated notifications for identical rule/entity combinations within a 24-hour window |
| Hybrid Periodic & Inline Alert Triggers | APScheduler executes background rule sweeps on a 30-minute timer, while inline hooks on `confirm_order`, `receive_stock`, and `adjust_stock` trigger immediate evaluations within seconds |
| Restock Availability Subscriptions (Auto-Unsubscribe) | `RestockAlertRule` delivers back-in-stock alerts via subscriber's preferred channel (WhatsApp/Email) when stock arrives, automatically setting `is_active=False` upon fulfillment to eliminate repeat spam |
| Pluggable Forecast Strategy Engine (OCP) | `ForecastStrategy` interface abstracts statistical demand forecasting algorithms (`MovingAverageForecast`, `ExponentialSmoothingForecast`), allowing new mathematical models without altering service orchestration or API routers |
| 24-Hour Forecast Database Caching | Forecast calculations cache historical outbound demand predictions per product in `forecasts` table with `expires_at` (24h TTL), guaranteeing sub-millisecond response latency with instant `force_refresh` support |
| Honest Zero-History Diagnostic Guard | Products with zero historical outbound movements return explicit `insufficient_data` status with 0.0 confidence rather than fabricating synthetic demand projections |

## Security & Audit Log Coverage

- **Audited Operations**:
  - `sales_order_created`: Creation of draft sales order with line items (`POST /sales-orders`)
  - `sales_order_confirmed`: Confirmation of sales order with credit reservation & FIFO batch deduction (`POST /sales-orders/{id}/confirm`)
  - `sales_order_status_updated`: Fulfillment status changes (packed, shipped, delivered, cancelled) (`PATCH /sales-orders/{id}/status`)
  - `invoice_generated`: Generation of sequential GST tax invoice for confirmed sales order (`POST /sales-orders/{id}/invoice`)
  - `payment_recorded`: Collection of settlement against tax invoice reducing retailer credit balance (`POST /invoices/{id}/payments`)
  - `einvoice_irn_generated`: Generation of statutory 64-hex IRN and signed QR code (`POST /invoices/{id}/generate-irn`)
  - `eway_bill_generated`: Generation of statutory 12-digit E-Way Bill for transit (`POST /invoices/{id}/generate-eway-bill`)
  - `overdue_invoices_flagged`: Batch scan flagging unpaid past-due invoices as overdue (`POST /invoices/detect-overdue`)
  - `retailer_created`: Registration of a new wholesale retailer account (`POST /retailers`)
  - `retailer_updated`: Updates to retailer contact info, pricing tier, or active status (`PATCH /retailers/{id}`)
  - `retailer_credit_limit_updated`: Retailer authorized credit limit adjustments (`PATCH /retailers/{id}/credit-limit`)
  - `business_settings_updated`: Legal business entity details, GSTIN, or FSSAI license updates (`PUT /settings/business`)
  - `product_price_updated`: Product wholesale and cost price alterations (`PATCH /products/{id}/price`)
  - `role_permissions_updated`: Permission matrix role-to-permission mapping updates (`PATCH /roles/{id}/permissions`)
  - `staff_role_updated`: Staff member role reassignments (`PATCH /staff/{id}/role`)
  - `staff_status_updated`: Staff member activation / suspension toggles (`PATCH /staff/{id}/status`)
  - `product_deleted`: Product catalog item removals (`DELETE /products/{id}`)

- Firebase ID tokens and session cookies verified server-side by FastAPI via Firebase Admin SDK
- RFC 6238 TOTP two-factor authentication mandatory for financial and administrative roles (`Owner`, `Manager`, `Accountant`)
- TOTP secrets and backup codes encrypted at rest with Fernet symmetric cryptography
- Single-use recovery backup codes permanently deleted from database record on use
- Database permissions loaded live per request for `CurrentUser` from `role_permissions`
- `require_permission(code)` raises 403 naming the specific missing permission code
- `require_2fa_if_enrolled` enforces 2FA challenge completion before sensitive operations
- Tokens never trusted from client alone
- .env files git-ignored forever (Secrets Rule #1)
- .env.example updated with placeholders for every new var (Secrets Rule #2)
- CORS restricted to allowed origins loaded dynamically from `ALLOWED_ORIGINS` settings
- PostgreSQL connection passwords percent-encoded (`%40` for `@`) in connection strings
- Server-side `httpOnly` session cookies protect Next.js routes with `sameSite: lax`

## Known Issues

- **Forward-Built Pre-Phase 6 Purchasing Spend Charts**: Spend-over-time, supplier spend, and category spend charts are intentionally forward-built to complete the Stock Analytics UI, but stay at zero / display empty states until Phase 6 (Purchase Orders & Receiving) produces real purchase order receipt transactions. This is expected and documented.
- **Supabase Free Project Inactivity Pause**: Supabase free-tier projects automatically pause after ~1 week of inactivity. If API endpoints return connection errors after an idle period, unpause the project from the Supabase dashboard.
- **In-Process APScheduler Lifetime**: The background alert scheduler runs in-process inside the FastAPI application lifespan. While ideal for single-instance free-tier deployments, multi-worker deployments (e.g. Gunicorn with >1 worker) would execute duplicate timer ticks unless bounded by `AlertLog` deduplication or migrated to an external Redis-backed Celery worker.



