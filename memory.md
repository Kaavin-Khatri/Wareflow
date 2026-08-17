# WareFlow — Project Memory

> Auto-maintained by coding agents. Do not delete.
> This file is **append-only** — history is never rewritten.
> Current system state lives in `codebase_audit.md`.

## Project Overview

- **Name:** WareFlow
- **Purpose:** AI-assisted wholesale inventory management system
- **Stack:** Next.js (frontend) + FastAPI (backend) + Supabase Postgres (DB) + Firebase (Auth) + Groq (AI)
- **Entry Points:** `apps/web/` (Next.js on :3000), `apps/api/app/main.py` (FastAPI on :8000)

## Architecture

- **Monorepo** with pnpm workspaces
- **Frontend:** Next.js App Router, TypeScript, Tailwind CSS
- **Backend:** FastAPI with SOLID layering — routers → services → repositories(interfaces) → repositories(impl)
- **Auth:** Firebase (Google/Apple/Email) — tokens verified server-side by FastAPI via Firebase Admin SDK
- **Database:** Supabase Postgres (system of record for orders, invoices, stock ledger)
- **Email:** Resend (low-stock/reorder alerts)
- **AI:** Groq (demand forecasting, smart reorder, NL queries, anomaly detection)

## Key Decisions

- Supabase is DATABASE ONLY — its Auth product is deliberately skipped in favor of Firebase
- Firebase Auth trust model: ID tokens verified server-side, never trusted from client alone
- Apple Sign-In enabled alongside Google + Email/Password (user's choice for iOS family)
- SOLID layering enforced from day one: routers never import repositories directly
- Secrets Rule #1: .env files are git-ignored forever
- Secrets Rule #2: Every new env var gets a placeholder in .env.example in the same commit

## Dependencies

- See `apps/web/package.json` for frontend dependencies
- See `apps/api/requirements.txt` for backend dependencies

## Environment

- OS: Windows 11 (NT 10.0.26200.0)
- Shell: PowerShell 5.1
- Node: v24.16.0 / pnpm: 11.8.0
- Python: 3.14.6
- Git: 2.55.0.windows.4
- AI Agent: Antigravity IDE

---

## Change Log

### Step 0.1 — Local Toolchain Setup

**Timestamp:** 2026-08-17T16:34:00Z
**Status:** COMPLETE

### What was done

- Verified all local toolchain dependencies
- Confirmed Git identity is configured (Kaavin / noreply GitHub email)
- Recorded OS + shell environment

### Decisions

- Node v24 LTS (exceeds minimum v20) — no downgrade needed
- pnpm v11 (exceeds minimum v9) — latest stable
- Python 3.14 (exceeds minimum 3.11) — used for scripting/tooling only

### Key values for future steps

- All future commands use PowerShell syntax

---

### Step 0.2 — GitHub Repo + Supabase (Database) + Firebase (Auth) Projects

**Timestamp:** 2026-08-17T16:55:00Z
**Status:** COMPLETE

### What was done

- GitHub repo confirmed: Kaavin-Khatri/Wareflow (private, main branch)
- Supabase project provisioned (DATABASE ONLY — Auth deliberately skipped)
- Firebase project provisioned with Authentication enabled
- Firebase web app registered (wareflow-web)
- Firebase Admin SDK service account key generated and saved outside repo

### Decisions

- Supabase = Postgres system of record (orders, invoices, stock ledger)
- Firebase = Auth + future realtime notifications
- Apple Sign-In enabled (user's choice for iOS family members)
- Google Analytics skipped on Firebase (not needed for MVP)

### Key values for future steps

- Supabase project ref: yappumzftkltlybmztgg
- Supabase region: Northeast Asia (Seoul) / ap-northeast-2
- Firebase project ID: wareflow-d17a4
- Firebase Auth providers: Email/Password, Google, Apple

---

### Step 0.3 — Email Alerts, Deploy Accounts & Env Convention

**Timestamp:** 2026-08-17T17:02:00Z
**Status:** COMPLETE

### What was done

- Resend account created — API key generated and saved
- Vercel account created — no project imported yet
- Render account created — no service created yet
- Groq account created — API key generated and saved
- Two project-wide secrets rules established

### Decisions

- Resend free tier (3,000 emails/month, 100/day) sufficient for alerts
- Vercel = Next.js hosting (deploy deferred to Phase 3)
- Render = FastAPI hosting (deploy deferred to Phase 3)
- Groq = LLM API for AI features

### Key values for future steps

- Resend tier: free (3k/mo, 100/day)
- Vercel + Render: accounts ready, deployment deferred

---

### Step 1.1 — Scaffold apps/web + apps/api + Protocol Files

**Timestamp:** 2026-08-17T17:04:00Z
**Status:** COMPLETE

### What was done

- Root monorepo with pnpm workspaces created
- apps/web scaffolded via create-next-app (App Router, TypeScript, Tailwind, ESLint)
- apps/api scaffolded with SOLID-first folder layout
- FastAPI /health endpoint created
- memory.md and codebase_audit.md bootstrapped with Phase 0 backfill
- .gitignore and .env.example files created per app
- Phase 0 outcomes backfilled and _phase0_outcomes.md consumed

### Decisions

- SOLID layering locked: routers → services → repositories(interfaces) → repositories(impl)
- Application factory pattern for FastAPI (testable, config-flexible)
- pydantic-settings for centralized config from env vars

### Key values for future steps

- Web: http://localhost:3000 (Next.js dev server)
- API: http://localhost:8000 (uvicorn dev server)
- SOLID rule: routers never import repositories directly, only services

### SOLID Principles Applied

- SRP: Each layer has one responsibility (HTTP, logic, data-access, validation)
- OCP: New domains added by creating new modules, not editing existing ones
- DIP: Services depend on repository interfaces, not implementations
- ISP: Separate interface per domain repository

### Files Created

- package.json, pnpm-workspace.yaml (root)
- apps/api/requirements.txt, apps/api/app/main.py
- apps/api/app/api/routers/health.py
- apps/api/app/core/config.py, apps/api/app/core/di.py
- All **init**.py files for SOLID layer packages
- .gitignore, apps/web/.env.example, apps/api/.env.example
- memory.md, codebase_audit.md

---

## Step 1.2 — Lint, Format & Local Dev Ergonomics

**Timestamp:** 2026-08-17T17:15:00Z
**Status:** COMPLETE

### What was done

- ESLint + Prettier + eslint-config-prettier integrated for apps/web
- Ruff configured (line-length 100, target py311) for apps/api
- Prettier config at root (.prettierrc) with 100 char line width
- README.md written with full quick-start guide for strangers
- docker-compose.yml with optional local Postgres fallback (port 5433)
- Format scripts added to root package.json

### Decisions

- Prettier line-length 100 matches ruff line-length 100 for monorepo consistency
- Ruff lint rules: E, W, F, I, B, UP, SIM, N — comprehensive without being noisy
- Local Postgres on port 5433 to avoid conflicts; Supabase stays primary
- requirements-dev.txt separates dev tools (ruff, pytest) from production deps

### Key values for future steps

- Format: `pnpm format` (web), `ruff format app/` (api)
- Lint: `pnpm lint:web` (web), `ruff check app/` (api)
- Local PG: `postgresql://wareflow:wareflow_dev@localhost:5433/wareflow`

### Files Created

- .prettierrc, .prettierignore
- apps/api/pyproject.toml, apps/api/requirements-dev.txt
- docker-compose.yml, README.md

### Files Modified

- package.json (format scripts)
- apps/web/eslint.config.mjs (prettier integration)

---

## Step 1.3 — Typed API Client, DI Container & CORS Handshake

**Timestamp:** 2026-08-17T17:25:00Z
**Status:** COMPLETE

### What was done

- Implemented dependency injection container (`app/core/di.py`) wiring FastAPI `Depends()` factories
- Created `ProductRepositoryInterface` protocol and decoupled `ProductService` for concrete DIP demonstration
- Automated tests verifying DIP swappability (swapping repo implementation requires zero service code changes)
- Configured dynamic `CORSMiddleware` reading `ALLOWED_ORIGINS` from `pydantic-settings`
- Created typed API client in `apps/web/lib/api-client.ts` with custom `ApiError` class
- Created temporary probe page `apps/web/app/debug/page.tsx` testing live `/health` status and `ApiError` contract
- Successfully verified web-to-api handshake with live 200 responses

### Decisions

- DI pattern locked: services depend on Protocol interfaces, never on SQLAlchemy classes directly
- Swapping a repository implementation in `di.py` requires touching zero service code (DIP proof verified in tests)
- `ALLOWED_ORIGINS` supports comma-separated strings or JSON arrays in env vars
- `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000` for local dev ergonomics

### Key values for future steps

- DI factory convention: `def get_<domain>_service(repo: <Domain>RepositoryInterface = Depends(get_<domain>_repository)) -> <Domain>Service`
- Frontend API helper: `apiClient.get<T>()`, `apiClient.post<T>()`, throwing typed `ApiError`

### Files Created

- `apps/api/app/repositories/interfaces/product_repository.py`
- `apps/api/app/repositories/impl/product_repository.py`
- `apps/api/app/services/product_service.py`
- `apps/api/tests/test_di_and_health.py`
- `apps/web/lib/api-client.ts`
- `apps/web/app/debug/page.tsx`

### Files Modified

- `apps/api/app/core/config.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/pyproject.toml`
- `apps/api/.env.example`

---

## Step 1.4 — CI Pipeline (GitHub Actions)

**Timestamp:** 2026-08-17T17:30:00Z
**Status:** COMPLETE

### What was done

- Scaffolded Vitest test runner in `apps/web` with unit tests for `ApiError` and `apiClient`
- Added `pytest-cov` to `apps/api` requirements and verified code coverage reporting
- Built GitHub Actions CI pipeline in `.github/workflows/ci.yml` covering lint, formatting checks, unit tests, and production build checks for both apps on every push/PR
- Documented branch protection setup guidelines in `README.md`
- Verified local test execution, linting, formatting, and Next.js production build pass clean

### Decisions

- CI pipeline scope: lint (ESLint/Ruff) + format check (Prettier/Ruff) + test (Vitest/Pytest) + build (Next.js) for both apps on every push and PR
- Automated QA rule: all future phase QA checklist items that are automatable must be written as pytest/vitest tests, not manual verification
- Main branch protection recommended: requiring CI check to pass before merge

### Key values for future steps

- CI workflow file: `.github/workflows/ci.yml`
- Local web test command: `pnpm test:web` (or `pnpm --filter web test`)
- Local API test command: `pytest --cov=app` (inside `apps/api/.venv`)
- Production build validation: `pnpm --filter web build`

### Files Created

- `.github/workflows/ci.yml`
- `apps/web/vitest.config.mts`
- `apps/web/lib/__tests__/api-client.test.ts`

### Files Modified

- `apps/api/requirements-dev.txt`
- `apps/web/package.json`
- `package.json`
- `README.md`

---

## Step 2.1 — SQLAlchemy + Alembic Wired to Supabase

**Timestamp:** 2026-08-17T17:45:00Z
**Status:** COMPLETE

### What was done

- Configured SQLAlchemy 2.0 engine in `app/db/session.py` with `NullPool` and `pool_pre_ping=True`
- Initialized Alembic migrations in `apps/api/alembic` reading `DIRECT_DATABASE_URL` for migration execution
- Created initial probe migration `0001_initial_schema_probe.py` and executed `alembic upgrade head` cleanly against live Supabase Postgres
- Added `GET /health/db` endpoint executing `SELECT 1` through `get_db_session` dependency, returning `{"status": "ok", "database": "connected"}`
- Verified zero credentials in git tracking

### Decisions

- Connection split in force: port 6543 pooler + NullPool at runtime (Supavisor transaction mode), port 5432 session pooler for migrations (supports DDL & advisory locks over IPv4)
- Percent-encoding (`%40`) required for special characters in PostgreSQL URL passwords
- NullPool prevents double-pooling overhead and connection leaks with Supabase's server-side pooler

### Key values for future steps

- Runtime session dependency: `get_db_session()` from `app.db.session`
- Migration execution: `alembic upgrade head`
- Database health check: `GET /health/db`

### Files Created

- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/script.py.mako`
- `apps/api/alembic/versions/0001_initial_schema_probe.py`
- `apps/api/app/db/__init__.py`
- `apps/api/app/db/session.py`
- `apps/api/app/db/base.py`

### Files Modified

- `apps/api/app/api/routers/health.py`
- `apps/api/app/core/config.py`
- `apps/api/tests/test_di_and_health.py`

---

## Step 2.2 — Core Wholesale Schema (products, stock, orders)

**Timestamp:** 2026-08-17T18:10:00Z
**Status:** COMPLETE

### What was done

- Designed and implemented full SQLAlchemy 2.0 ORM models in modular domain packages under `app/models/`:
  - `uom.py`: `units_of_measure` (id, name, abbreviation) and `product_uom_conversions` (product_id, from_uom_id, to_uom_id, factor)
  - `catalog.py`: `categories` (id, name, parent_id) and `products` (id, sku, name, description, content_details, image_url, hsn_code, category_id, base_uom_id, unit, cost_price, wholesale_price, reorder_point, reorder_qty, barcode, is_active)
  - `warehouse.py`: `warehouses` (id, name, location, is_active) and `stock_batches` (id, product_id, warehouse_id, batch_no, quantity, expiry_date, received_at)
  - `supplier.py`: `suppliers` (id, name, contact_person, phone, email, address, gstin, fssai_license_no, fssai_expiry_date), `purchase_orders` (id, po_number, supplier_id, status, order_date, expected_date, total_amount), and `purchase_order_items` (id, po_id, product_id, qty_ordered, qty_received, unit_cost, uom_id)
  - `retailer.py`: `retailers` (id, name, contact_person, phone, email, address, gstin, pricing_tier, credit_limit, credit_balance), `sales_orders` (id, so_number, retailer_id, status, order_date, total_amount), and `sales_order_items` (id, so_id, product_id, qty, unit_price, uom_id)
  - `inventory.py`: `stock_movements` (id, product_id, warehouse_id, batch_id, type [in/out/adjustment/transfer/return_in/return_out], quantity, reference_type, reference_id, created_by, created_at)
  - `notification.py`: `notifications` (id, user_id, type, title, body, is_read, created_at)
- Created Alembic migration `0002_core_wholesale_schema.py` creating all 14 tables, enums, FK constraints, and indexes.
- Executed migration and verified `downgrade base` and `upgrade head` round-trips cleanly against live Supabase PostgreSQL.
- Added comprehensive model test suite in `tests/test_models.py` reaching 96% test coverage.

### Decisions

- **Schema v1 Full Domain Foundation**: All core tables (including UOM conversion, batch tracking, supplier FSSAI, retailer credit, and notifications) created now so later phases only add application behavior and APIs, not breaking DDL changes.
- **Stock Movements Ledger**: `stock_movements` is the single source of truth for on-hand quantity across warehouses and batches — never trust a cached counter alone.
- **Retailer Credit Tracking**: `credit_limit` and `credit_balance` live directly on `retailers` now so Phase 9 (Billing & Invoicing) adds logic without schema alterations.
- **PO Dispatch Status**: `ready_for_dispatch` status added to `po_status_enum` so a supplier/manufacturer can signal 'goods packed, ready to collect' before receiving, triggering notifications in Phase 11.
- **Rich Catalog Fields**: `description`, `content_details`, and `image_url` included on `products` at schema-v1 time for retailer catalog and portal needs.
- **GST Compliance**: `hsn_code` added to `products` at schema-v1 time for GST-compliant invoice generation.
- **Food Safety Compliance**: `fssai_license_no` and `fssai_expiry_date` added to `suppliers` for Indian regulatory food safety requirements.

### Key values for future steps

- 14 core tables live on Supabase: `units_of_measure`, `product_uom_conversions`, `categories`, `products`, `warehouses`, `stock_batches`, `suppliers`, `purchase_orders`, `purchase_order_items`, `retailers`, `sales_orders`, `sales_order_items`, `stock_movements`, `notifications`
- PO status enum values: `draft`, `ordered`, `ready_for_dispatch`, `partially_received`, `received`, `cancelled`
- SO status enum values: `draft`, `confirmed`, `packed`, `shipped`, `delivered`, `cancelled`
- Stock movement types: `in`, `out`, `adjustment`, `transfer`, `return_in`, `return_out`

### Files Created

- `apps/api/app/models/__init__.py`
- `apps/api/app/models/uom.py`
- `apps/api/app/models/catalog.py`
- `apps/api/app/models/warehouse.py`
- `apps/api/app/models/supplier.py`
- `apps/api/app/models/retailer.py`
- `apps/api/app/models/inventory.py`
- `apps/api/app/models/notification.py`
- `apps/api/alembic/versions/0002_core_wholesale_schema.py`
- `apps/api/tests/test_models.py`

### Files Modified

- `apps/api/alembic/env.py`

---

## Step 2.3 — Extended Schema: Invoicing, Returns & Deliveries

**Timestamp:** 2026-08-17T18:25:00Z
**Status:** COMPLETE

### What was done

- Designed and implemented the complete extended wholesale domain model suite in `app/models/`:
  - `billing.py`: `invoices` (id, sales_order_id, invoice_no, invoice_date, gst_rate, subtotal, tax_amount, total_amount, status [unpaid/partially_paid/paid/overdue], e_invoice_irn, e_invoice_ack_no, e_invoice_qr_code, e_way_bill_no), `invoice_items` (frozen accounting snapshot: id, invoice_id, product_id, product_name, hsn_code, qty, unit_price, tax_rate, tax_amount, total, uom_id), and `payments` (id, invoice_id, retailer_id, customer_id, amount, method [cash/bank_transfer/cheque/upi], paid_at, note)
  - `returns.py`: `sales_returns` (id, sales_order_id, retailer_id, status [requested/approved/rejected/completed], reason, requested_at), `sales_return_items` (id, return_id, product_id, qty, batch_id, condition [resellable/damaged]), `purchase_returns` (id, purchase_order_id, supplier_id, status [requested/shipped/credited], reason, requested_at), and `purchase_return_items` (id, return_id, product_id, qty, batch_id, reason)
  - `delivery.py`: `deliveries` (id, sales_order_id, driver_name, vehicle_no, status [assigned/out_for_delivery/delivered/failed], dispatched_at, delivered_at, notes)
  - `auth_rbac.py`: `roles` (id, name, description), `permissions` (id, code, description), and `role_permissions` (role_id, permission_id)
  - `portal.py`: `customers` (id, name, phone, email, address, notes), `stock_subscriptions` (id, retailer_id, product_id, channel_preference [whatsapp/email/both], is_active, notified_at), `supplier_access_tokens` (magic links: id, supplier_id, purchase_order_id, token, expires_at), and `product_inquiries` (id, product_id, retailer_id, customer_id, message, status [open/responded/closed], response, responded_at)
  - `recalls.py`: `batch_recalls` (id, batch_id, product_id, reason, severity [low/medium/critical], status [initiated/notifying/resolved], initiated_at, resolved_at) and `recall_affected_orders` (id, recall_id, sales_order_id, retailer_id, customer_id, notified_at)
  - `audit_and_settings.py`: `admin_audit_log` (id, actor_id, action, entity_type, entity_id, before_value, after_value, created_at) and `business_settings` (id, business_name, gstin, fssai_license_no, fssai_expiry_date, address, phone, email)
  - `retailer.py`: Updated `sales_orders` with `buyer_type` discriminator (`retailer` vs `customer`), `customer_id` FK, and nullable `retailer_id`
- Created and executed Alembic migration `0003_extended_wholesale_schema.py` creating all extended tables, foreign keys, and indexes.
- Verified bidirectional migration round-trips (`downgrade base` / `upgrade head`) across the complete combined database schema on Supabase.
- Added comprehensive unit tests in `tests/test_extended_models.py` verifying frozen invoice snapshots, payment netting against credit balance, RBAC mappings, and magic tokens (12 total tests, 98% coverage).

### Decisions

- **Frozen Invoice Snapshot**: `invoice_items` store snapshot product names, pricing, and HSN codes at invoice generation time — editing a sales order or catalog item never alters an issued tax invoice.
- **Single-Path Sales Order Architecture**: The `buyer_type` discriminator on `sales_orders` enables a single fulfillment and inventory deduction engine to serve wholesale B2B accounts and walk-in buyers alike without code or schema duplication.
- **Supplier Magic Links**: `supplier_access_tokens` provide temporary, tokenized URLs allowing suppliers to update dispatch status directly without requiring login accounts.
- **GST & E-Invoicing Ready**: IRN, Ack No, QR code, and e-way bill fields are built into `invoices` at schema time.
- **Generic Admin Audit Logging**: `admin_audit_log` captures before/after JSON payloads for any sensitive administrative operations.
- **Distributor Compliance Identity**: `business_settings` provides a single source of truth for the distributor's own business legal data and FSSAI tracking.

### Key values for future steps

- 27 total domain tables live on Supabase covering all distribution, accounting, and compliance operations
- Payment methods: `cash`, `bank_transfer`, `cheque`, `upi`
- Delivery statuses: `assigned`, `out_for_delivery`, `delivered`, `failed`
- Return item conditions: `resellable`, `damaged`
- Stock subscription channels: `whatsapp`, `email`, `both`

### Files Created

- `apps/api/app/models/billing.py`
- `apps/api/app/models/returns.py`
- `apps/api/app/models/delivery.py`
- `apps/api/app/models/auth_rbac.py`
- `apps/api/app/models/portal.py`
- `apps/api/app/models/recalls.py`
- `apps/api/app/models/audit_and_settings.py`
- `apps/api/alembic/versions/0003_extended_wholesale_schema.py`
- `apps/api/tests/test_extended_models.py`

### Files Modified

- `apps/api/app/models/__init__.py`
- `apps/api/app/models/retailer.py`

---

## Step 2.4 — Seed Data (products, suppliers, retailers, warehouses)

**Timestamp:** 2026-08-17T18:31:00Z
**Status:** COMPLETE

### What was done

- Created idempotent wholesale distribution seed script in `scripts/seed.py`:
  - **2 Base UOMs + Pack UOMs**: Piece (`pcs`), Case (`case`, 24 pcs conversion factor), Kilogram (`kg`), Box (`box`, 10 pcs)
  - **2 Warehouses**: Bhiwandi Central Hub (Logistics Park, Bhiwandi) and Navi Mumbai APMC Terminal (Sector 19, Vashi)
  - **5 Major FMCG/Food Suppliers**: HUL, ITC Limited, Tata Consumer Products, Nestle India, Britannia Industries (all with valid GSTIN, FSSAI license numbers & expiry dates)
  - **8 B2B Wholesale Retailers**: Mixed pricing tiers (`standard`, `wholesale_silver`, `wholesale_gold`, `vip`) with credit limits ranging from ₹0 to ₹500,000 and starting credit balances
  - **5 Product Categories**: Staples & Grains, Beverages & Tea, Snacks & Biscuits, Personal Care & Hygiene, Packaged Foods & Sauces
  - **40 Wholesale Products**: Populated with realistic Indian wholesale pricing, cost prices, GST HSN codes, GS1 barcodes, reorder points, and reorder quantities
  - **5 Default RBAC Roles & Permissions Matrix**: Owner (Root/All), Manager (Operations), Sales Staff, Warehouse Staff, and Accountant, mapped to granular system permissions
  - **Stock Batches**: Distributed across warehouses, with healthy inventory plus 4 products deliberately seeded below `reorder_point` (Nescafe 200g, Taj Mahal Tea 500g, Kissan Mixed Fruit Jam 1kg, Del Monte Penne Pasta) to prove low-stock alert triggers in Phase 8
  - **Business Profile Settings**: Initial distributor legal entity profile with GSTIN and FSSAI license
- Solved psycopg 3 + Supavisor pooler prepared statement conflict by setting `connect_args={"prepare_threshold": None}` in `app/db/session.py`.
- Added unit test suite in `apps/api/tests/test_seed.py` verifying full seed idempotency across multiple runs, low-stock threshold queries, and RBAC matrix integrity.

### Decisions

- **Natural-Key Idempotency**: All seed operations perform upserts matching on unique natural business keys (`sku` for products, `abbreviation` for UOMs, `code` for permissions, and `name` for categories/roles/warehouses/suppliers/retailers). Re-running `seed.py` never duplicates records or raises unique constraint violations.
- **Transaction Pooler Prepared Statements**: Disabled named prepared statement caching in psycopg (`prepare_threshold=None`) to ensure compatibility with multiplexed Supabase transaction poolers on port 6543.
- **Intentional Low Stock**: 4 products are seeded with batch inventory strictly below their configured `reorder_point` to validate notification triggers, reorder suggestions, and visual alert badges.

### Key values for future steps

- 40 active SKUs across 5 core categories available for UI display, order creation, and search
- 8 seeded retailers with credit limit profiles ready for order checkout validation
- Default roles for RBAC verification: `Owner`, `Manager`, `Sales Staff`, `Warehouse Staff`, `Accountant`
- Low-stock testing SKUs: `SKU-COF-NESC-200G`, `SKU-TEA-TAJ-500G`, `SKU-JAM-KISS-MIX-1KG`, `SKU-PAS-DELM-PEN-500G`

### Files Created

- `scripts/seed.py`
- `apps/api/tests/test_seed.py`

### Files Modified

- `apps/api/app/db/session.py`

---

## Step 3.1 — Firebase Auth: Google Sign-In + Email/Password UI + Session Cookie

**Timestamp:** 2026-08-17T18:40:00Z
**Status:** COMPLETE

### What was done

- Integrated Firebase Web SDK in `apps/web` with safe initialization in `apps/web/lib/firebase-client.ts` supporting SSR and Next.js static prerendering.
- Designed and built responsive, modern authentication interface in `apps/web/app/(auth)/login/page.tsx`:
  - Prominent "Continue with Google" popup button with Google logo SVG.
  - Email/Password form with sign-in and sign-up toggle modes, show/hide password visibility, and helpful error alerts.
  - Built-in `<Suspense>` boundary wrapping search params for safe SSR.
- Created server-side session cookie management in `apps/web/app/api/auth/session/route.ts` and `apps/web/app/(auth)/logout/route.ts` setting and clearing `httpOnly`, `sameSite: lax` cookies.
- Implemented Next.js auth middleware in `apps/web/middleware.ts` protecting `/dashboard`, `/inventory`, `/orders`, `/invoices` and redirecting authenticated users away from `/login`.
- Created landing workspace in `apps/web/app/dashboard/page.tsx` confirming verified auth session and sign-out controls.
- Designed and migrated backend `profiles` table linked to Firebase UIDs via Alembic migration `0004_user_profiles.py`.
- Created SOLID profile layer in `apps/api`:
  - `ProfileRepository` interface protocol and `SqlAlchemyProfileRepository` implementation.
  - `ProfileService` with `bootstrap_user` method assigning the root `Owner` role to the first authenticated user in the system (`ALLOW_FIRST_SIGNUP`).
  - `POST /profiles/bootstrap` and `GET /profiles/me` endpoints in `apps/api/app/api/routers/profiles.py`.
  - Token verification and dependency injection in `apps/api/app/core/security.py` and `apps/api/app/core/di.py`.
- Added unit tests in `apps/web/lib/__tests__/firebase-client.test.ts` and `apps/api/tests/test_profiles.py` reaching 95% total API coverage across 19 tests.

### Decisions

- **Client Auth + Server-Side Session Cookie**: Next.js middleware and SSR components inspect an `httpOnly` session cookie (`session`) minted immediately upon Firebase client authentication, eliminating client-side auth waterfalls on protected pages.
- **First-User Bootstrap Pattern**: The very first user to sign in automatically receives the `Owner` role in Postgres with full root administrative permissions, while subsequent uninvited signups are rejected with 403 Forbidden.
- **Safe SSR Fallbacks**: `firebase-client.ts` uses fallback dummy configuration during `next build` static export to ensure build pipelines compile without hard runtime exceptions.

### Key values for future steps

- Login page: `/login`
- Logout route: `/logout` or `DELETE /api/auth/session`
- Authenticated landing page: `/dashboard`
- Profile bootstrap API: `POST /profiles/bootstrap`
- User profile & permissions API: `GET /profiles/me`

### Files Created

- `apps/api/app/models/profile.py`
- `apps/api/alembic/versions/0004_user_profiles.py`
- `apps/api/app/repositories/interfaces/profile_repository.py`
- `apps/api/app/repositories/impl/profile_repository.py`
- `apps/api/app/services/profile_service.py`
- `apps/api/app/schemas/profile.py`
- `apps/api/app/api/routers/profiles.py`
- `apps/api/app/core/security.py`
- `apps/api/tests/test_profiles.py`
- `apps/web/lib/firebase-client.ts`
- `apps/web/lib/__tests__/firebase-client.test.ts`
- `apps/web/app/(auth)/login/page.tsx`
- `apps/web/app/(auth)/logout/route.ts`
- `apps/web/app/api/auth/session/route.ts`
- `apps/web/app/dashboard/page.tsx`
- `apps/web/middleware.ts`

### Files Modified

- `apps/api/app/models/__init__.py`
- `apps/api/app/core/config.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/package.json`

---

## Step 3.2 — FastAPI Firebase ID-Token Verification + Permission Guards

**Timestamp:** 2026-08-17T18:50:00Z
**Status:** COMPLETE

### What was done

- Initialized Firebase Admin SDK with service-account JSON path loaded via `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` / `FIREBASE_SERVICE_ACCOUNT_PATH`.
- Implemented dual-mode inbound authentication in `apps/api/app/core/security.py` supporting both `Authorization: Bearer <id_token>` (for mobile/API clients) and `Cookie: session=<cookie>` / `__session` (for Next.js SSR and client calls).
- Constructed typed `CurrentUser` context dataclass (`id`, `email`, `role`, `permissions: set[str]`, `display_name`, `avatar_url`, `phone`, `is_active`).
- Built `get_current_user` FastAPI dependency resolving caller identity and looking up live permission codes directly from Postgres (`role_permissions` join `permissions`).
- Built data-driven permission and role guard factories in `apps/api/app/core/security.py`:
  - `require_permission(permission_code)`: returns 403 Forbidden naming the specific missing permission code when unauthorized.
  - `require_role(role_name)`: convenience wrapper enforcing role membership.
- Added `GET /me` route in `apps/api/app/api/routers/me.py` and connected it to FastAPI app factory in `apps/api/app/main.py`.
- Integrated Apple Sign-In on the web frontend:
  - Added `OAuthProvider("apple.com")` in `apps/web/lib/firebase-client.ts`.
  - Added "Continue with Apple" button with Apple SVG, loading states, and error handling in `apps/web/app/(auth)/login/page.tsx`.
  - Updated frontend unit tests in `apps/web/lib/__tests__/firebase-client.test.ts`.
- Created comprehensive test suite in `apps/api/tests/test_auth_and_guards.py` verifying `GET /me`, permission enforcement (Warehouse Staff getting 403 on invoicing routes), 401 for tampered tokens, session cookie equivalence, and inactive user blocks (25 total backend tests passing with 95% coverage).

### Decisions

- **Identity Bridge Pattern**: Firebase UID (`uid`) is the stable primary key join between Firebase Auth and the Postgres `profiles` table.
- **Data-Driven RBAC Contract**: `CurrentUser(id, role, permissions, email)` is the single auth contract for all future routes — authorization checks query the database permission set, never hardcoded role string lists.
- **Dual Inbound Auth**: FastAPI accepts either Bearer tokens or `httpOnly` session cookies transparently, facilitating both SSR server component calls and external API client integrations.
- **Explicit 403 Detail**: Missing permission failures explicitly state `Missing required permission: <code_name>` for clear frontend debugging and permission handling.

### Key values for future steps

- Current user dependency: `get_current_user` from `app.core.security`
- Permission guard: `require_permission("<permission_code>")` from `app.core.security`
- Role guard: `require_role("<role_name>")` from `app.core.security`
- Current user model: `CurrentUser` dataclass with `permissions: set[str]`
- User info endpoint: `GET /me` (alias `GET /profiles/me`)

### Files Created

- `apps/api/app/api/routers/me.py`
- `apps/api/tests/test_auth_and_guards.py`

### Files Modified

- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/tests/test_seed.py`
- `apps/web/lib/firebase-client.ts`
- `apps/web/lib/__tests__/firebase-client.test.ts`
- `apps/web/app/(auth)/login/page.tsx`

---

## Step 3.3 — Staff Management, Role Assignment & Route Protection

**Timestamp:** 2026-08-17T19:00:00Z
**Status:** COMPLETE

### What was done

- Designed and implemented Staff and Role-Permission APIs in FastAPI:
  - `POST /staff/invite`: Creates Firebase Auth user via Admin SDK with temporary password reset / sign-in link, creates `profiles` record with assigned role.
  - `GET /staff`: Lists staff user profiles with role names, active statuses, and joined dates.
  - `PATCH /staff/{id}/role`: Updates a staff member's assigned role in the database.
  - `PATCH /staff/{id}/status`: Toggles active/inactive account status for staff profiles.
  - `GET /roles`: Retrieves all defined roles along with their granted permission codes.
  - `GET /permissions`: Retrieves all granular system permission definitions.
  - `PATCH /roles/{id}/permissions`: Updates role-to-permission mappings in `role_permissions` in real-time.
- Built dynamic navigation and permission filtering architecture in `apps/web`:
  - `apps/web/lib/nav.ts`: Navigation configuration where items carry `requiredPermission` / `requiredRole` declarations, filtered dynamically via `filterNavSections`.
  - `apps/web/components/Sidebar.tsx`: Dynamic RBAC-driven sidebar loading user permissions from `/me` and rendering only permitted sections and actions.
  - `apps/web/components/AppLayout.tsx`: Reusable app shell layout.
  - `apps/web/middleware.ts`: Enhanced route protection checking session cookies across all `/admin/*`, `/inventory/*`, `/orders/*`, `/invoices/*`, `/returns/*`, `/deliveries/*`, `/reports/*` routes with `?next=<path>` redirect parameters.
- Built rich frontend administration pages:
  - `apps/web/app/admin/settings/staff/page.tsx`: Staff invitation card + active team table with inline role changer dropdown and activation toggles.
  - `apps/web/app/admin/settings/permissions/page.tsx`: Interactive Permission Matrix Editor with live domain groupings and real-time checkbox toggles with immediate database synchronization.
- Created automated test suites in `apps/web/lib/__tests__/nav.test.ts` and `apps/api/tests/test_staff_and_roles.py` validating staff onboarding, unauthorized invite rejection (403), permission matrix live editing, and nav filtering (all 38 monorepo tests passing with 95% API coverage).

### Decisions

- **Permission-Matrix-Driven Navigation**: Nav items are filtered strictly by the user's actual permission codes rather than hardcoded role string lists. Adding a new role in the future requires zero frontend code changes.
- **Server-Side Firebase Admin User Creation**: Firebase Admin SDK user creation is executed strictly server-side inside `StaffService`, never exposing service account keys to client applications.
- **Single Responsibility Separation**: Decoupled Firebase Admin app lifecycle into `app.core.firebase` to eliminate circular dependencies with dependency injection containers.

### Key values for future steps

- Staff invite API: `POST /staff/invite`
- Staff listing API: `GET /staff`
- Staff role patch API: `PATCH /staff/{id}/role`
- Roles list API: `GET /roles`
- Permission list API: `GET /permissions`
- Permission matrix patch API: `PATCH /roles/{id}/permissions`
- Web Staff management: `/admin/settings/staff`
- Web Permissions matrix editor: `/admin/settings/permissions`
- Nav filtering utility: `filterNavSections()` from `@/lib/nav`

### Files Created

- `apps/api/app/core/firebase.py`
- `apps/api/app/schemas/staff.py`
- `apps/api/app/services/staff_service.py`
- `apps/api/app/api/routers/staff.py`
- `apps/api/app/api/routers/roles.py`
- `apps/api/tests/test_staff_and_roles.py`
- `apps/web/lib/nav.ts`
- `apps/web/lib/__tests__/nav.test.ts`
- `apps/web/components/Sidebar.tsx`
- `apps/web/components/AppLayout.tsx`
- `apps/web/app/admin/settings/staff/page.tsx`
- `apps/web/app/admin/settings/permissions/page.tsx`

### Files Modified

- `apps/api/requirements.txt`
- `apps/api/app/repositories/interfaces/profile_repository.py`
- `apps/api/app/repositories/impl/profile_repository.py`
- `apps/api/app/core/di.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `scripts/seed.py`
- `apps/web/middleware.ts`
- `apps/web/app/dashboard/page.tsx`
