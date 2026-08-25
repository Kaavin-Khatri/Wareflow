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

---

## Step 3.4 — TOTP Two-Factor Authentication (Owner/Admin/Accountant)

**Timestamp:** 2026-08-17T19:35:00Z
**Status:** COMPLETE

### What was done

- Implemented RFC 6238 Time-based One-Time Password (TOTP) two-factor authentication in FastAPI using `pyotp`, `qrcode`, and `cryptography`:
  - `POST /auth/2fa/enroll`: Generates random base32 TOTP secret, provisioning URI, scannable PNG QR code (base64 Data URL), and 10 single-use recovery backup codes. Encrypts secret and codes at rest.
  - `POST /auth/2fa/verify-enrollment`: Confirms the first 6-digit TOTP code before activating 2FA on the user's profile (`totp_enabled = True`).
  - `POST /auth/2fa/verify`: Validates 6-digit TOTP codes or single-use recovery backup codes during login challenges. Reused backup codes are strictly rejected.
  - `POST /auth/2fa/disable`: Disables 2FA upon valid TOTP verification and clears stored secrets.
  - `GET /auth/2fa/status`: Returns current 2FA status, requirement policy, and remaining active backup code count.
  - `POST /auth/2fa/regenerate-backup-codes`: Generates 10 fresh recovery backup codes after verifying live TOTP.
- 2FA Policy & Route Guard Enforcement:
  - 2FA is mandatory for financial and administrative roles (`Owner`, `Manager`, `Accountant`) and routes touching sensitive permissions.
  - Warehouse Staff and Sales Staff are exempt by default for rapid shop-floor operations.
  - Enforced via `require_2fa_if_enrolled` and sensitive permission checks in `app.core.security`.
- Built frontend 2FA user flows and security dashboard in Next.js:
  - `apps/web/app/(auth)/login/2fa/page.tsx`: Glassmorphic 6-digit PIN input with automatic focus, numeric paste support, backup code recovery fallback, and countdown/resubmit.
  - `apps/web/app/(auth)/login/page.tsx`: Checks 2FA status after Firebase primary sign-in and routes 2FA-enabled accounts directly to `/login/2fa`.
  - `apps/web/app/admin/settings/security/page.tsx`: 2FA management console with status badge, QR code setup wizard, downloadable `.txt` backup codes, remaining codes counter, and regeneration/disable modals.
  - `apps/web/app/api/auth/session/route.ts`: Added `PATCH` handler establishing verified 2FA session cookies.
  - `apps/web/lib/nav.ts`: Added "Security & 2FA" navigation link under Organization & Admin.
- Created automated test suites in `apps/api/tests/test_2fa.py` validating enrollment, verification, single-use backup code consumption, sensitive route protection, and operational staff exemption (all 43 monorepo tests passing with 94% backend coverage).

### Decisions

- **In-House TOTP over Paid Firebase SMS MFA**: Free-tier RFC 6238 TOTP with Google Authenticator / Authy compatibility avoids paid Firebase Blaze plan SMS fees.
- **Symmetric Secret Encryption at Rest**: `totp_secret_encrypted` and `backup_codes_encrypted` are encrypted using Fernet (AES-128-CBC + HMAC-SHA256) with keys derived deterministically from application secrets.
- **Single-Use Atomic Backup Code Consumption**: Each backup code is removed from the encrypted array upon first successful verification, preventing replay attacks.
- **Operational Staff Exemption**: Floor staff are exempt by default from 2FA to prevent operational delays during high-speed barcode scanning and order packing.

### Key values for future steps

- 2FA Enroll API: `POST /auth/2fa/enroll`
- 2FA Verify Enrollment API: `POST /auth/2fa/verify-enrollment`
- 2FA Challenge Verify API: `POST /auth/2fa/verify`
- 2FA Status API: `GET /auth/2fa/status`
- 2FA Guard dependency: `require_2fa_if_enrolled` from `app.core.security`
- Web 2FA Login Challenge: `/login/2fa`
- Web Security Settings: `/admin/settings/security`

### Files Created

- `apps/api/alembic/versions/0005_two_factor_auth.py`
- `apps/api/app/core/crypto.py`
- `apps/api/app/schemas/two_factor.py`
- `apps/api/app/services/two_factor_service.py`
- `apps/api/app/api/routers/two_factor.py`
- `apps/api/tests/test_2fa.py`
- `apps/web/app/(auth)/login/2fa/page.tsx`
- `apps/web/app/admin/settings/security/page.tsx`

### Files Modified

- `apps/api/requirements.txt`
- `apps/api/.env.example`
- `apps/api/app/core/config.py`
- `apps/api/app/core/security.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/app/models/profile.py`
- `apps/api/app/repositories/interfaces/profile_repository.py`
- `apps/api/app/repositories/impl/profile_repository.py`
- `apps/web/app/(auth)/login/page.tsx`
- `apps/web/app/api/auth/session/route.ts`
- `apps/web/middleware.ts`
- `apps/web/lib/nav.ts`

---

## Step 3.5 — General Admin Action Audit Log

**Timestamp:** 2026-08-17T20:15:00Z
**Status:** COMPLETE

### What was done

- Implemented general administrator audit logging engine backed by `admin_audit_log` database table:
  - Created `AuditRepository` protocol and `SqlAlchemyAuditRepository` implementation for persisting and querying audit entries with pagination, date-range, and entity filters.
  - Implemented `AuditService` with `log()` and `list_logs()` and intelligent human-readable sentence synthesis (converting raw diffs into clear business narratives).
  - Instrumented sensitive mutations to automatically record before/after diffs in `admin_audit_log`:
    - **Product Price Edits**: `ProductService.update_price` (`PATCH /products/{id}/price`) records before/after wholesale and cost prices.
    - **Retailer Credit Limit Edits**: `RetailerService.update_credit_limit` (`PATCH /retailers/{id}/credit-limit`) records before/after authorized credit limits.
    - **Permission Matrix Edits**: `StaffService.update_role_permissions` (`PATCH /roles/{id}/permissions`) records added/removed permission codes per role.
    - **Staff Role Updates**: `StaffService.update_staff_role` (`PATCH /staff/{id}/role`) records before/after role assignment.
    - **Staff Status Toggles**: `StaffService.update_staff_status` (`PATCH /staff/{id}/status`) records activation/suspension.
    - **Product Deletions**: `ProductService.delete_product` records entity deletion.
- Created `GET /admin/audit-log` endpoint in FastAPI:
  - Paginated (`page`, `page_size`), filterable by `entity_type`, `actor_id`, `action`, `start_date`, `end_date`.
  - Protected with `require_permission("audit:view")` (accessible by Owner and roles with `audit:view`).
- Built rich frontend Audit Log UI in Next.js:
  - `apps/web/app/admin/audit/page.tsx`: Timeline interface with humanized event descriptions, entity type badges, actor attribution, filter bar, pagination, and "Inspect Diff" modal displaying before/after JSON states.
  - `apps/web/app/admin/settings/audit-log/page.tsx`: Alias route rendering audit timeline.
- Created test suite in `apps/api/tests/test_audit_log.py` verifying pricing mutations, credit limit changes, permission matrix updates, filtering, and 403 authorization enforcement (all 47 monorepo tests passing with 92% backend coverage).

### Decisions

- **Human-Readable Sentence Generation at Service Layer**: `AuditService` translates JSON state transitions into natural business language ("Owner changed Retailer 'X' credit limit from ₹50,000 to ₹75,000") while retaining raw JSON before/after snapshots for deep compliance inspection.
- **DIP Repository Pattern**: Created `AuditRepository` and `RetailerRepository` interfaces to ensure service layers never bind directly to database engines.
- **Reference List of Audit-Wrapped Mutations**:
  1. `product_price_updated`: `ProductService.update_price`
  2. `retailer_credit_limit_updated`: `RetailerService.update_credit_limit`
  3. `role_permissions_updated`: `StaffService.update_role_permissions`
  4. `staff_role_updated`: `StaffService.update_staff_role`
  5. `staff_status_updated`: `StaffService.update_staff_status`
  6. `product_deleted`: `ProductService.delete_product`

### Key values for future steps

- Audit log API: `GET /admin/audit-log`
- Product price update API: `PATCH /products/{id}/price`
- Retailer credit limit update API: `PATCH /retailers/{id}/credit-limit`
- Web Audit timeline: `/admin/audit` and `/admin/settings/audit-log`
- `AuditService.log(actor_id, action, entity_type, entity_id, before, after)` factory from `app.core.di`

### Files Created

- `apps/api/app/repositories/interfaces/audit_repository.py`
- `apps/api/app/repositories/impl/audit_repository.py`
- `apps/api/app/repositories/interfaces/retailer_repository.py`
- `apps/api/app/repositories/impl/retailer_repository.py`
- `apps/api/app/schemas/audit.py`
- `apps/api/app/schemas/products.py`
- `apps/api/app/schemas/retailers.py`
- `apps/api/app/services/audit_service.py`
- `apps/api/app/services/retailer_service.py`
- `apps/api/app/api/routers/audit.py`
- `apps/api/app/api/routers/products.py`
- `apps/api/app/api/routers/retailers.py`
- `apps/api/tests/test_audit_log.py`
- `apps/web/app/admin/audit/page.tsx`
- `apps/web/app/admin/settings/audit-log/page.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/app/repositories/interfaces/product_repository.py`
- `apps/api/app/repositories/impl/product_repository.py`
- `apps/api/app/services/product_service.py`
- `apps/api/app/services/staff_service.py`
- `apps/api/app/api/routers/staff.py`
- `apps/api/app/api/routers/roles.py`

---

## Step 4.1 — Liquid Glass Design Tokens (Black/White + Purple) & Gradient Backdrop

**Timestamp:** 2026-08-17T20:30:00Z
**Status:** COMPLETE

### What was done

- Established the core Phase 4 Liquid Glass visual identity and design token system in Tailwind CSS v4 and vanilla CSS:
  - **Base Palette**: Built a strict true black/white foundation with zero washed-out grays. Light mode uses `#ffffff`/`#fafafa` surfaces with near-black `#0a0a0a` text; Dark mode uses true near-black `#09090b`/`#141418` surfaces with off-white `#f5f5f7` text.
  - **Single Accent Color**: Anchored the entire platform on **Electric Violet Purple** (`#7c3aed` light / `#8b5cf6` dark luminance-lifted), with derivative tokens for hover (`--accent-hover`), subtle background tints (`--accent-subtle`), focus rings (`--accent-border`), and luminous glows (`--accent-glow`).
  - **Liquid Glass Token Layer**: Defined frosted glass surfaces with high-precision backdrop blurs (`16px`/`24px`), 1px specular top highlight gradients (`--glass-highlight`), subtle border contours (`--glass-border`), and deep diffusion shadows (`--glass-shadow`).
  - **Liquid Glass Utility Classes**: Added `.glass-panel`, `.glass-panel-elevated`, `.glass-button-primary`, `.glass-button-secondary`, `.glass-input`, and `.glow-purple`.
- Created fixed full-viewport `GradientBackdrop` component (`apps/web/components/GradientBackdrop.tsx`) featuring 3 multi-layered radial ambient glow blooms that drift smoothly via GPU-accelerated CSS keyframe animations, overlaid with a subtle SVG fractal noise grain layer for anti-banding.
- Built a robust, hydration-safe `ThemeProvider` (`apps/web/components/ThemeProvider.tsx`) and `ThemeToggle` (`apps/web/components/ThemeToggle.tsx`) utilizing React 19 `useSyncExternalStore`:
  - Persistent user choice stored in `localStorage` (`wareflow-theme`), defaulting to system OS preference on first visit.
  - Injected an inline anti-flash script in `layout.tsx` `<head>` ensuring 0 layout shifts or unstyled flashes on initial paint.
  - Added modern Topbar in `AppLayout.tsx` and updated `Sidebar.tsx` with unified liquid glass tokens and electric violet active item highlights.
- Created interactive developer `/styleguide` page (`apps/web/app/styleguide/page.tsx`) rendering side-by-side theme archetypes, token swatches, glass panel hierarchies, button states, form controls, and live modal demonstrations.
- Created unit test suite `apps/web/lib/__tests__/theme.test.ts` (10 web tests + 40 API tests passing across monorepo).

### Decisions

- **Palette locked**: Black/white base + single purple accent (Electric Violet `#7C3AED` / `#8B5CF6`), both themes — not proposed, decided.
- **Theme toggle is a real user choice (persisted)**: Explicit user preference persists in `localStorage` across sessions and reloads, falling back to OS `prefers-color-scheme` on first visit.
- **`useSyncExternalStore` for Theme Synchronization**: Eliminates cascading render lint warnings and ensures seamless hydration between server and client without flicker.
- **GPU-Accelerated Ambient Backdrop**: Liquid gradient blooms use CSS `will-change: transform` and gentle infinite keyframe translations for maximum 60fps rendering performance.

### Key values for future steps

- Primary Accent Color: Electric Violet `#7C3AED` (light) / `#8B5CF6` (dark)
- Background Base: `#FAFAFA` (light) / `#09090B` (dark)
- Glass Card Classes: `.glass-panel` (cards/panels) and `.glass-panel-elevated` (modals/popovers)
- Glass Button Classes: `.glass-button-primary` (main violet CTA) and `.glass-button-secondary` (frosted ghost)
- Backdrop Component: `<GradientBackdrop />` mounted at root layout
- Theme Context: `useTheme()` hook returning `{ theme, resolvedTheme, setTheme, toggleTheme }`
- Developer Styleguide: `/styleguide`

### Files Created

- `apps/web/components/GradientBackdrop.tsx`
- `apps/web/components/ThemeProvider.tsx`
- `apps/web/components/ThemeToggle.tsx`
- `apps/web/app/styleguide/page.tsx`
- `apps/web/lib/__tests__/theme.test.ts`

### Files Modified

- `apps/web/app/globals.css`
- `apps/web/app/layout.tsx`
- `apps/web/components/AppLayout.tsx`
- `apps/web/components/Sidebar.tsx`
- `apps/web/lib/nav.ts`

---

## Step 4.2 — Glass Component Primitives (Real Specular Refraction) + Motion Stack Wiring

**Timestamp:** 2026-08-17T18:55:00Z
**Status:** COMPLETE

### What was done

- Realistic specular-refraction glass is now the DEFAULT for every button and interactive control — not an opt-in stretch effect on one hero element.
- Created `GlassButton` flagship primitive with 1.5px shifting specular highlight, active spring compression for tactile feedback, and accessible HTML/polymorphic forwarding.
- Created `GlassCard` and `GlassPanel` with lighter edge-only refraction contours tuned for cost at larger surface areas (preserving GPU fill rates).
- Created elevated `GlassModal`, `GlassDropdown`, `GlassInput`, and `GlassBadge` primitives.
- Built layered Motion Stack infrastructure:
  - `motion` (Framer Motion) as default for React-driven UI transitions with shared spring physics presets (`MotionProvider`, `GlassMotion`).
  - `gsap` (+ ScrollTrigger) reserved for marketing/landing page timelines.
  - `@formkit/auto-animate` for dynamic list/grid mutations.
  - `@react-spring/web` for physics micro-interactions.
- Created architectural specifications in `docs/GLASS_GUIDE.md` and `docs/ANIMATION_GUIDE.md`.
- Updated `/styleguide` with interactive glass primitives showcase, modal demonstrations, and 24-button dense table benchmark.
- Added comprehensive unit tests in `apps/web/lib/__tests__/glass-primitives.test.tsx` (all 55 monorepo tests passing).

### Decisions

- **Realistic Specular Refraction as Default**: Every button and control receives specular top highlights and tactile spring responses — not an isolated hero gimmick.
- **Surface Area vs Cost Performance Hierarchy**: Refraction strength scales inversely with element count/size: small buttons get full specular shifts and active compression, while large panels get light-edge highlights.
- **Motion Domain Ownership**: Each library has one designated domain (`motion` for UI/route transitions, `gsap` for marketing sequences, `@formkit/auto-animate` for list reflows, `@react-spring/web` for physics gestures).

### Key values for future steps

- Flagship Button: `<GlassButton variant="primary|secondary|outline|ghost|destructive" size="sm|md|lg|icon">`
- Container Cards: `<GlassCard hoverable glow>`, `<GlassPanel elevated>`
- Overlays: `<GlassModal>`, `<GlassDropdown>`
- Form & Status: `<GlassInput>`, `<GlassBadge variant="accent|neutral|success|warning|error">`
- Motion Hook: `useMotionPresets()` (`snappy`, `glassMorph`, `gentle`, `bouncy`, `smoothFade`)
- Motion Wrappers: `<PageTransition>`, `<FadeIn>`, `<StaggerContainer>`, `<StaggerItem>`
- Specs: `docs/GLASS_GUIDE.md`, `docs/ANIMATION_GUIDE.md`

### Files Created

- `apps/web/lib/utils.ts`
- `apps/web/components/glass/GlassButton.tsx`
- `apps/web/components/glass/GlassCard.tsx`
- `apps/web/components/glass/GlassPanel.tsx`
- `apps/web/components/glass/GlassModal.tsx`
- `apps/web/components/glass/GlassDropdown.tsx`
- `apps/web/components/glass/GlassInput.tsx`
- `apps/web/components/glass/GlassBadge.tsx`
- `apps/web/components/glass/index.ts`
- `apps/web/components/motion/MotionProvider.tsx`
- `apps/web/components/motion/GlassMotion.tsx`
- `apps/web/lib/__tests__/glass-primitives.test.tsx`
- `docs/GLASS_GUIDE.md`
- `docs/ANIMATION_GUIDE.md`

### Files Modified

- `apps/web/package.json`
- `apps/web/app/layout.tsx`
- `apps/web/app/styleguide/page.tsx`

---

## Step 4.3 — Theme Settings: Dark/Light Toggle Persistence + Accent Customization

**Timestamp:** 2026-08-17T19:25:00Z
**Status:** COMPLETE

### What was done

- Created dedicated Appearance & Theme settings console in `/admin/settings/appearance` and portal alias `/portal/settings/appearance`.
- Implemented mode selection (Light / Dark / System) with real-time UI switching and persistence in both `localStorage` and the database `profiles` table via Alembic migration `0006_profile_appearance.py`.
- Designed and verified a curated set of 7 pre-tested accent swatches (`violet`, `indigo`, `emerald`, `cyan`, `rose`, `amber`, `cobalt`), with Electric Violet (`#7C3AED`) as the default.
- Upgraded `ThemeProvider` to dynamically inject CSS custom properties (`--accent`, `--accent-hover`, `--accent-subtle`, `--accent-border`, `--accent-glow`) across all root elements, re-theming buttons, active states, focus rings, and badges instantly with zero page reload.
- Upgraded `<head>` anti-flash script in `RootLayout` to load saved accent tokens before DOM paint, eliminating color flash on page load.
- Added `PATCH /profiles/preferences` endpoint in FastAPI and updated `GET /me` response model.
- Added unit test suites `apps/web/lib/__tests__/appearance.test.ts` and `apps/api/tests/test_appearance_preferences.py` (all 62 monorepo tests passing: 18 web + 44 API).

### Decisions

- **Accent Customization Scoped to Curated Pre-Tested Swatches**: Restricted accent choices to 7 verified swatches rather than an unconstrained color wheel to guarantee that every color passes WCAG AA contrast against both true black (`#09090B`) and white (`#FAFAFA`) glass backgrounds.
- **Fixed Glass Foundation**: The black/white liquid glass base (surfaces, specular bevels, blurs, borders) remains un-customizable to preserve design system coherence across all wholesale distribution screens.
- **Dual Preference Persistence**: Preferences are stored in `localStorage` for instant client-side rendering and synchronized with `profiles.theme_preference` and `profiles.accent_color` so preferences follow users across different machines/browsers.

### Key values for future steps

- Appearance Settings Route: `/admin/settings/appearance` (portal: `/portal/settings/appearance`)
- Preferences API: `PATCH /profiles/preferences` (`theme_preference`, `accent_color`)
- Curated Swatches: `ACCENT_SWATCHES` in `@/lib/theme-accents`
- Theme Context: `useTheme()` providing `theme`, `resolvedTheme`, `accent`, `currentSwatch`, `availableAccents`, `setTheme`, `setAccent`

### Files Created

- `apps/api/alembic/versions/0006_profile_appearance.py`
- `apps/api/tests/test_appearance_preferences.py`
- `apps/web/lib/theme-accents.ts`
- `apps/web/lib/__tests__/appearance.test.ts`
- `apps/web/app/admin/settings/appearance/page.tsx`
- `apps/web/app/portal/settings/appearance/page.tsx`

### Files Modified

- `apps/api/app/models/profile.py`
- `apps/api/app/schemas/profile.py`
- `apps/api/app/repositories/interfaces/profile_repository.py`
- `apps/api/app/repositories/impl/profile_repository.py`
- `apps/api/app/services/profile_service.py`
- `apps/api/app/api/routers/profiles.py`
- `apps/web/components/ThemeProvider.tsx`
- `apps/web/app/layout.tsx`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`

---

## Step 4.4 — Sitemap & Page Template System

**Timestamp:** 2026-08-18T02:25:00Z
**Status:** COMPLETE

### What was done

- Authored and finalized `docs/SITEMAP.md` documenting every screen across all 19 phases/domains (Auth, Dashboards, Inventory, Purchasing, Sales, Billing, Logistics, Analytics, Leads/Growth, Admin/Settings, External Portals) mapped strictly to one of four locked page templates.
- Established the locked 12-column responsive layout grid system (`grid grid-cols-12 gap-4 lg:gap-6`) and 4px spacing scale modeled on Linear, Stripe Dashboard, and Notion design benchmarks.
- Created `ListViewTemplate` with sticky search/filter bar, bulk actions, GlassCard table wrapper, and pagination controls.
- Created `DetailViewTemplate` with status badge, back link, and responsive 8-column main content + 4-column sticky side panel layout.
- Created `FormTemplate` & `FormSection` with grouped sectioned cards, inline validation hints, and a sticky bottom action bar (`Save Changes`, `Discard`, status indicator, `⌘S` shortcut) that never scrolls out of reach.
- Created `DashboardTemplate` with top KPI metric row (4-6 GlassCards with trend metrics and spark indicators) + 8/4 responsive chart and urgent alert grid.
- Wired `animejs` as the fifth and final motion library strictly scoped to SVG path morphing/draw-in and micro-button/icon press interactions (`AnimeCheckIcon`, `AnimeMorphIcon`, `AnimeMicroPress` in `@/components/motion/AnimeMicro`).
- Updated `docs/ANIMATION_GUIDE.md` with anime.js ownership row and updated `/styleguide` with interactive previews for all 4 templates and motion engines.
- Added comprehensive unit tests in `apps/web/lib/__tests__/templates.test.tsx` (all 67 monorepo tests passing: 23 web + 44 API).

### Decisions

- **Template Conformance Rule**: Every future feature phase screen must strictly map to one of the four locked templates (`ListViewTemplate`, `DetailViewTemplate`, `FormTemplate`, `DashboardTemplate`). No feature phase may invent an uncoordinated page structure from scratch.
- **12-Column Responsive Grid + 4px Base Spacing**: All layout geometry derives from the standard 12-column grid and 4px Tailwind spacing scale, guaranteeing proportional rhythm across viewports.
- **Narrowly Scoped anime.js Ownership**: `anime.js` is strictly isolated to SVG path animations and button micro-morphs, avoiding any functional overlap with `motion`, `gsap`, `@react-spring/web`, or `@formkit/auto-animate`.

### Key values for future steps

- Master Sitemap: `docs/SITEMAP.md`
- Templates: `@/components/templates` (`ListViewTemplate`, `DetailViewTemplate`, `FormTemplate`, `FormSection`, `DashboardTemplate`)
- Micro-Motion: `@/components/motion/AnimeMicro` (`AnimeCheckIcon`, `AnimeMorphIcon`, `AnimeMicroPress`)

### Files Created

- `docs/SITEMAP.md`
- `apps/web/components/motion/AnimeMicro.tsx`
- `apps/web/components/templates/ListViewTemplate.tsx`
- `apps/web/components/templates/DetailViewTemplate.tsx`
- `apps/web/components/templates/FormTemplate.tsx`
- `apps/web/components/templates/DashboardTemplate.tsx`
- `apps/web/components/templates/index.ts`
- `apps/web/lib/__tests__/templates.test.tsx`

### Files Modified

- `apps/web/package.json`
- `docs/ANIMATION_GUIDE.md`
- `apps/web/app/styleguide/page.tsx`
- `codebase_audit.md`

---

## Step 4.5 — 3D/Animated Marketing Landing Page

**Timestamp:** 2026-08-18T02:35:00Z
**Status:** COMPLETE

### What was done

- Installed `@react-three/fiber`, `@react-three/drei`, `three`, and `@types/three` for low-poly, mobile-optimized WebGL 3D rendering.
- Built `Hero3DCanvas.tsx` featuring low-poly floating wholesale inventory nodes (crates/pallets) with glass-refraction physical materials, specular edge wireframes, and mouse parallax tracking.
- Built `Hero3DFallback.tsx` with a lightweight, accessible SVG/CSS glass schematic for SSR, low-power devices, and `prefers-reduced-motion`.
- Implemented `HeroScene.tsx` using `useSyncExternalStore` and `next/dynamic` (`ssr: false`) to guarantee zero hydration mismatch and instant reduced-motion fallback.
- Created `AceternityBeams.tsx` delivering dynamic laser spotlights and luminous ambient radiant grid lines behind the hero headline.
- Enhanced `GradientBackdrop.tsx` with a 4-orb GPU-accelerated animated gradient mesh ensuring dynamic background life across the entire application.
- Implemented `BentoGrid.tsx` with GSAP ScrollTrigger animating 5 core feature cells (Low-Stock Reordering, AI Forecasting, WhatsApp Dispatches, GST/FSSAI Compliance, APMC Wholesale Map) with `once: true` to prevent scroll re-trigger jank.
- Assembled the public marketing landing page in `apps/web/app/page.tsx` outside the dashboard shell, featuring live telemetry tickers, security highlights, and CTA buttons routing to `/login`.
- Created comprehensive test suite in `apps/web/lib/__tests__/marketing.test.tsx` (all 72 monorepo unit tests passing: 28 web + 44 API).

### Decisions

- **Performance-Budget-Gates-Animation Rule**: Stated budget of First Contentful Paint < 1.0s, Hero Canvas < 25KB geometric footprint, Zero main thread blocking. 3D scenes lazy-load dynamically without SSR and cap `dpr` to `[1, 1.5]` on mobile.
- **First-Class Reduced-Motion Support**: Every animation layer (R3F 3D scene, GSAP ScrollTrigger, CSS keyframe ambient meshes) checks `prefers-reduced-motion: reduce` and provides immediate static/solid fallbacks.
- **Dynamic Site-Wide Background**: The entire website operates over an animated 4-orb floating gradient mesh with noise overlay to eliminate OLED banding while maintaining 60fps GPU performance.

### Key values for future steps

- 3D Hero Scene: `apps/web/components/marketing/HeroScene.tsx`
- 3D Canvas: `apps/web/components/marketing/Hero3DCanvas.tsx`
- 3D Fallback: `apps/web/components/marketing/Hero3DFallback.tsx`
- Bento Grid: `apps/web/components/marketing/BentoGrid.tsx`
- Beams Backdrop: `apps/web/components/marketing/AceternityBeams.tsx`
- Marketing Nav & Footer: `apps/web/components/marketing/MarketingNav.tsx`, `MarketingFooter.tsx`

### Files Created

- `apps/web/components/marketing/Hero3DCanvas.tsx`
- `apps/web/components/marketing/Hero3DFallback.tsx`
- `apps/web/components/marketing/HeroScene.tsx`
- `apps/web/components/marketing/AceternityBeams.tsx`
- `apps/web/components/marketing/BentoGrid.tsx`
- `apps/web/components/marketing/MarketingNav.tsx`
- `apps/web/components/marketing/MarketingFooter.tsx`
- `apps/web/lib/__tests__/marketing.test.tsx`

### Files Modified

- `apps/web/package.json`
- `apps/web/components/GradientBackdrop.tsx`
- `apps/web/app/page.tsx`
- `codebase_audit.md`

---

## Step 4.6 — Dashboard Shell with Page Transitions & Micro-interactions

**Timestamp:** 2026-08-18T02:55:00Z
**Status:** COMPLETE

### What was done

- Implemented standard `PageHeader` component (`apps/web/components/PageHeader.tsx`) providing responsive title, description, live badge, back-links, and primary/secondary action button slots for all application pages.
- Upgraded `Sidebar.tsx` into a full `GlassNav`:
  - Frosted liquid glass floating frame above the animated gradient backdrop.
  - Motion active-item indicator pill (`layoutId="active-sidebar-pill"`) with smooth spring sliding physics between routes.
  - Responsive mobile Sheet / Drawer below `lg` with smooth spring slide-in (`x: "-100%"` -> `x: 0`), accessible backdrop overlay, and automatic route-change dismiss.
- Upgraded `Topbar.tsx`:
  - Frosted `GlassPanel` floating header with responsive mobile hamburger trigger.
  - Live 0.02s Settlement telemetry pill.
  - Interactive Notification Center with `@formkit/auto-animate` for silky add/remove/dismiss actions.
  - User profile menu with avatar initials, role badge, quick links (Appearance, 2FA Security, Audit Log, Styleguide), and server-side sign out.
- Upgraded `AppLayout.tsx`:
  - Integrated `AnimatePresence mode="wait"` and `PageTransition` keyed by `pathname` for smooth, non-jarring route transitions.
  - Guaranteed 360px mobile responsiveness with zero horizontal overflow.
- Built `AnimatedNumber.tsx` (`NumberTicker`):
  - Direct ref DOM animation with `motion`'s `animate()` avoiding cascading React re-renders.
  - Animates on initial paint with snappy easing `[0.16, 1, 0.3, 1]`.
  - Does not re-animate distractingly on background refetches.
  - Respects `prefers-reduced-motion: reduce` with instant text render.
- Upgraded `apps/web/app/dashboard/page.tsx`:
  - Uses `DashboardTemplate` and `PageHeader`.
  - 4 animated KPI metrics with `AnimatedNumber` tickers.
  - Live recent orders table with `@formkit/auto-animate` for interactive dispatch simulations.
  - Urgent operations alert queue and terminal sync telemetry cards.
- Added comprehensive unit test suite in `apps/web/lib/__tests__/dashboard-shell.test.tsx` (all 36 web tests + 44 API tests passing).

### Decisions

- **Motion-Signals-State-Change Rule (Guardrail against over-animating)**: Motion is strictly reserved to draw attention to STATE CHANGES (active link shift, number count-up on load, row addition/removal in tables, drawer slide, route enter/exit). Motion MUST NEVER decorate static content or loop continuously without purpose.
- **Direct Ref Number Animation**: Numeric tickers mutate the DOM node directly during tweening to deliver 60fps animations without thrashing React component trees or triggering ESLint state cascading warnings.
- **Single PageHeader Standard**: Every page across all phases consumes `PageHeader` (directly or via templates) to enforce typographic consistency, breadcrumb navigation, and responsive action placement.

### Key values for future steps

- Page Header: `apps/web/components/PageHeader.tsx`
- Animated Number: `apps/web/components/motion/AnimatedNumber.tsx`
- Topbar: `apps/web/components/Topbar.tsx`
- Sidebar: `apps/web/components/Sidebar.tsx`
- App Layout: `apps/web/components/AppLayout.tsx`

### Files Created

- `apps/web/components/PageHeader.tsx`
- `apps/web/components/Topbar.tsx`
- `apps/web/components/motion/AnimatedNumber.tsx`
- `apps/web/lib/__tests__/dashboard-shell.test.tsx`

### Files Modified

- `apps/web/components/Sidebar.tsx`
- `apps/web/components/AppLayout.tsx`
- `apps/web/components/templates/DashboardTemplate.tsx`
- `apps/web/app/dashboard/page.tsx`
- `apps/api/tests/test_staff_and_roles.py`
- `codebase_audit.md`

---

## Step 4.7 — Empty/Skeleton/Status Primitives & Full Responsiveness Audit

**Timestamp:** 2026-08-18T03:15:00Z
**Status:** COMPLETE

### What was done

- Created universal `EmptyState.tsx` (`apps/web/components/EmptyState.tsx`) with subtle Motion entrance, frosted icon container, warehouse copy defaults ("No wholesale records found"), and primary/secondary action button slots.
- Created fluid gradient shimmer `SkeletonPrimitives.tsx` (`apps/web/components/SkeletonPrimitives.tsx`):
  - `SkeletonBox`: animated linear shimmer sweep.
  - `SkeletonText`: variable lines with 75% last line width.
  - `SkeletonBadge`: compact pill placeholder.
  - `SkeletonCard`: KPI metric card & detail card shimmer layouts.
  - `SkeletonTable(rows, cols)`: responsive grid shimmer matching table structures.
- Implemented universal `StatusBadge.tsx` (`apps/web/components/StatusBadge.tsx`) mapping every schema enum to token colors (`neutral`, `accent`, `success`, `warning`, `error`) with pulse dot for active/in-progress states.
- Implemented universal `DataTable.tsx` (`apps/web/components/DataTable.tsx`):
  - Generic type safe `<T>` data grid.
  - Sortable column headers with animated ascending/descending arrows.
  - Smooth row diffing powered by `@formkit/auto-animate`.
  - Built-in `isLoading` (`SkeletonTable`) and empty state (`EmptyState`) fallback views.
  - Automatic mobile card-view transformation below `md` (768px): restructures table rows into stacked `GlassCard` units with primary title header, key-value grid, and touch-target action buttons (>= 44px).
- Implemented Low-Power / Reduced-Transparency Fallback layer:
  - `apps/web/lib/device-performance.ts`: checks `prefers-reduced-transparency`, hardware memory (<4GB), and CPU concurrency (<=4 cores).
  - Wired into `ThemeProvider.tsx` using `useSyncExternalStore` for SSR/hydration safety.
  - Added `.low-power-glass` CSS rules in `apps/web/app/globals.css` disabling GPU backdrop-filters and ambient floating animations, switching to flat translucent surfaces to preserve 60fps on budget mobile hardware.
- Expanded `/styleguide` (`apps/web/app/styleguide/page.tsx`) with interactive showcases for `EmptyState`, `SkeletonCard`, `StatusBadge` matrix, live-sorted `DataTable` with shimmer/empty toggles, and real-time Low-Power Glass toggle.
- Created unit test suite in `apps/web/lib/__tests__/ui-primitives.test.tsx` (all 48 web tests + 44 API tests passing, 100% clean Next.js build).

### Verbatim Status → Color Map

| Status Enum          | Badge Variant | Label              | Pulse Dot | Context                  |
| -------------------- | ------------- | ------------------ | --------- | ------------------------ |
| `draft`              | `neutral`     | Draft              | No        | PO / SO / Invoice        |
| `submitted`          | `accent`      | Submitted          | Yes       | Purchase Order           |
| `confirmed`          | `accent`      | Confirmed          | Yes       | Purchase / Sales Order   |
| `processing`         | `accent`      | Processing         | Yes       | Warehouse Fulfillment    |
| `packed`             | `accent`      | Packed             | Yes       | Warehouse Packing        |
| `dispatched`         | `accent`      | Dispatched         | Yes       | Transport / Delivery     |
| `in_transit`         | `accent`      | In Transit         | Yes       | Active Dispatch Run      |
| `partially_received` | `warning`     | Partially Received | Yes       | Inward GRN               |
| `received`           | `success`     | Received           | No        | Inward GRN Complete      |
| `delivered`          | `success`     | Delivered          | No        | Sales Delivery           |
| `cancelled`          | `error`       | Cancelled          | No        | Order Cancelled          |
| `issued`             | `accent`      | Issued             | Yes       | Invoice Issued           |
| `paid`               | `success`     | Paid               | No        | Full Payment Cleared     |
| `partially_paid`     | `warning`     | Partially Paid     | Yes       | Partial Payment Received |
| `overdue`            | `error`       | Overdue            | Yes       | Payment Overdue          |
| `in_stock`           | `success`     | In Stock           | No        | Stock Balance Normal     |
| `low_stock`          | `warning`     | Low Stock          | Yes       | Below Reorder Level      |
| `out_of_stock`       | `error`       | Out of Stock       | Yes       | Zero Inventory Balance   |
| `overstocked`        | `neutral`     | Overstocked        | No        | Exceeds Max Threshold    |
| `inward`             | `success`     | Inward             | No        | Inventory Movement In    |
| `outward`            | `accent`      | Outward            | No        | Inventory Movement Out   |
| `good`               | `success`     | Good Condition     | No        | Batch Quality Passed     |
| `damaged`            | `error`       | Damaged            | Yes       | Quality Rejection        |
| `critical`           | `error`       | Critical Recall    | Yes       | Quarantine / Recall      |
| `active`             | `success`     | Active             | No        | User / Staff Account     |
| `suspended`          | `error`       | Suspended          | No        | Locked / Deactivated     |
| `enrolled`           | `success`     | 2FA Enrolled       | No        | TOTP Enabled             |
| `not_enrolled`       | `neutral`     | 2FA Disabled       | No        | TOTP Not Enrolled        |
| `required`           | `warning`     | 2FA Required       | Yes       | Mandatory 2FA Pending    |

### Decisions

- **Universal DataTable Rule**: All future list and ledger screens across the system MUST use `DataTable` rather than bespoke HTML tables; mobile card-view is automatically handled at 768px.
- **Graceful Performance Degradation**: Hardware capability and accessibility preferences automatically strip heavy multi-layer blur filters to ensure fluid 60fps responsiveness across low-end mobile devices without degrading UX or information hierarchy.

### Key values for future steps

- Universal Data Table: `apps/web/components/DataTable.tsx`
- Status Badge Component: `apps/web/components/StatusBadge.tsx`
- Empty State Component: `apps/web/components/EmptyState.tsx`
- Skeleton Loaders: `apps/web/components/SkeletonPrimitives.tsx`
- Low-Power Performance Utility: `apps/web/lib/device-performance.ts`

### Files Created

- `apps/web/components/StatusBadge.tsx`
- `apps/web/components/EmptyState.tsx`
- `apps/web/components/SkeletonPrimitives.tsx`
- `apps/web/components/DataTable.tsx`
- `apps/web/lib/device-performance.ts`
- `apps/web/lib/__tests__/ui-primitives.test.tsx`

### Files Modified

- `apps/web/app/globals.css`
- `apps/web/components/ThemeProvider.tsx`
- `apps/web/app/styleguide/page.tsx`
- `codebase_audit.md`

---

## Step 5.1 — ProductRepository Interface + Product/Category CRUD

**Timestamp:** 2026-08-18T14:25:00Z
**Status:** COMPLETE

### What was done

- **ProductRepository Interface Contract (`ProductRepositoryInterface`)**:
  - Defined strict Python `Protocol` in `apps/api/app/repositories/interfaces/product_repository.py`.
  - Comprehensive method surface for products: `get_by_id`, `get_by_sku`, `list_products` (with filters for `category_id`, `search`, `is_active`, `skip`, `limit`), `create_product`, `update_product`, `update_prices`, `deactivate_product`, `set_image_url`, `delete`, and `has_open_orders`.
  - Category operations: `list_categories`, `get_category_by_id`, `create_category`, `update_category`, `delete_category`.
  - Zero SQLAlchemy-specific types leaked into interface signatures.
- **Implementations (`SqlAlchemyProductRepository` & `InMemoryProductRepository`)**:
  - Implemented in `apps/api/app/repositories/impl/product_repository.py`.
  - `SqlAlchemyProductRepository`: PostgreSQL ORM queries with eager relationship joins (`joinedload(Product.category)`), case-insensitive search, and open order detection across `PurchaseOrderItem` (excluding received/cancelled POs) and `SalesOrderItem` (excluding delivered/cancelled SOs).
  - `InMemoryProductRepository`: In-memory dictionary store for fast, 100% isolated tests and proof of Dependency Inversion Principle.
- **Product Domain Service (`ProductService`)**:
  - Encapsulates business logic with constructor-injected repository (`ProductRepositoryInterface`), `AuditService`, and `StorageServiceInterface`.
  - Enforces SKU natural key uniqueness (returns HTTP 409 Conflict if SKU exists).
  - Enforces price non-negativity validation (`wholesale_price >= 0`, `cost_price >= 0`).
  - Guards product deactivation: strictly blocks deactivation if open Purchase Orders or Sales Orders reference the SKU (returns HTTP 400 Bad Request).
  - Emits immutable audit log records for `product_created`, `product_updated`, `product_price_updated`, `product_deactivated`, `product_image_updated`, and category mutations.
- **Storage Service (`StorageServiceInterface` & `SupabaseStorageService`)**:
  - Built in `apps/api/app/services/storage_service.py` with `MockStorageService` for unit testing.
  - Enforces file type validation (JPEG, PNG, WebP) and size validation (<=5MB).
  - Uploads to Supabase Storage `product-images` public bucket with unique UUID filename generation and public URL resolution.
- **Schemas & Routers**:
  - Created `apps/api/app/schemas/categories.py` and updated `apps/api/app/schemas/products.py` (with `description`, `content_details`, `category`, and image upload response schemas).
  - Implemented `apps/api/app/api/routers/categories.py` and upgraded `apps/api/app/api/routers/products.py` with multipart image upload endpoint `POST /products/{id}/image`.
  - Registered `categories` and `products` routers in `main.py` and wired DI dependencies in `di.py`.
- **Frontend Management UI**:
  - Created `/admin/products` (`apps/web/app/admin/products/page.tsx`) with `ListViewTemplate`, `DataTable`, category filters, live search, `StatusBadge`, Create/Edit `GlassModal`, and Drag-and-drop Image Upload modal with client-side type/size validation and thumbnail previews.
  - Created `/admin/categories` (`apps/web/app/admin/categories/page.tsx`) with taxonomy tree visualization, create/edit modals, and delete guards.
  - Updated `apps/web/lib/nav.ts` to include Product Catalog and Categories under Wholesale Operations.
- **Testing & Verification**:
  - Created unit tests in `apps/api/tests/test_products.py` verifying DIP swappability, duplicate SKU 409, open PO deactivation blocking, image validation, and CRUD endpoints.
  - Created unit tests in `apps/web/lib/__tests__/products.test.tsx`.
  - Monorepo 100% green: 48 backend pytest tests passing, 51 frontend vitest tests passing, 0 ESLint warnings, 0 ruff errors, and successful Next.js production build.

### Decisions

- **DIP Compliance as Architectural Mandate**: `ProductService` depends solely on `ProductRepositoryInterface` (Protocol) and `StorageServiceInterface`, never importing concrete database models or sessions directly.
- **SKU as Natural Key**: Uniqueness is strictly enforced in both database unique indexes and service-layer validation with friendly 409 Conflict errors.
- **Open Order Deactivation Guard**: Products referenced in active supply chain workflows (open POs or SOs) cannot be deactivated until orders are delivered, received, or cancelled.

### Key values for future steps

- Product Repository Interface: `apps/api/app/repositories/interfaces/product_repository.py`
- Product Repository Impl: `apps/api/app/repositories/impl/product_repository.py`
- Product Domain Service: `apps/api/app/services/product_service.py`
- Storage Service: `apps/api/app/services/storage_service.py`
- Product Schemas: `apps/api/app/schemas/products.py` & `categories.py`
- Product Web Console: `/admin/products`
- Category Web Console: `/admin/categories`

### Files Created

- `apps/api/app/schemas/categories.py`
- `apps/api/app/api/routers/categories.py`
- `apps/api/app/services/storage_service.py`
- `apps/api/tests/test_products.py`
- `apps/web/app/admin/products/page.tsx`
- `apps/web/app/admin/categories/page.tsx`
- `apps/web/lib/__tests__/products.test.tsx`

### Files Modified

- `apps/api/app/repositories/interfaces/product_repository.py`
- `apps/api/app/repositories/impl/product_repository.py`
- `apps/api/app/services/product_service.py`
- `apps/api/app/schemas/products.py`
- `apps/api/app/api/routers/products.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/requirements.txt`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`

## Step 5.2 — Unit-of-Measure (UoM) Conversion

**Timestamp:** 2026-08-18T14:40:00Z
**Status:** COMPLETE

### What was done

- **UoM Repository Interface & Implementations**:
  - Created `apps/api/app/repositories/interfaces/uom_repository.py` defining `UomRepositoryInterface` Protocol (`list_uoms`, `get_uom_by_id`, `get_uom_by_abbreviation`, `create_uom`, `update_uom`, `delete_uom`, `list_product_conversions`, `get_conversion_by_id`, `get_conversion_between`, `create_or_update_conversion`, `delete_conversion`, `get_product_base_uom_id`).
  - Created `apps/api/app/repositories/impl/uom_repository.py` implementing `SqlAlchemyUomRepository` and `InMemoryUomRepository` for fast zero-IO testing.
- **UoM Domain Service & Graph Traversal**:
  - Implemented `apps/api/app/services/uom_service.py` with `UomService` and `UomConversionError`.
  - Implemented multi-hop conversion factor resolution using breadth-first search (BFS) over product conversion ratios (supports multi-level packaging hierarchies e.g., Pallet -> Master Carton -> Case -> Pack -> Piece, direct and inverse conversions).
  - Implemented single-point-of-truth stock-movement boundary rule: `convert_to_base_uom(product_id, qty, uom_id)` guarantees all stock movements and batch quantities are strictly written in base UoM.
  - Added full audit trail logging on UoM and Conversion mutation events.
- **Pydantic Schemas & REST Router**:
  - Created `apps/api/app/schemas/uom.py` for request and response validation.
  - Implemented `apps/api/app/api/routers/uom.py` registering endpoints: `GET /uom`, `POST /uom`, `PATCH /uom/{id}`, `DELETE /uom/{id}`, `GET /products/{id}/conversions`, `POST /products/{id}/conversions`, `DELETE /products/{id}/conversions/{id}`, `POST /products/{id}/convert`.
  - Registered router in `apps/api/app/main.py` and wired DI in `apps/api/app/core/di.py`.
- **Frontend Management & Interactive Calculator**:
  - Updated `apps/web/app/admin/products/page.tsx` with Base Unit selector linked to `/uom` catalog.
  - Added dedicated Packaging Ratios Manager modal with live conversions table, ratio deletion, and ratio definition wizard.
  - Integrated interactive Live Conversion Calculator widget enabling real-time conversion preview testing.
  - Updated `GlassModal` to support `2xl` max-width and `apiClient` to support multipart `upload`.
- **Automated Tests & Quality Verification**:
  - Created `apps/api/tests/test_uom.py` validating DIP swappability, receiving 5 cases -> 120 base units, selling pieces deducting base units, 1:1 default fallback without conversion rule, error handling on unresolvable ratios, and full REST lifecycle.
  - Created `apps/web/lib/__tests__/uom.test.tsx` verifying product catalog table rendering with base units and conversion explanations.
  - Monorepo 100% green: 54 pytest tests passing, 53 vitest tests passing, 0 ruff errors, 0 ESLint warnings, and Next.js build succeeding.

### Decisions

- **Graph Traversal (BFS) for Packaging Ratios**: Resolving conversions via adjacency list BFS ensures support for arbitrary packaging chains (e.g. Pallet -> Case -> Inner Pack -> Piece) and inverse conversions without hardcoding fixed levels.
- **Strict Boundary Conversion Rule**: Inventory ledger entries and warehouse stock batches store quantities exclusively in the product's `base_uom_id`. Purchase order items and sales order items carry their own operational `uom_id` and are converted to base UoM at the exact moment they touch stock movements.
- **Graceful Default Fallback**: If a product has no custom packaging conversion defined, transactions default to 1:1 in its base unit without runtime error.

### Key values for future steps

- UoM Repository Interface: `apps/api/app/repositories/interfaces/uom_repository.py`
- UoM Repository Impl: `apps/api/app/repositories/impl/uom_repository.py`
- UoM Domain Service: `apps/api/app/services/uom_service.py`
- Stock Ledger Conversion Rule: `uom_service.convert_to_base_uom(product_id, qty, uom_id)`
- Multi-hop Conversion Function: `uom_service.convert(product_id, qty, from_uom_id, to_uom_id)`
- UoM Router: `apps/api/app/api/routers/uom.py` (`/uom`, `/products/{id}/conversions`, `/products/{id}/convert`)

### Files Created

- `apps/api/app/repositories/interfaces/uom_repository.py`
- `apps/api/app/repositories/impl/uom_repository.py`
- `apps/api/app/schemas/uom.py`
- `apps/api/app/services/uom_service.py`
- `apps/api/app/api/routers/uom.py`
- `apps/api/tests/test_uom.py`
- `apps/web/lib/__tests__/uom.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/app/schemas/products.py`
- `apps/api/app/repositories/impl/product_repository.py`
- `apps/web/app/admin/products/page.tsx`
- `apps/web/components/glass/GlassModal.tsx`
- `apps/web/lib/api-client.ts`
- `memory.md`
- `codebase_audit.md`

---

## Step 5.3 — Multi-Warehouse Batch Stock View

**Timestamp:** 2026-08-18T09:33:00Z
**Status:** COMPLETE

### What was done

- **StockRepository Protocol & Implementations**:
  - Defined `StockRepositoryInterface` in `apps/api/app/repositories/interfaces/stock_repository.py` specifying: `get_on_hand(product_id, warehouse_id=None)`, `get_batches_by_product(product_id, warehouse_id=None)` (FIFO sorted by `expiry_date.asc()`, `received_at.asc()`), `get_batches_expiring_soon(days=30, warehouse_id=None)`, `get_all_warehouses(active_only=True)`, `get_warehouse_by_id(warehouse_id)`, `get_stock_overview_data(warehouse_id=None, category_id=None, search=None)`, and `get_product_with_base_uom(product_id)`.
  - Implemented `SqlAlchemyStockRepository` and `InMemoryStockRepository` in `apps/api/app/repositories/impl/stock_repository.py`.
- **Stock Domain Service**:
  - Implemented `StockService` in `apps/api/app/services/stock_service.py` with health threshold calculation:
    - `ok`: `total_on_hand > reorder_point`
    - `low`: `0.25 * reorder_point < total_on_hand <= reorder_point`
    - `critical`: `total_on_hand <= 0.25 * reorder_point` (or 0 / negative)
  - Integrated `UomService` for secondary display conversion (e.g. `120 pcs` $\rightarrow$ `5 Cases`).
  - Added methods `get_product_stock`, `get_stock_overview`, `get_batches_expiring_soon`, and `list_warehouses`.
- **FastAPI Endpoints**:
  - Created router `apps/api/app/api/routers/stock.py` registered in `main.py` and `di.py`:
    - `GET /stock/overview` (summary counts, list of products with on-hand quantities, warehouse breakdown chips, health badges, filterable by `warehouse_id`, `category_id`, `status`, `search`).
    - `GET /stock/warehouses` (active warehouse list).
    - `GET /stock/expiring` (batches expiring within horizon days).
    - `GET /products/{product_id}/stock` (detailed product stock with warehouse breakdown and active FIFO batch list).
- **Frontend Inventory View**:
  - Built `/admin/inventory` page in `apps/web/app/admin/inventory/page.tsx` using `ListViewTemplate` and `DataTable`.
  - Top summary cards: Stocked SKUs, Healthy Stock, Low Stock Alerts, Critical / Depleted Items.
  - Interactive filters for Warehouse, Category, Health Status, and dynamic Search.
  - Per-warehouse distribution chips, reorder threshold indicator, and `StatusBadge`.
  - Batch detail drawer/modal with expiry horizon badges (Expired, $\le 30$d, $> 30$d).
  - Updated `apps/web/lib/nav.ts` to route "Inventory & Stock" to `/admin/inventory`.
  - Updated `StatusBadge` `STATUS_MAP` with `ok`, `low`, and `critical` mappings.
- **Verification & Testing**:
  - 60 Pytest tests passing (including 6 new tests in `test_stock.py` covering DIP verification, spot-check SQL sum match, health thresholds, warehouse/category filtering, and API endpoints).
  - 54 Vitest unit tests passing (including `stock.test.tsx`).
  - Next.js production build succeeded with 21 valid routes.
  - 0 Ruff lint warnings and 0 ESLint errors.

### Decisions

- **Stock Health Threshold Location**: Defined directly in `StockService.calculate_stock_status(on_hand, reorder_point)` to ensure consistent evaluation across REST API, reports, and UI.
- **Expiry Horizon Warning**: Set default horizon to 30 days (`<= 30` days highlighted with amber warning pill, expired items flagged in bold red).
- **Secondary Display Conversion**: If a product defines packaging UoM conversions (e.g., Case or Box), the stock overview displays the base units (`120 pcs`) alongside the largest packaging unit (`≈ 5 Cases`) for warehouse picking efficiency.

### Key values for future steps

- Stock Repository Interface: `apps/api/app/repositories/interfaces/stock_repository.py`
- Stock Repository Implementation: `apps/api/app/repositories/impl/stock_repository.py`
- Stock Domain Service: `apps/api/app/services/stock_service.py`
- Stock Status Thresholds:
  - `ok`: `on_hand > reorder_point`
  - `low`: `0.25 * reorder_point < on_hand <= reorder_point`
  - `critical`: `on_hand <= 0.25 * reorder_point`
- Stock Endpoints: `GET /stock/overview`, `GET /stock/warehouses`, `GET /stock/expiring`, `GET /products/{id}/stock`
- Inventory Web Page: `apps/web/app/admin/inventory/page.tsx`

### Files Created

- `apps/api/app/repositories/interfaces/stock_repository.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/api/app/schemas/stock.py`
- `apps/api/app/services/stock_service.py`
- `apps/api/app/api/routers/stock.py`
- `apps/api/tests/test_stock.py`
- `apps/web/app/admin/inventory/page.tsx`
- `apps/web/lib/__tests__/stock.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/components/StatusBadge.tsx`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

## Step 6.1 — Stock Value & Composition Charts

**Timestamp:** 2026-08-18T10:00:00Z
**Status:** COMPLETE

### What was done

- **Installed recharts in web frontend**: Added `recharts@^2.15.1` to `apps/web`.
- **Domain Layer & Schemas (`apps/api/app/schemas/stock_analytics.py`)**:
  - `StockValueSummary`: total stock valuation ($\sum \text{qty} \times \text{cost\_price}$), total units, total products, category breakdowns with percentage shares, warehouse allocations.
  - `StockHealthDistribution`: counts and percentage distributions across 4 health bands (`healthy`, `low`, `critical`, `out_of_stock`).
  - `TopProductsResponse`: top 10 products ranked by tied-up capital and top 10 by on-hand quantity.
  - `ExpiryTimelineResponse`: forward-looking 6-window expiry buckets (`expired`, `this_week`, `this_month`, `next_3_months`, `later`, `no_expiry`).
- **Repository Layer (`StockAnalyticsRepositoryInterface`)**:
  - Defined protocol in `apps/api/app/repositories/interfaces/stock_analytics_repository.py`.
  - Implemented `SqlAlchemyStockAnalyticsRepository` and `InMemoryStockAnalyticsRepository` in `apps/api/app/repositories/impl/stock_analytics_repository.py`.
  - Cast numeric computations to `float` for SQLite and PostgreSQL engine portability.
- **Service Layer (`StockAnalyticsService`)**:
  - Implemented business logic in `apps/api/app/services/stock_analytics_service.py` adhering strictly to SRP and DIP.
  - Dynamically calculates category valuation percentages, health band thresholds, and 6-window batch expiration horizons.
- **API Router (`/analytics/stock`)**:
  - Created router `apps/api/app/api/routers/stock_analytics.py`:
    - `GET /analytics/stock/value-summary`
    - `GET /analytics/stock/health-distribution`
    - `GET /analytics/stock/top-value-products`
    - `GET /analytics/stock/expiry-timeline`
  - Registered in `apps/api/app/core/di.py` and `apps/api/app/main.py`.
- **Frontend Analytics View (`apps/web/app/admin/analytics/stock/page.tsx`)**:
  - Built full dashboard page using `DashboardTemplate` and `AppLayout`.
  - 4 Top KPI Cards wrapped in `GlassCard`: Total Valuation (₹ formatted with `AnimatedNumber`), Total Stocked Units, Healthy Stock Count, Attention Required Count.
  - Donut Chart: Capital Concentration by Category using `recharts` (`PieChart`, `Pie`, `Cell`, `Tooltip`, custom glassmorphic tooltip).
  - Bar Chart: Valuation by Storage Warehouse using `recharts` (`BarChart`, `Bar`, `XAxis`, `YAxis`, `CartesianGrid`).
  - Ranked Ranking List: Top 10 Products by Capital Tied-Up with cost price and unit metrics.
  - Stock Health Meter: Multi-segmented progress bar with status cards.
  - Batch Expiry Horizon: 6-window timeline breakdown with `GlassBadge` danger/warning levels.
  - Updated `apps/web/lib/nav.ts` with "Stock Analytics" under Wholesale Operations.
- **Testing & Verification**:
  - 6 Pytest unit tests in `apps/api/tests/test_analytics_stock.py` (DIP verification with InMemory repo, exact SQL parity, critical threshold reclassification, top products, expiry horizons, API lifecycle).
  - 66 Pytest tests passing total (100% green).
  - Vitest unit test in `apps/web/lib/__tests__/stock-analytics.test.tsx` (55 tests passing across 14 test suites).
  - Next.js production build (`next build`) succeeded with 22 routes.
  - 0 Ruff lint errors, 0 ESLint errors, 100% Prettier formatting compliant.

### Decisions

- **Stock Value vs Spend Charts**: Stock VALUE charts compute live balances immediately with Phase 5 inventory structures. SPEND-over-time charts will be fed in later phases once real purchase orders are completed.
- **Floating Point Compatibility**: SQLAlchemy aggregation expressions use `.cast(Float)` or Python `float()` coercions to ensure seamless test execution across SQLite in-memory test databases and PostgreSQL production instances.
- **Stock Health Bands Parity**: Stock health classification on the dashboard strictly mirrors Step 5.3 rules (`healthy` > reorder_point, `low` between 25% and 100%, `critical` <= 25%, `out_of_stock` <= 0).

### Key values for future steps

- Stock Analytics Repository Interface: `apps/api/app/repositories/interfaces/stock_analytics_repository.py`
- Stock Analytics Repository Implementation: `apps/api/app/repositories/impl/stock_analytics_repository.py`
- Stock Analytics Domain Service: `apps/api/app/services/stock_analytics_service.py`
- Stock Analytics Endpoints:
  - `GET /analytics/stock/value-summary`
  - `GET /analytics/stock/health-distribution`
  - `GET /analytics/stock/top-value-products`
  - `GET /analytics/stock/expiry-timeline`
- Stock Analytics Web Dashboard: `apps/web/app/admin/analytics/stock/page.tsx`

### Files Created

- `apps/api/app/schemas/stock_analytics.py`
- `apps/api/app/repositories/interfaces/stock_analytics_repository.py`
- `apps/api/app/repositories/impl/stock_analytics_repository.py`
- `apps/api/app/services/stock_analytics_service.py`
- `apps/api/app/api/routers/stock_analytics.py`
- `apps/api/tests/test_analytics_stock.py`
- `apps/web/app/admin/analytics/stock/page.tsx`
- `apps/web/lib/__tests__/stock-analytics.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/package.json`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

## Step 6.2 — Purchasing Spend & Trend Charts

**Timestamp:** 2026-08-18T10:00:00Z
**Status:** COMPLETE

### What was done

- **Backend Schemas (`apps/api/app/schemas/stock_analytics.py`)**:
  - Added `MonthlySpendItem`, `SpendTrendResponse`, `SupplierSpendItem`, `SupplierSpendResponse`, `CategorySpendItem`, `CategorySpendResponse`, `ProductCostPoint`, `ProductCostTrendItem`, and `AvgCostTrendResponse`.
- **Repository Layer (`StockAnalyticsRepositoryInterface`)**:
  - Added query methods: `get_spend_trend_data`, `get_spend_by_supplier_data`, `get_spend_by_category_data`, `get_product_cost_history_data` in [`stock_analytics_repository.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/repositories/interfaces/stock_analytics_repository.py).
  - Implemented SQL joins across `purchase_orders`, `purchase_order_items`, `suppliers`, and `categories` with float coercions in `SqlAlchemyStockAnalyticsRepository` and full in-memory support in `InMemoryStockAnalyticsRepository`.
- **Service Layer (`StockAnalyticsService`)**:
  - Implemented `get_spend_trend` (12-month calendar bucketing with zeros for empty history, total spend, and monthly average).
  - Implemented `get_spend_by_supplier` and `get_spend_by_category` with percentage shares of total procurement capital.
  - Implemented `get_avg_cost_trend` with baseline catalog cost price integration, and price creep percentage calculation (+25%, 0% flat line for single-point history).
- **FastAPI Endpoints (`apps/api/app/api/routers/stock_analytics.py`)**:
  - `GET /analytics/stock/spend-trend`
  - `GET /analytics/stock/spend-by-supplier`
  - `GET /analytics/stock/spend-by-category`
  - `GET /analytics/stock/avg-cost-trend`
- **Frontend Spend Intelligence View (`apps/web/app/admin/analytics/stock/page.tsx`)**:
  - Section 2: "Purchasing Spend & Cost Trend Intelligence" added below valuation composition.
  - 12-Month Spend Trend Area Chart using `recharts` `<AreaChart>` with gradient purple fill.
  - Spend by Supplier Horizontal Bar Chart with vendor allocation percentages.
  - Spend by Category Donut Chart with custom palette cells.
  - Product Cost Price Evolution & Price Creep Tracker with interactive SKU inspector dropdown and line chart.
  - Custom `EmptySpendState` components for all spend widgets displaying a clear, friendly placeholder (_"No purchase data yet — this fills in automatically once you start receiving stock in Phase 6."_).
  - Interactive time horizon selector (6M, 12M, 24M) dynamically requesting backend window sizes.
- **Testing & Verification**:
  - Added 5 new Pytest unit tests in `apps/api/tests/test_analytics_stock.py` (empty pre-Phase 6 verification, populated PO calculation, single-cost flat line guarantee, price creep calculation, REST API endpoints).
  - All 71 Pytest backend tests passing (100% green).
  - Added frontend test cases in `apps/web/lib/__tests__/stock-analytics.test.tsx` verifying clean empty states and populated spend charts (56 tests passing across 14 test suites).
  - Next.js production build (`next build`) succeeded with 22 routes.
  - 0 Ruff lint warnings, 0 ESLint errors, 100% Prettier formatting compliant.

### Decisions

- **Forward-Built Pre-Phase 6 Spend Infrastructure**: Spend analytics endpoints return valid empty structures (0 total spend, 0 orders, zero-filled monthly slots) and frontend charts render polished `EmptySpendState` cards without division-by-zero, NaN, or console errors.
- **Flat Line for Single Cost Point**: If a product has only 1 recorded cost point (its baseline catalog cost price), the cost trend plots a stable flat line with `pct_change = 0.0` rather than throwing an error.

### Key values for future steps

- Spend Trend Endpoint: `GET /analytics/stock/spend-trend`
- Spend by Supplier Endpoint: `GET /analytics/stock/spend-by-supplier`
- Spend by Category Endpoint: `GET /analytics/stock/spend-by-category`
- Avg Cost Trend Endpoint: `GET /analytics/stock/avg-cost-trend`
- Empty State Rule: Pre-Phase 6 forward-built charts stay in clean empty state until purchase order line items are created and received in Phase 6.

### Files Modified

- `apps/api/app/schemas/stock_analytics.py`
- `apps/api/app/repositories/interfaces/stock_analytics_repository.py`
- `apps/api/app/repositories/impl/stock_analytics_repository.py`
- `apps/api/app/services/stock_analytics_service.py`
- `apps/api/app/api/routers/stock_analytics.py`
- `apps/api/tests/test_analytics_stock.py`
- `apps/web/app/admin/analytics/stock/page.tsx`
- `apps/web/lib/__tests__/stock-analytics.test.tsx`
- `memory.md`
- `codebase_audit.md`

---

## Step 7.1 — Supplier CRUD

**Timestamp:** 2026-08-18T10:20:00Z
**Status:** COMPLETE

### What was done

- **Backend Schemas (`apps/api/app/schemas/suppliers.py`)**:
  - Implemented `SupplierCreateRequest`, `SupplierUpdateRequest`, and `SupplierResponse` with field validators for uppercase GSTIN normalization, name cleaning, and length constraints.
- **Repository Abstraction & Impl (`SupplierRepositoryInterface`)**:
  - Defined `SupplierRepositoryInterface` Protocol in [`supplier_repository.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/repositories/interfaces/supplier_repository.py) (`get_by_id`, `get_by_name`, `list_suppliers`, `create_supplier`, `update_supplier`, `delete_supplier`).
  - Implemented `SqlAlchemySupplierRepository` (using SQLAlchemy with case-insensitive search and active status filters) and `InMemorySupplierRepository` (for high-speed unit testing and DIP proof) in [`apps/api/app/repositories/impl/supplier_repository.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/repositories/impl/supplier_repository.py).
- **Service Layer (`SupplierService` in `apps/api/app/services/supplier_service.py`)**:
  - Implemented duplicate supplier name check (case-insensitive) raising friendly 409 Conflict.
  - Implemented Indian 15-character GSTIN format validation (`^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`).
  - Implemented contact phone (7-15 digits) and email syntax validation.
  - Integrated administrative audit logging (`supplier_created`, `supplier_updated`) recording before/after state diffs.
- **Dependency Injection & Routing**:
  - Wired `get_supplier_repository`, `get_db_supplier_repository`, and `get_supplier_service` in [`apps/api/app/core/di.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/core/di.py).
  - Created [`apps/api/app/api/routers/suppliers.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/api/routers/suppliers.py) (`GET /suppliers`, `POST /suppliers`, `GET /suppliers/{id}`, `PATCH /suppliers/{id}`).
  - Registered `suppliers.router` in [`apps/api/app/main.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/main.py).
- **Frontend Liquid Glass Admin UI (`apps/web/app/admin/suppliers/page.tsx`)**:
  - Built `/admin/suppliers` using `ListViewTemplate` and responsive `DataTable`.
  - Added KPI summary cards: Total Vendors, Active Suppliers, GSTIN Verified, and FSSAI Certified.
  - Added live text search and status filter tabs (All / Active / Inactive).
  - Added Create / Edit Supplier modal with validation for company name, contact person, phone, email, address, 15-digit GSTIN, 14-digit FSSAI license, expiry date, and active toggle.
  - Added "Suppliers & Vendors" navigation item to `apps/web/lib/nav.ts` under Wholesale Operations.
- **Testing & Verification**:
  - Added 6 automated Pytest tests in `apps/api/tests/test_suppliers.py` (InMemory CRUD, duplicate name 409, GSTIN validation, contact info checks, SqlAlchemy persistence, and FastAPI REST endpoints).
  - 77/77 Pytest tests passing (100% green).
  - Added 3 Vitest tests in `apps/web/lib/__tests__/suppliers.test.tsx` verifying stats rendering, search filtering, and create/update submission flow (59 tests passing across 15 test suites).
  - 0 Ruff lint warnings, 0 ESLint errors, 100% Prettier formatted.
  - Next.js production build (`next build`) succeeded with 23 routes.

### Decisions

- **Pattern Reused Identically from Phase 5**: Reused the exact `Protocol` interface + SQLAlchemy / InMemory repository + Domain Service + DI factory pattern established in Step 5.1, confirming complete generalization.
- **GSTIN Normalization**: Handled at both schema level (uppercase transformation) and service regex validation level to protect against malformed tax identifiers.

### Key values for future steps

- Supplier Listing Endpoint: `GET /suppliers`
- Supplier Creation Endpoint: `POST /suppliers`
- Supplier Detail Endpoint: `GET /suppliers/{id}`
- Supplier Patch Endpoint: `PATCH /suppliers/{id}`
- Web Admin URL: `/admin/suppliers`
- Permissions: `inventory:view` for read operations; `inventory:manage` for create/update.

### Files Created

- `apps/api/app/schemas/suppliers.py`
- `apps/api/app/repositories/interfaces/supplier_repository.py`
- `apps/api/app/repositories/impl/supplier_repository.py`
- `apps/api/app/services/supplier_service.py`
- `apps/api/app/api/routers/suppliers.py`
- `apps/api/tests/test_suppliers.py`
- `apps/web/app/admin/suppliers/page.tsx`
- `apps/web/lib/__tests__/suppliers.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/lib/nav.ts`
- `apps/web/app/admin/analytics/stock/page.tsx`
- `memory.md`
- `codebase_audit.md`

---

### Step 7.2 — Purchase Orders & Goods Receiving

**Timestamp:** 2026-08-18T16:30:00Z
**Status:** COMPLETE

### What was done

- **Schemas & Data Models (`apps/api/app/schemas/purchase_orders.py`)**:
  - Defined Pydantic v2 schemas: `POItemCreateRequest`, `POCreateRequest`, `POItemUpdateRequest`, `POUpdateRequest`, `POReceiveItemRequest`, `POReceiveRequest`, `POItemResponse`, `PurchaseOrderResponse`, `PurchaseOrderListResponse`.
- **Purchase Order Repository & Stock Receipt Extensions**:
  - Created `PurchaseOrderRepositoryInterface` protocol in [`apps/api/app/repositories/interfaces/purchase_order_repository.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/repositories/interfaces/purchase_order_repository.py).
  - Created `SqlAlchemyPurchaseOrderRepository` with eager relationship loading and `InMemoryPurchaseOrderRepository` in [`apps/api/app/repositories/impl/purchase_order_repository.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/repositories/impl/purchase_order_repository.py).
  - Extended `StockRepositoryInterface` and implementations with `record_stock_receipt(...)` for atomic batch upsert and `stock_movements(type=in)` ledger generation.
- **Stock Service & Purchase Order Service (`apps/api/app/services/`)**:
  - Extended `StockService` with `receive_stock(...)` integrating 5.2's `UomService.convert_to_base_uom(...)` converter.
  - Built `PurchaseOrderService` in [`apps/api/app/services/purchase_order_service.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/services/purchase_order_service.py):
    - `create_draft_po`: Validates active supplier and positive line items, computes total amounts, generates unique PO numbers (`PO-YYYYMM-XXXX`).
    - `update_draft_po`: Strict draft status guard protecting against post-order modifications.
    - `transition_to_ordered`: Moves PO from `DRAFT` to `ORDERED`.
    - `receive_goods`: Single-door goods receiving pipeline that validates pending item balances, converts incoming units to base UoM, records inbound stock movement and batch entry, updates line item received quantities, and auto-derives `PARTIALLY_RECEIVED` vs `RECEIVED` status.
    - Integrated administrative audit logging for `purchase_order_created`, `purchase_order_updated`, `purchase_order_ordered`, and `purchase_order_goods_received`.
- **Dependency Injection & Routing**:
  - Wired `get_purchase_order_repository`, `get_db_purchase_order_repository`, and `get_purchase_order_service` in [`apps/api/app/core/di.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/core/di.py).
  - Created [`apps/api/app/api/routers/purchase_orders.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/api/routers/purchase_orders.py) (`GET/POST /purchase-orders`, `GET/PATCH /purchase-orders/{id}`, `POST /purchase-orders/{id}/order`, `POST /purchase-orders/{id}/receive`).
  - Registered `purchase_orders.router` in [`apps/api/app/main.py`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/api/app/main.py).
- **Frontend Liquid Glass Admin UI (`apps/web/app/admin/purchase-orders/page.tsx`)**:
  - Built `/admin/purchase-orders` with `ListViewTemplate`, `DataTable`, status tabs (`All`, `Draft`, `Ordered`, `Partially Received`, `Received`), and live vendor/PO search.
  - Added KPI summary cards: Total Orders, Total Purchasing Spend (₹), Awaiting Delivery, and Fully Received.
  - Added Create Draft PO Modal with dynamic line item row addition/removal, cost calculation, and UoM dropdown.
  - Added Authoritative Goods Receiving Drawer/Modal with per-line batch number, expiry date picker, destination warehouse selector, and real-time pending balance validation.
  - Added "Purchase Orders" navigation link under Wholesale Operations in [`apps/web/lib/nav.ts`](file:///c:/Users/khatr/Documents/GitHub/Wareflow/apps/web/lib/nav.ts).
- **Testing & Verification**:
  - Added 5 Pytest unit and integration tests in `apps/api/tests/test_purchase_orders.py` (82/82 Pytest tests passing across 16 test suites).
  - Added 4 Vitest frontend unit tests in `apps/web/lib/__tests__/purchase-orders.test.tsx` (63/63 Vitest tests passing across 16 test suites).
  - 0 Ruff lint warnings, 0 ESLint errors, 100% Prettier formatted.
  - Next.js production build (`next build`) succeeded with 24 routes.

### Decisions

- **Single Door Rule for Inbound Stock**: Receiving a Purchase Order (`POST /purchase-orders/{id}/receive`) is the sole path through which new inventory is introduced into stock batches and logged in the immutable `stock_movements(type=in)` ledger.
- **Base UoM Normalization at Receipt**: All received goods quantities are converted to base UoM via `UomService.convert_to_base_uom` before touching `StockBatch` or `StockMovement`, ensuring consistent stock valuations across warehouses.
- **Auto-Derived Order State**: PO status is derived directly from the ratio of line item received quantities to ordered quantities (`PARTIALLY_RECEIVED` vs `RECEIVED`).

### Key values for future steps

- PO List Endpoint: `GET /purchase-orders`
- PO Creation Endpoint: `POST /purchase-orders`
- PO Detail Endpoint: `GET /purchase-orders/{id}`
- PO Update Endpoint: `PATCH /purchase-orders/{id}`
- PO Order Transition Endpoint: `POST /purchase-orders/{id}/order`
- PO Goods Receiving Endpoint: `POST /purchase-orders/{id}/receive`
- Web Admin URL: `/admin/purchase-orders`

### Files Created

- `apps/api/app/schemas/purchase_orders.py`
- `apps/api/app/repositories/interfaces/purchase_order_repository.py`
- `apps/api/app/repositories/impl/purchase_order_repository.py`
- `apps/api/app/services/purchase_order_service.py`
- `apps/api/app/api/routers/purchase_orders.py`
- `apps/api/tests/test_purchase_orders.py`
- `apps/web/app/admin/purchase-orders/page.tsx`
- `apps/web/lib/__tests__/purchase-orders.test.tsx`

### Files Modified

- `apps/api/app/repositories/interfaces/stock_repository.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/api/app/services/stock_service.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

## [2026-08-18] — Step 7.3: Supplier Returns (RMA Out)

- **Phase:** Phase 7 — Suppliers & Purchase Orders
- **Step:** 7.3 — Supplier Returns (RMA Out)
- **Status:** Complete

### What was built

1. **Database Model & Migrations Enhancement (`apps/api/app/models/returns.py`)**:
   - Added `credit_note_ref: Mapped[str | None]` to `PurchaseReturn` model to capture supplier credit note identifiers upon settlement.
2. **Pydantic Schemas (`apps/api/app/schemas/purchase_returns.py`)**:
   - `PurchaseReturnItemCreateRequest`, `PurchaseReturnCreateRequest`, `PurchaseReturnStatusUpdateRequest`, `PurchaseReturnItemResponse`, `PurchaseReturnResponse`.
3. **Repository Interface & Implementations (`apps/api/app/repositories/`)**:
   - `PurchaseReturnRepositoryInterface` defining `create_return`, `update_status`, `get_by_id`, and `list_returns` (with supplier and status filters).
   - `SqlAlchemyPurchaseReturnRepository` with eager `joinedload` on items and unique result mapping.
   - `InMemoryPurchaseReturnRepository` for unit tests and testing environments.
   - Added `get_batch_by_id` and `record_stock_return` to `StockRepositoryInterface`, `SqlAlchemyStockRepository`, and `InMemoryStockRepository`.
4. **Domain Service (`apps/api/app/services/purchase_return_service.py`)**:
   - Immediate stock deduction on return request (`StockMovementTypeEnum.RETURN_OUT`) as physical goods leave the warehouse.
   - Guard against over-returns: validating returned batch quantities against current on-hand batch balances.
   - Strict status transition lifecycle enforcement: `requested` $\rightarrow$ `shipped` $\rightarrow$ `credited`.
   - Credit note validation: requires `credit_note_ref` string when transitioning to `credited`.
   - Structured audit logging via `AuditService`.
5. **FastAPI DI & Routing (`apps/api/app/core/di.py`, `apps/api/app/api/routers/purchase_returns.py`)**:
   - Factory `get_purchase_return_service` wired with clean dependency injection.
   - `POST /purchase-returns`, `GET /purchase-returns` (with `supplier_id` & `status` query filters), `GET /purchase-returns/{id}`, and `PATCH /purchase-returns/{id}/status`.
6. **Frontend Admin UI (`apps/web/app/admin/purchase-returns/page.tsx`)**:
   - Liquid Glass UI styled table with KPI cards (Total Returns, Units Returned, Shipped in Transit, Vendor Credited).
   - "Request Return (RMA)" modal with live batch stock lookup, pre-populating matching batches from selected purchase orders.
   - "Ship RMA" and "Credit Note" status transition dialogs.
   - Quick-action "Return to Supplier" buttons integrated on `/admin/purchase-orders` table row actions and detail modal footer with URL parameter prefill (`/admin/purchase-returns?po_id=...`).
   - Added `Supplier Returns` to navigation sidebar (`apps/web/lib/nav.ts`).
7. **Testing & Quality Assurance**:
   - Comprehensive backend test suite in `apps/api/tests/test_purchase_returns.py` (5 tests covering creation, stock movement validation, over-return bounds, status state machine, SQLite DB persistence, and FastAPI TestClient).
   - Frontend Vitest suite in `apps/web/lib/__tests__/purchase-returns.test.tsx` (5 tests covering KPI cards, search, status filters, RMA creation form, and status transition).
   - Pytest passed: 87 / 87 tests passing.
   - Vitest passed: 68 / 68 tests across 17 test suites passing.
   - Ruff linting and Next.js production build (`next build`) passing with 25 routes.

### SOLID Principles Applied

- **Single Responsibility Principle (SRP):** `PurchaseReturnService` strictly manages return lifecycles and stock reduction contracts; stock ledger updates delegated to `StockRepositoryInterface`.
- **Open/Closed Principle (OCP):** Lifecycle state machines and filtering are structured cleanly without modifying existing purchase order or inventory movement logic.
- **Liskov Substitution Principle (LSP):** `InMemoryPurchaseReturnRepository` and `SqlAlchemyPurchaseReturnRepository` completely satisfy `PurchaseReturnRepositoryInterface`.
- **Interface Segregation Principle (ISP):** Segregated `PurchaseReturnRepositoryInterface` and `StockRepositoryInterface` methods with tailored, role-specific operations.
- **Dependency Inversion Principle (DIP):** `PurchaseReturnService` and router endpoints depend exclusively on repository interfaces injected via `di.py`.

### Key values for future steps

- Return List Endpoint: `GET /purchase-returns`
- Return Creation Endpoint: `POST /purchase-returns`
- Return Status Transition Endpoint: `PATCH /purchase-returns/{id}/status`
- Web Admin URL: `/admin/purchase-returns`

### Files Created

- `apps/api/app/schemas/purchase_returns.py`
- `apps/api/app/repositories/interfaces/purchase_return_repository.py`
- `apps/api/app/repositories/impl/purchase_return_repository.py`
- `apps/api/app/services/purchase_return_service.py`
- `apps/api/app/api/routers/purchase_returns.py`
- `apps/api/tests/test_purchase_returns.py`
- `apps/web/app/admin/purchase-returns/page.tsx`
- `apps/web/lib/__tests__/purchase-returns.test.tsx`

### Files Modified

- `apps/api/app/models/returns.py`
- `apps/api/app/repositories/interfaces/stock_repository.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/api/app/repositories/impl/purchase_order_repository.py`
- `apps/api/app/repositories/impl/supplier_repository.py`
- `apps/api/app/repositories/impl/product_repository.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/app/admin/purchase-orders/page.tsx`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

### Step 7.4 — FSSAI License Compliance Tracking

**Timestamp:** 2026-08-18T19:20:00Z
**Status:** COMPLETE

### What was done

1. **Domain Schemas & Models (`apps/api/app/schemas/business_settings.py`, `apps/api/app/schemas/alerts.py`)**:
   - `BusinessSettingsResponse`, `BusinessSettingsUpdate`, and `FssaiComplianceStatusResponse` schemas with automatic days-to-expiry calculation and status enum (`valid`, `expiring_soon`, `expired`, `missing`).
   - `AlertItemResponse` and `AlertEngineSummaryResponse` schemas supporting tiered severity levels (`critical`, `warning`, `info`), channels (`in_app`, `whatsapp`, `email`), and escalation flags.
2. **Business Settings Repository Protocol (DIP) & Implementations (`apps/api/app/repositories/interfaces/business_settings_repository.py`, `apps/api/app/repositories/impl/business_settings_repository.py`)**:
   - `BusinessSettingsRepositoryInterface` defining `get_settings()` and `upsert_settings()`.
   - `SqlAlchemyBusinessSettingsRepository` utilizing PostgreSQL `business_settings` table.
   - `InMemoryBusinessSettingsRepository` enabling fast, zero-DB mock isolation for tests.
3. **Domain Services (`apps/api/app/services/business_settings_service.py`, `apps/api/app/services/alert_engine_service.py`)**:
   - `BusinessSettingsService`: Single responsibility for business legal profile, FSSAI compliance calculation, and audit trail logging.
   - `AlertEngineService` & `ExpiringLicenseRule` (OCP): Pluggable alert evaluation strategy pattern calculating 30-day early warnings, 7-day escalated alerts, and expired status for both distributor and suppliers.
4. **FastAPI Endpoints & DI (`apps/api/app/core/di.py`, `apps/api/app/api/routers/business_settings.py`, `apps/api/app/api/routers/alerts.py`, `apps/api/app/main.py`)**:
   - Dependency injection factories `get_business_settings_service` and `get_alert_engine_service`.
   - `GET /settings/business`: Fetches business settings + computed FSSAI status and days remaining.
   - `PUT /settings/business`: Updates legal name, GSTIN, FSSAI license, address, and contact details with `settings:manage` permission guard and audit logging.
   - `GET /alerts`: Returns evaluated alerts across the organization.
   - `GET /alerts/summary`: Aggregate counts of critical, warning, and total active compliance alerts.
5. **Frontend Business Settings & Supplier Badges (`apps/web/app/admin/settings/business/page.tsx`, `apps/web/app/admin/suppliers/page.tsx`)**:
   - Liquid Glass UI for Distributor Profile & FSSAI Compliance management at `/admin/settings/business` with real-time status banner.
   - Enhanced Supplier table with FSSAI expiry status badges (`Valid`, `Expiring Soon`, `Expired`, `No FSSAI`) and days remaining counters matching stock status badge visual language.
6. **PO Creation Guard & Soft Confirmation Dialog (`apps/web/app/admin/purchase-orders/page.tsx`)**:
   - Supplier dropdown with FSSAI expiry checks.
   - In-form warning banner when an expired supplier is selected.
   - Hard confirmation modal requiring explicit acknowledgment of regulatory risk before placing a Purchase Order with an expired supplier.
7. **Comprehensive Test Suite**:
   - Backend `apps/api/tests/test_fssai_compliance.py`: 5 tests covering business settings CRUD, 30-day warning triggers, 7-day escalation, expired supplier detection, OCP alert extensibility, and FastAPI TestClient endpoints.
   - Frontend `apps/web/lib/__tests__/fssai-compliance.test.tsx`: 14 unit tests covering `computeFssaiStatus`, `getFssaiBannerConfig`, and PO compliance gates.
   - Full suite verification: 92/92 Pytest passed, 82/82 Vitest passed, ESLint passing with 0 errors/0 warnings, and Next.js build succeeding with 26 static routes.

### SOLID Principles Applied

- **Single Responsibility Principle (SRP):** `BusinessSettingsService` manages business profile and status calculation; `AlertEngineService` orchestrates alert strategies; `ExpiringLicenseRule` encapsulates license expiry logic.
- **Open/Closed Principle (OCP):** Alert engine consumes `AlertRule` strategies; new alert types (e.g. low stock, payment overdue) can be added without modifying `AlertEngineService`.
- **Liskov Substitution Principle (LSP):** `InMemoryBusinessSettingsRepository` and `SqlAlchemyBusinessSettingsRepository` strictly honor `BusinessSettingsRepositoryInterface`.
- **Interface Segregation Principle (ISP):** Small, focused interfaces for `BusinessSettingsRepositoryInterface` and `AlertRule`.
- **Dependency Inversion Principle (DIP):** Routers and services depend on repository interfaces injected via `di.py`.

### Key values for future steps

- Business Settings API: `GET /settings/business`, `PUT /settings/business`
- Alerts API: `GET /alerts`, `GET /alerts/summary`
- Web Route: `/admin/settings/business`
- Alert Evaluation Rules: Pluggable into `AlertEngineService`

### Files Created

- `apps/api/app/schemas/business_settings.py`
- `apps/api/app/schemas/alerts.py`
- `apps/api/app/repositories/interfaces/business_settings_repository.py`
- `apps/api/app/repositories/impl/business_settings_repository.py`
- `apps/api/app/services/business_settings_service.py`
- `apps/api/app/services/alert_engine_service.py`
- `apps/api/app/api/routers/business_settings.py`
- `apps/api/app/api/routers/alerts.py`
- `apps/api/tests/test_fssai_compliance.py`
- `apps/web/app/admin/settings/business/page.tsx`
- `apps/web/lib/__tests__/fssai-compliance.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/app/admin/suppliers/page.tsx`
- `apps/web/app/admin/purchase-orders/page.tsx`
- `memory.md`
- `codebase_audit.md`

---

## Step 8.1 — Retailer CRUD & Bulk Pricing Tiers
**Timestamp:** 2026-08-18T19:35:00Z
**Status:** COMPLETE

### What was done

1. **Retailer Domain Schemas & Repository Protocol (DIP) (`apps/api/app/schemas/retailers.py`, `apps/api/app/repositories/interfaces/retailer_repository.py`, `apps/api/app/repositories/impl/retailer_repository.py`)**:
   - Extended `RetailerResponse`, `RetailerCreateRequest`, and `RetailerUpdateRequest` with `pricing_tier` enum (`standard`, `silver`, `gold`), address, GSTIN, credit limits, balances, and computed `available_credit`.
   - Updated `RetailerRepository` protocol with full CRUD operations (`get_by_id`, `get_by_name`, `list_all`, `create`, `update`, `update_credit_limit`).
   - Implemented `SqlAlchemyRetailerRepository` and fast in-memory mock `InMemoryRetailerRepository`.
2. **Pluggable Pricing Strategy Engine (Open/Closed Principle) (`apps/api/app/services/pricing_strategy.py`)**:
   - Defined abstract `PricingStrategy` interface specifying `calculate_unit_price` and `calculate_line`.
   - Built concrete strategies:
     - `StandardPricingStrategy`: 0% discount (base wholesale price).
     - `SilverPricingStrategy`: 5% discount on bulk line totals.
     - `GoldPricingStrategy`: 10% discount on bulk line totals.
     - `TieredDiscountPricingStrategy`: Volume-tiered quantity thresholds.
   - Built `PricingEngineService` strategy registry enabling zero-modification extension of custom tiers (e.g. Platinum VIP).
3. **Retailer Domain Service (`apps/api/app/services/retailer_service.py`)**:
   - `RetailerService` managing retailer lifecycle, duplicate name prevention, pricing calculations, and automated audit logging for creations, updates, and credit limit alterations.
4. **FastAPI Endpoints (`apps/api/app/api/routers/retailers.py`, `apps/api/app/core/di.py`)**:
   - `GET /retailers` (pagination + search query + active filter).
   - `POST /retailers` (retailer registration with tier assignment).
   - `GET /retailers/{id}` (fetch single retailer profile).
   - `PATCH /retailers/{id}` (profile/tier updates).
   - `PATCH /retailers/{id}/credit-limit` (authorized credit updates with audit logging).
5. **Frontend Web UI (`apps/web/app/admin/retailers/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Liquid Glass UI for `/admin/retailers` with KPI metric cards (Total Retailers, Active Accounts, Gold & Silver Tiers, Total Credit Extended).
   - Responsive `DataTable` with tier badges, contact indicators, credit availability breakdown, and active status indicators.
   - Modal create/edit form with real-time tier selector and credit limit inputs.
   - Added `Retailers & B2B` to navigation sidebar.
6. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_retailers.py` (11 tests covering pricing strategies, gold vs standard price differentiation proof, OCP platinum tier extension proof, repository CRUD, service validations, and API HTTP lifecycle).
   - Frontend `apps/web/lib/__tests__/retailers.test.tsx` (4 tests covering KPI cards, search filtering, status tab filtering, and modal registration).
   - 103/103 Pytest backend tests passing.
   - 86/86 Vitest frontend tests passing.
   - 0 errors/0 warnings on Ruff and ESLint; Next.js build succeeding with 27 static routes.

### Decisions

- **Open/Closed Pricing Engine**: `PricingStrategy` pattern decouples discount calculation from order and checkout services. Adding new pricing schemes requires writing one new `PricingStrategy` subclass and registering it, requiring zero changes to order processing logic.
- **Credit Line Visibility**: Track both `credit_limit` and `credit_balance` with computed `available_credit` to safeguard against retailer over-extension during subsequent sales order dispatch.

### Key values for future steps

- Retailers API: `GET /retailers`, `POST /retailers`, `GET /retailers/{id}`, `PATCH /retailers/{id}`
- Pricing Engine: `PricingEngineService` (injectable into future `SalesOrderService`)
- Web Route: `/admin/retailers`
- Pricing Tiers: `standard` (0%), `silver` (5%), `gold` (10%)

### Files Created

- `apps/api/app/services/pricing_strategy.py`
- `apps/api/tests/test_retailers.py`
- `apps/web/app/admin/retailers/page.tsx`
- `apps/web/lib/__tests__/retailers.test.tsx`

### Files Modified

- `apps/api/app/schemas/retailers.py`
- `apps/api/app/repositories/interfaces/retailer_repository.py`
- `apps/api/app/repositories/impl/retailer_repository.py`
- `apps/api/app/services/retailer_service.py`
- `apps/api/app/api/routers/retailers.py`
- `apps/api/app/core/di.py`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

## Step 8.2 — Sales Orders, Stock Deduction & Fulfillment

**Timestamp:** 2026-08-18T15:05:00Z
**Status:** COMPLETE

### What was done

1. **Sales Order Schemas & Data Transfer Objects (`apps/api/app/schemas/sales_orders.py`)**:
   - Built Pydantic V2 schemas: `SalesOrderItemCreateRequest`, `SalesOrderCreateRequest`, `SalesOrderStatusUpdateRequest`, `SalesOrderItemResponse`, `SalesOrderResponse`, and `SalesOrderListResponse`.
2. **FIFO-by-Expiry Stock Deduction & Compensating Adjustment Restoration (`apps/api/app/repositories/interfaces/stock_repository.py`, `apps/api/app/repositories/impl/stock_repository.py`)**:
   - Added `deduct_stock_fifo` and `restore_sales_order_stock` to `StockRepositoryInterface`.
   - In `SqlAlchemyStockRepository` and `InMemoryStockRepository`, implemented oldest-expiry-first (FIFO) allocation (`expiry_date ASC nulls last, received_at ASC`) across available batches with atomic `StockMovement(type=out, reference_type="sales_order")` generation.
   - Implemented `restore_sales_order_stock` for cancelling confirmed orders, restoring deducted quantities to their exact source batches with compensating `StockMovement(type=adjustment, reference_type="sales_order_cancellation")` rows and credit balance refunds.
3. **Sales Order Repositories (`apps/api/app/repositories/interfaces/sales_order_repository.py`, `apps/api/app/repositories/impl/sales_order_repository.py`)**:
   - Built `SalesOrderRepositoryInterface` defining `get_by_id`, `get_by_so_number`, `list_all`, `create`, `update`, and `generate_next_so_number`.
   - Implemented `SqlAlchemySalesOrderRepository` and `InMemorySalesOrderRepository`.
4. **Sales Order Domain Service & Credit Limit Gate (`apps/api/app/services/sales_order_service.py`)**:
   - `SalesOrderService` enforcing transactional domain logic:
     - **Credit Gate First**: Checks `retailer.credit_balance + order_total <= retailer.credit_limit` (0 limit = cash-only, always allowed) **before** inspecting or touching inventory batches. Shortfalls return descriptive 422 HTTP exceptions naming the exact shortfall.
     - **FIFO Stock Deduction Second**: Confirms order atomically consuming batches oldest-expiry-first. Insufficient stock raises 422 with shortfall details and aborts the entire transaction.
     - **Fulfillment State Machine**: `draft` -> `confirmed` (stock deducted) -> `packed` -> `shipped` -> `delivered`, plus `cancelled`. Cancelling confirmed orders triggers compensating inventory adjustments and credit balance refunds.
     - **Audit Logging**: Logs structured audit actions for order creation, confirmation, and status changes.
5. **FastAPI Endpoints (`apps/api/app/api/routers/sales_orders.py`, `apps/api/app/core/di.py`, `apps/api/app/main.py`)**:
   - `GET /sales-orders` (filterable by status, buyer type, retailer ID, search).
   - `POST /sales-orders` (draft order creation with tier-adjusted pricing).
   - `GET /sales-orders/{id}` (order details with line items).
   - `POST /sales-orders/{id}/confirm` (credit check + atomic FIFO stock deduction).
   - `PATCH /sales-orders/{id}/status` (fulfillment state advancement & cancellation).
6. **Frontend Web UI (`apps/web/app/admin/sales-orders/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Liquid Glass UI for `/admin/sales-orders` with KPI metric cards (Total Orders, Draft Orders, In Fulfillment, Total Revenue).
   - Filterable `DataTable` with status badges, retailer tier pills, and credit warning indicators.
   - Interactive Create Order modal with live tier-discount calculation and credit availability warning indicator.
   - Comprehensive Order Details view with line items table, batch allocation context, and status progression action buttons (`Confirm Order (Deduct FIFO)`, `Mark Packed`, `Dispatch / Ship`, `Mark Delivered`, `Cancel Order`).
   - Wired `Orders & Dispatch` navigation in Wholesale Operations sidebar.
7. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_sales_orders.py` (7 tests covering credit limit check before stock inspection, cash-only accounts, FIFO oldest-expiry-first stock consumption across multiple batches, compensating stock restoration on cancellation, invalid state transition rejections, and FastAPI endpoint HTTP lifecycle).
   - Frontend `apps/web/lib/__tests__/sales-orders.test.tsx` (5 tests covering KPI cards, search filtering, status tab filtering, modal draft creation, and order confirmation).
   - 110/110 Pytest backend tests passing.
   - 91/91 Vitest frontend tests passing across 20 test files.
   - 0 errors/0 warnings on Ruff and ESLint; Next.js build succeeding with 28 static and dynamic routes.

### Decisions

- **Credit Limit Gate Before Stock Check**: Credit verification strictly precedes inventory allocation. If a retailer's credit balance exceeds credit limit, the transaction aborts with zero inventory batches altered.
- **Compensating Adjustments for Cancellation**: Cancelling a confirmed order creates `StockMovement(type=adjustment)` referencing the original sales order rather than deleting movements, ensuring an immutable audit trail.
- **Oldest-Expiry-First (FIFO)**: Sorting by `expiry_date ASC nulls last, received_at ASC` guarantees perishable inventory is dispatched before newer stock, minimizing spoilage.

### Key values for future steps

- Sales Orders API: `GET /sales-orders`, `POST /sales-orders`, `GET /sales-orders/{id}`, `POST /sales-orders/{id}/confirm`, `PATCH /sales-orders/{id}/status`
- Web Route: `/admin/sales-orders`
- Status Workflow: `draft` -> `confirmed` -> `packed` -> `shipped` -> `delivered` (or `cancelled`)

### Files Created

- `apps/api/app/schemas/sales_orders.py`
- `apps/api/app/repositories/interfaces/sales_order_repository.py`
- `apps/api/app/repositories/impl/sales_order_repository.py`
- `apps/api/app/services/sales_order_service.py`
- `apps/api/app/api/routers/sales_orders.py`
- `apps/api/tests/test_sales_orders.py`
- `apps/web/app/admin/sales-orders/page.tsx`
- `apps/web/lib/__tests__/sales-orders.test.tsx`

### Files Modified

- `apps/api/app/repositories/interfaces/stock_repository.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/api/app/services/pricing_strategy.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

## Step 8.3 — Retailer Returns (RMA In)

**Timestamp:** 2026-08-18T15:20:00Z
**Status:** COMPLETE

### What was done

1. **Schemas & DTOs (`apps/api/app/schemas/sales_returns.py`)**:
   - Implemented `SalesReturnItemCreateRequest`, `SalesReturnCreateRequest`, `SalesReturnStatusUpdateRequest`, `SalesReturnItemResponse`, `SalesReturnResponse`, and `SalesReturnListResponse`.
   - Included product metadata, line pricing, condition tags (`resellable` | `damaged`), and total credit adjustment values.
2. **Stock Repository Inbound RMA Extension (`StockRepositoryInterface` & `SqlAlchemyStockRepository` / `InMemoryStockRepository`)**:
   - Added `record_sales_return_stock(product_id, quantity, batch_id, warehouse_id, reference_id, created_by)` to atomically top up `StockBatch.quantity` and insert immutable `StockMovement(type=return_in, reference_type="sales_return")`.
3. **Sales Return Repositories (`SalesReturnRepositoryInterface` & `SqlAlchemySalesReturnRepository` / `InMemorySalesReturnRepository`)**:
   - Implemented protocol interface and implementations with eager-loading queries and cumulative returned quantities calculation (`get_returned_quantities_by_order`).
4. **Sales Return Domain Service (`SalesReturnService`)**:
   - **Sales Order Quantity Gate**: Validates that order exists and is in a returnable fulfillment status (`confirmed`, `packed`, `shipped`, `delivered`), and verifies requested return quantity does not exceed (`sold_qty - previously_returned_qty`).
   - **Condition-Based Restocking Engine**: Items marked `resellable` increment sellable batch stock and insert `RETURN_IN` ledger movements. Items marked `damaged` are logged in return records for loss tracking and credit calculation, but strictly do NOT increment sellable stock.
   - **Credit Adjustment Intent**: Pre-calculates line refund amounts based on original sales order unit pricing.
   - **State Machine & Audit Logging**: `requested` -> `approved` (restocked) / `rejected`. Emits audit logs on creation, approval, and rejection.
5. **FastAPI Endpoints (`apps/api/app/api/routers/sales_returns.py`)**:
   - `GET /sales-returns`: Filterable by retailer, sales order ID, status, and search query.
   - `POST /sales-returns`: Request new RMA return.
   - `GET /sales-returns/{id}`: Detailed RMA return record.
   - `PATCH /sales-returns/{id}/approve`: Approves return and restocks resellable inventory.
   - `PATCH /sales-returns/{id}/reject`: Rejects return request.
   - Registered router in `main.py` and DI factories in `di.py`.
6. **Frontend Liquid Glass View (`apps/web/app/admin/sales-returns/page.tsx`)**:
   - Built Liquid Glass layout with KPI cards: Total RMA Returns, Pending Approvals, Resellable Restocked Units, Damaged Write-offs.
   - Filter pills (`All`, `Requested`, `Approved`, `Rejected`), `DataTable` with status badges and condition pills.
   - Request RMA Return modal with sales order picker and line items condition assessment.
   - Return Details modal with line items table, credit adjustment banner, and status actions (`Approve (Restock Resellable)`, `Reject Return`).
   - Added direct "Request RMA Return" action button in `/admin/sales-orders` detail modal and updated `nav.ts` `Returns & RMA` link to `/admin/sales-returns`.
7. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_sales_returns.py` (7 tests covering sold quantity caps, cumulative return validation, resellable batch replenishment, damaged write-offs excluding sellable stock, rejection, and full FastAPI router integration).
   - Frontend `apps/web/lib/__tests__/sales-returns.test.tsx` (5 tests covering KPI cards, search filtering, status tab filtering, modal creation, and approve/reject workflows).
   - 117/117 Pytest backend tests passing (100% green).
   - 96/96 Vitest frontend tests passing across 21 test files (100% green).
   - 0 errors / 0 warnings on Ruff and ESLint; Next.js build succeeding with 29 static and dynamic routes.

### Decisions

- **Condition-Based Restocking Rule ("Not Every Return is Stock Back")**: Resellable stock returns to inventory batches via immutable `StockMovement(type=return_in)` ledger entries. Damaged stock is stored in `sales_return_items` for loss tracking and credit ledger adjustments, but is strictly excluded from sellable inventory batches to prevent corrupted inventory dispatch.
- **Original Quantity Sold Cap**: A retailer return request cannot exceed the fulfilled quantity for any line item on that sales order, factoring in all active previous return requests on the order.
- **Credit Adjustment Intent Stored**: Calculates the financial refund value upfront using the sales order line item's negotiated wholesale price, preparing seamless handoff for Phase 9 Billing & Invoicing credit notes.

### Key values for future steps

- Sales Returns API: `GET /sales-returns`, `POST /sales-returns`, `GET /sales-returns/{id}`, `PATCH /sales-returns/{id}/approve`, `PATCH /sales-returns/{id}/reject`
- Web Route: `/admin/sales-returns`
- Status Workflow: `requested` -> `approved` (restocked) / `rejected`
- Condition Enum: `resellable` (restocks inventory), `damaged` (write-off / loss tracking only)

### Files Created

- `apps/api/app/schemas/sales_returns.py`
- `apps/api/app/repositories/interfaces/sales_return_repository.py`
- `apps/api/app/repositories/impl/sales_return_repository.py`
- `apps/api/app/services/sales_return_service.py`
- `apps/api/app/api/routers/sales_returns.py`
- `apps/api/tests/test_sales_returns.py`
- `apps/web/app/admin/sales-returns/page.tsx`
- `apps/web/lib/__tests__/sales-returns.test.tsx`

### Files Modified

- `apps/api/app/repositories/interfaces/stock_repository.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/app/admin/sales-orders/page.tsx`
- `apps/web/lib/nav.ts`
- `memory.md`
- `codebase_audit.md`

---

## Step 8.4 — Walk-In / Direct End-Customer Management

**Timestamp:** 2026-08-18T15:48:00Z
**Status:** COMPLETE

### What was done

1. **Direct Customer Schemas (`apps/api/app/schemas/customers.py`)**:
   - Built Pydantic V2 schemas: `CustomerCreateRequest`, `CustomerUpdateRequest`, `CustomerResponse`, and `CustomerListResponse`.
   - Deliberately simplified entity without credit limits or pricing tiers (standard pricing only).
2. **Customer Repositories (`apps/api/app/repositories/interfaces/customer_repository.py`, `apps/api/app/repositories/impl/customer_repository.py`)**:
   - Built `CustomerRepositoryInterface` protocol defining `get_by_id`, `get_by_email`, `get_by_phone`, `list_all`, `create`, `update`, and `delete`.
   - Implemented `SqlAlchemyCustomerRepository` with case-insensitive search and `InMemoryCustomerRepository` for unit tests.
3. **Customer Domain Service & Active Orders Deletion Guard (`apps/api/app/services/customer_service.py`)**:
   - `CustomerService` providing full CRUD operations, email/phone format validation, and structured audit logs via `AuditRepository.create_log()`.
   - Built relational integrity guard: `delete_customer` checks associated sales orders and raises `422 Unprocessable Content` if order history exists.
4. **Shared Sales Order Pipeline & Credit Check Bypass (`apps/api/app/services/sales_order_service.py`)**:
   - Injected `CustomerRepositoryInterface` into `SalesOrderService`.
   - Updated `_resolve_retailer` to validate customer existence when `buyer_type == BuyerTypeEnum.CUSTOMER`.
   - `_check_and_reserve_credit` immediately no-ops for `buyer_type == BuyerTypeEnum.CUSTOMER` (direct buyers are assumed cash/UPI immediate settlement).
   - Oldest-expiry FIFO batch deduction (`_deduct_stock_fifo`) and cancellation compensating adjustments work identically to retailer orders.
   - Populated `customer_name` dynamically in `SalesOrderResponse`.
5. **FastAPI Endpoints (`apps/api/app/api/routers/customers.py`, `apps/api/app/core/di.py`, `apps/api/app/main.py`)**:
   - Registered endpoints: `GET /customers`, `POST /customers`, `GET /customers/{id}`, `PATCH /customers/{id}`, and `DELETE /customers/{id}`.
   - Bound DI providers in `di.py` and registered `/customers` router in `main.py`.
6. **Frontend Liquid Glass View (`apps/web/app/admin/customers/page.tsx`, `apps/web/app/admin/sales-orders/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Created `/admin/customers` with 4 KPI cards (Total Customers, Active Buyers, Direct Orders Placed, Direct Sales Volume).
   - Filterable `DataTable` with contact details, order count, total spend, and action buttons.
   - Registration and Edit modals with form validation.
   - Customer Details modal with order telemetry and quick edit shortcut.
   - Updated `/admin/sales-orders` Create Order modal with `Buyer Type` toggle (`Wholesale Retailer` vs `Direct Customer`), dynamic retailer/customer dropdown pickers, and informational standard pricing badge.
   - Added `Direct Customers` link in Wholesale Operations sidebar navigation.
7. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_customers.py` (6 tests covering CRUD round-trip, credit-check skipping with FIFO stock deduction, customer order cancellation inventory restoration, invalid customer rejection, open orders deletion guard, and HTTP API endpoints).
   - Frontend `apps/web/lib/__tests__/customers.test.tsx` (4 tests covering KPI rendering, search query filtering, customer registration, and edit profile updates).
   - 123/123 Pytest backend tests passing (100% green).
   - 100/100 Vitest frontend tests passing across 22 test files (100% green).
   - 0 errors / 0 warnings on Ruff and ESLint; Next.js build succeeding with 30 static and dynamic routes.

### Decisions

- **Shared Sales Order Pipeline for All Buyers**: Direct end-customers reuse the exact same sales order and FIFO inventory fulfillment engine as B2B retailers via the `buyer_type` discriminator (`buyer_type=customer`), eliminating duplicate order processing logic.
- **Credit Verification Bypass for Walk-Ins**: Direct walk-in buyers are assumed immediate payment (cash/UPI/POS), so `SalesOrderService._check_and_reserve_credit` and credit refund logic cleanly no-op while preserving FIFO batch deductions.
- **Active Orders Deletion Guard**: A customer record with existing sales orders cannot be deleted, preserving relational integrity and accounting traceability.

### Key values for future steps

- Customers API: `GET /customers`, `POST /customers`, `GET /customers/{id}`, `PATCH /customers/{id}`, `DELETE /customers/{id}`
- Web Route: `/admin/customers`
- Order Integration: `SalesOrderCreateRequest(buyer_type="customer", customer_id="...")`

### Files Created

- `apps/api/app/schemas/customers.py`
- `apps/api/app/repositories/interfaces/customer_repository.py`
- `apps/api/app/repositories/impl/customer_repository.py`
- `apps/api/app/services/customer_service.py`
- `apps/api/app/api/routers/customers.py`
- `apps/api/tests/test_customers.py`
- `apps/web/app/admin/customers/page.tsx`
- `apps/web/lib/__tests__/customers.test.tsx`

### Files Modified

- `apps/api/app/services/sales_order_service.py`
- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/web/app/admin/sales-orders/page.tsx`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`
- `memory.md`

---

## Step 9.1 — Movement Ledger UI & Manual Adjustments

**Timestamp:** 2026-08-18T16:00:00Z
**Status:** COMPLETE

### What was done

1. **Stock Adjustment & Movement Schemas (`apps/api/app/schemas/stock_adjustments.py`)**:
   - Created `AdjustmentReasonEnum` (`damage`, `loss`, `recount`, `other`).
   - Created `StockAdjustmentCreateRequest` (`product_id`, `warehouse_id`, `batch_id`, `delta`, `reason`, `notes`).
   - Created `StockAdjustmentResponse` with previous and updated batch quantities.
   - Created `StockMovementListItemResponse` and `StockMovementListResponse` with human-readable labels and pagination metadata.
2. **Stock Repositories (`apps/api/app/repositories/interfaces/stock_repository.py`, `apps/api/app/repositories/impl/stock_repository.py`)**:
   - Added `record_stock_adjustment` and `list_movements` methods to `StockRepositoryInterface`.
   - Implemented `SqlAlchemyStockRepository` and `InMemoryStockRepository` with non-negative batch quantity validation, atomic `stock_movements(type=adjustment)` persistence, and multi-filter ledger queries with contextual labels.
3. **Domain Service & Permission Enforcement (`apps/api/app/services/stock_service.py`)**:
   - Extended `StockService` with `adjust_stock` and `list_movements`.
   - Recount permission gate: `reason=recount` strictly requires `stock.recount` / `stock:recount` permission or `Owner` role (raises `403 Forbidden` if unauthorized).
   - Negative batch balance guard: Raises `422 Unprocessable Content` if `batch.quantity + delta < 0`.
   - Zero-delta guard: Raises `400 Bad Request` if `delta == 0`.
   - Emits structured audit log to `AdminAuditLog` via `AuditRepository.create_log()`.
   - Formatted human labels for all movement references (`purchase_order`, `sales_order`, `sales_order_cancellation`, `purchase_return`, `sales_return`, `manual_adjustment`).
4. **FastAPI Endpoints (`apps/api/app/api/routers/stock.py`, `apps/api/app/core/di.py`)**:
   - `POST /stock/adjustments`: Creates manual stock adjustment with validation and audit logging.
   - `GET /stock/movements`: Returns paginated, filterable movement ledger with human labels.
   - Updated `get_stock_service` dependency factory in `di.py` to inject `AuditRepository`.
5. **Frontend Liquid Glass Movement Ledger & Adjustment Pages (`apps/web/app/admin/stock/ledger/page.tsx`, `apps/web/app/admin/stock/adjust/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Built `/admin/stock/ledger` with 4 KPI cards (Movement Records, Total Inbound, Total Outbound, Net Adjustments Variance), type filter pills (`All`, `Inbound Receipts`, `Outbound Dispatches`, `Adjustments`, `Returns RMA In`, `Supplier Returns`), search bar, and `DataTable` with colored deltas and activity context.
   - Built `/admin/stock/adjust` with product, warehouse, and batch selectors, real-time projected batch balance preview, reason picker with disabled recount locked badge for non-owners/managers, notes textarea, and confirmation state.
   - Added `Movement Ledger` and `Stock Adjustments` navigation links in `nav.ts`.
6. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_stock_adjustments.py` (5 tests covering damage/loss deductions, negative batch rejection 422, recount permission guard 403 vs 200, human label synthesis across PO/SO/RMA/adjustment, and HTTP API endpoints).
   - Frontend `apps/web/lib/__tests__/stock-movements.test.tsx` (3 tests covering KPI rendering, search filtering, batch selection, and manual adjustment submission).
   - Full test suites: 128/128 Pytest tests passing (100% green); 103/103 Vitest tests passing across 23 test files (100% green).
   - Zero lint errors/warnings on Ruff and ESLint; Next.js production build cleanly compiled with 32 routes.

### Decisions

- **Single Legitimate Manual Write Path**: Manual adjustment with mandatory reason (`damage`, `loss`, `recount`, `other`) is the sole direct stock modification path, preserving the immutable append-only ledger invariant.
- **Recount Permission Gate**: The `recount` adjustment reason requires the explicit `stock.recount` permission code or `Owner` role, preventing unauthorized floor staff from adding arbitrary inventory balances.
- **Human Label Synthesis**: Enriched ledger items with human context (`PO #... (Goods Receipt)`, `SO #... (Fulfillment Dispatch)`, `Adjustment: Damage (...)`) directly in the API layer, giving complete transparency without requiring multiple N+1 client joins.

### Key values for future steps

- Adjustments API: `POST /stock/adjustments`
- Movements Ledger API: `GET /stock/movements`
- Web Routes: `/admin/stock/ledger`, `/admin/stock/adjust`
- Permission Code: `stock.recount` / `stock:recount`

### Files Created

- `apps/api/app/schemas/stock_adjustments.py`
- `apps/api/tests/test_stock_adjustments.py`
- `apps/web/app/admin/stock/ledger/page.tsx`
- `apps/web/app/admin/stock/adjust/page.tsx`
- `apps/web/lib/__tests__/stock-movements.test.tsx`

### Files Modified

- `apps/api/app/repositories/interfaces/stock_repository.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/api/app/repositories/impl/audit_repository.py`
- `apps/api/app/services/stock_service.py`
- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/stock.py`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`
- `memory.md`

---

## Step 9.2 — Inter-Warehouse Transfers

**Timestamp:** 2026-08-18T16:20:00Z
**Status:** COMPLETE

### What was done

1. **Transfer Schemas (`apps/api/app/schemas/stock_transfers.py`)**:
   - Built Pydantic V2 schemas: `StockTransferCreateRequest`, `StockTransferResponse`, `StockTransferListItemResponse`, and `StockTransferListResponse`.
2. **Transfer Repositories (`apps/api/app/repositories/interfaces/transfer_repository.py`, `apps/api/app/repositories/impl/transfer_repository.py`)**:
   - Created `TransferRepositoryInterface(Protocol)` defining `execute_transfer` and `list_transfers`.
   - Built `SqlAlchemyTransferRepository`:
     - Wraps source batch decrement, destination batch lookup/creation with matching `batch_no` and `expiry_date`, and paired `StockMovement(type=OUT, quantity=-qty)` at source and `StockMovement(type=IN, quantity=+qty)` at destination inside a single atomic database transaction.
     - On any exception or shortfall, automatically rolls back leaving zero half-applied changes.
   - Built `InMemoryTransferRepository` with rollback simulation for test suites.
3. **Transfer Domain Service (`apps/api/app/services/transfer_service.py`)**:
   - Built `TransferService` providing transfer orchestration, validation (positive quantity, distinct warehouses `400`, insufficient source stock `422`), structured audit logging via `AdminAuditLog` (`action="stock_transferred"`), and paginated historical query retrieval.
4. **FastAPI Endpoints & DI Wiring (`apps/api/app/api/routers/stock.py`, `apps/api/app/core/di.py`)**:
   - Registered endpoints: `POST /stock/transfers` (201 Created) and `GET /stock/transfers` (200 OK, paginated and filterable).
   - Wired `get_transfer_repository` and `get_transfer_service` in `di.py`.
5. **Frontend Liquid Glass View (`apps/web/app/admin/stock/transfer/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Built `/admin/stock/transfer` with product, source warehouse, batch, and destination warehouse selectors.
   - Built Dual-Warehouse Live On-Hand Impact Preview displaying current and projected balances at both source and destination facilities with real-time over-stock warning badges.
   - Added recent transfers history `DataTable` with route visualization (`From → To`).
   - Added `Warehouse Transfers` link in sidebar navigation.
6. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_stock_transfers.py` (5 tests covering insufficient source stock rejection 422, same-warehouse rejection 400, atomic paired quantities and movements, destination top-up, and HTTP endpoints).
   - Frontend `apps/web/lib/__tests__/stock-transfers.test.tsx` (2 tests covering form rendering, live preview updates, and transfer execution).
   - All 133 backend Pytest tests passing (100% green).
   - All 105 frontend Vitest tests passing across 24 test files (100% green).
   - 0 errors / 0 warnings on Ruff and ESLint; Next.js production build cleanly compiled with 33 routes.

### Decisions

- **Transfer-As-Atomic-Pair Rule**: Inter-warehouse transfer is strictly executed as a single atomic operation writing a paired `OUT` movement at source and `IN` movement at destination with matching `reference_type="warehouse_transfer"` and `reference_id=transfer_id`. Stock can never exist in an indeterminate or half-transferred state.
- **Batch Identity Preservation**: The destination warehouse batch preserves the source batch's `batch_no` and `expiry_date` (topping up existing batch if already present in destination, or creating a new batch entry if absent).
- **Dual Live Preview UI**: The frontend immediately computes and visualizes the projected inventory levels for both the source facility (reduction) and destination facility (replenishment) before the user commits the transfer.

### Key values for future steps

- Transfers API: `POST /stock/transfers`, `GET /stock/transfers`
- Web Route: `/admin/stock/transfer`
- Ledger Reference Type: `reference_type="warehouse_transfer"` with `reference_id="<transfer_id>:<notes>"`

### Files Created

- `apps/api/app/schemas/stock_transfers.py`
- `apps/api/app/repositories/interfaces/transfer_repository.py`
- `apps/api/app/repositories/impl/transfer_repository.py`
- `apps/api/app/services/transfer_service.py`
- `apps/api/tests/test_stock_transfers.py`
- `apps/web/app/admin/stock/transfer/page.tsx`
- `apps/web/lib/__tests__/stock-transfers.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/stock.py`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`
- `memory.md`

---

## Step 9.3 — Batch Recall & Traceability

**Timestamp:** 2026-08-18T16:30:00Z
**Status:** COMPLETE

### What was done

1. **Pydantic Schemas (`apps/api/app/schemas/recalls.py`)**:
   - Implemented `BatchRecallCreateRequest`, `BatchRecallResponse`, `BatchRecallListItemResponse`, `BatchRecallListResponse`, `BatchRecallNotifyResponse`, and `RecallAffectedOrderItemResponse`.
2. **Recall Repository Protocol & Implementation (`apps/api/app/repositories/interfaces/recall_repository.py`, `apps/api/app/repositories/impl/recall_repository.py`)**:
   - Defined `RecallRepositoryInterface(Protocol)` and implemented `SqlAlchemyRecallRepository` + `InMemoryRecallRepository`.
   - Automated order defect tracing: queries `StockMovement(type=OUT, reference_type="sales_order")` for the given `batch_id`, joining `SalesOrder`, `Retailer`, and `Customer` to accurately map every affected order and buyer.
   - Atomically populates `RecallAffectedOrder` rows.
   - Handled `mark_affected_orders_notified` (populates `notified_at` per order and sets `status = RecallStatusEnum.NOTIFYING`) and `resolve_recall` (sets `resolved_at` and `status = RecallStatusEnum.RESOLVED`).
3. **Unsellable Batch Isolation Guard (`apps/api/app/repositories/impl/stock_repository.py`)**:
   - `SqlAlchemyStockRepository.deduct_stock_fifo` and `InMemoryStockRepository.deduct_stock_fifo` immediately exclude any batch with an active recall (`status.in_(["initiated", "notifying"])`) from new sales order deductions.
   - Retains full batch history in the database without deletion.
4. **Recall Domain Service & DI (`apps/api/app/services/recall_service.py`, `apps/api/app/core/di.py`)**:
   - Created `RecallService` providing `initiate_recall`, `notify_affected_retailers`, `resolve_recall`, `get_recall_details`, and `list_recalls`.
   - Structured audit logging via `AuditRepository.create_log` (`action="batch_recall_initiated"`, `"batch_recall_notified"`, `"batch_recall_resolved"`).
   - Injected in `app.core.di`.
5. **FastAPI Endpoints (`apps/api/app/api/routers/stock.py`)**:
   - `POST /stock/recalls` (201 Created)
   - `GET /stock/recalls` (200 OK, paginated and filterable)
   - `GET /stock/recalls/{recall_id}` (200 OK)
   - `PATCH /stock/recalls/{recall_id}/notify` (200 OK)
   - `PATCH /stock/recalls/{recall_id}/resolve` (200 OK)
6. **Frontend Liquid Glass View (`apps/web/app/admin/stock/recalls/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Built `/admin/stock/recalls` with 4 KPI cards (Total Recalls, Active Quarantines, Affected Orders Traced, Retailers Alerted).
   - "Initiate Batch Recall" modal with product & batch pickers, severity selector (`Critical`, `Medium`, `Low`), and root cause reason.
   - Recalls `DataTable` with severity and status badges.
   - Recall Detail Drawer showing traced affected orders with buyer contact info, units supplied, notification status, "Broadcast Recall Alerts (WhatsApp + Email)" action, and "Mark as Resolved" action.
   - Added `Batch Recalls` link under Wholesale Operations in `nav.ts`.
7. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_recalls.py` (4 tests passing: exact 3-order tracing, unsellable stock exclusion without deletion, notification & resolution lifecycle, HTTP endpoints).
   - Frontend `apps/web/lib/__tests__/recalls.test.tsx` (3 tests passing: dashboard rendering, modal recall creation, alert broadcast).
   - Full test suites: 137 / 137 Pytest tests passing (100% green); 108 / 108 Vitest tests passing across 25 test suites (100% green).
   - 0 errors / 0 warnings on Ruff and ESLint; Next.js production build cleanly compiled with 34 routes.

### Decisions

- **Recall Traceability Method**: Traced via `stock_movements(type=out)` references, not a separate manually-maintained record. The immutable append-only ledger serves as the single source of truth for all outbound stock distribution.
- **Unsellable Stock Quarantine**: Recalled stock is flagged unsellable, never deleted — traceability requires the history to remain intact. Active recalled batches are dynamically filtered out of FIFO sales deductions.
- **Notification Engine Reuse**: Recall notifications reuse the existing notification engine / audit dispatch mechanism with zero new channel code.

### Key values for future steps

- Recalls API: `POST /stock/recalls`, `GET /stock/recalls`, `GET /stock/recalls/{id}`, `PATCH /stock/recalls/{id}/notify`, `PATCH /stock/recalls/{id}/resolve`
- Web Route: `/admin/stock/recalls`
- Recall Statuses: `initiated`, `notifying`, `resolved`
- Recall Severities: `low`, `medium`, `critical`

### Files Created

- `apps/api/app/schemas/recalls.py`
- `apps/api/app/repositories/interfaces/recall_repository.py`
- `apps/api/app/repositories/impl/recall_repository.py`
- `apps/api/app/services/recall_service.py`
- `apps/api/tests/test_recalls.py`
- `apps/web/app/admin/stock/recalls/page.tsx`
- `apps/web/lib/__tests__/recalls.test.tsx`

### Files Modified

- `apps/api/app/api/routers/stock.py`
- `apps/api/app/core/di.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`
- `memory.md`

## Step 10.1 — Invoice Generation (GST-ready)

**Timestamp:** 2026-08-18T16:58:00Z
**Status:** COMPLETE

### What was done

1. **Pydantic V2 Schemas (`apps/api/app/schemas/invoices.py`)**:
   - `InvoiceItemResponse`, `InvoiceResponse`, `InvoiceListItemResponse`, `InvoiceListResponse`.
   - Frozen snapshot representation of line items, HSN codes, GST rate breakdown, subtotal, tax amount, and grand total.
2. **Repository Layer & Dependency Inversion (`apps/api/app/repositories/interfaces/invoice_repository.py` & `apps/api/app/repositories/impl/invoice_repository.py`)**:
   - Defined `InvoiceRepositoryInterface` Protocol (`get_by_id`, `get_by_sales_order_id`, `get_next_invoice_number`, `create_invoice`, `list_invoices`).
   - Implemented `SqlAlchemyInvoiceRepository` with joined loads for line items and sales order metadata.
   - Implemented `InMemoryInvoiceRepository` for fast, hermetic zero-IO domain testing with sequential financial-year numbering regex parser.
3. **Domain Service (`apps/api/app/services/invoice_service.py`)**:
   - `generate_invoice_for_sales_order(sales_order_id, current_user)`:
     - **Status Guardrail**: Enforces order status must be `confirmed`, `packed`, `shipped`, or `delivered`. Rejects `draft` or `cancelled` orders with HTTP 422.
     - **Idempotency**: Checks `invoice_repo.get_by_sales_order_id(sales_order_id)`; if already generated, returns existing invoice immediately without duplicates.
     - **Frozen Snapshotting**: Snapshots each `sales_order_item` into `InvoiceItem` at confirmed pricing and snapshots catalog `product_name` and `hsn_code` to ensure immunity from future catalog mutations.
     - **GST Computation**: Calculates 18% default GST (or category-specific rate), item tax amounts, CGST/SGST breakdown, subtotal, and total amount.
     - **Audit Logging**: Emits `INVOICE_GENERATED` audit event to `AdminAuditLog`.
   - `get_invoice(invoice_id)`: Fetches frozen invoice by ID with full item details.
   - `list_invoices(...)`: Paginated and filterable listing by retailer ID, buyer type, status (`unpaid`, `partially_paid`, `paid`, `overdue`), and search queries.
4. **API Router & Dependency Injection (`apps/api/app/api/routers/invoices.py`, `apps/api/app/core/di.py`, `apps/api/app/main.py`)**:
   - `POST /sales-orders/{id}/invoice`: Permission-guarded (`orders:manage`) invoice generation.
   - `GET /invoices`: Permission-guarded (`orders:view` / `invoices:view`) filterable invoice list.
   - `GET /invoices/{id}`: Permission-guarded invoice detail retrieval.
   - Registered router with `/api/v1` prefix and OpenAPI tags `["Invoices & Billing"]`.
5. **Frontend Web UI (`apps/web/app/admin/invoices/page.tsx`, `apps/web/app/admin/sales-orders/page.tsx`, `apps/web/lib/nav.ts`)**:
   - Built `/admin/invoices` page with 4 KPI cards (Total Invoiced Value, Outstanding Unpaid, Collected Revenue, Active Invoices).
   - Invoices `DataTable` with status filtering tabs (`all`, `unpaid`, `paid`, `partially_paid`, `overdue`), search filter, and currency formatting.
   - **GST Tax Invoice Preview & Print Modal (`GlassModal`)**: Full compliant wholesale tax invoice layout including distributor credentials (GSTIN, FSSAI), buyer billing details, frozen line item matrix with HSN codes, and CGST/SGST tax breakdown with browser print/PDF export support.
   - Updated Sales Order detail modal with "Generate / View Invoice" button for confirmed/in-flight orders.
   - Added `GST Invoices` link in sidebar navigation under Wholesale Operations (`nav.ts`).
6. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_invoices.py` (5 tests passing: idempotency verification, frozen snapshotting against price hikes, gap-free financial-year sequence e.g. `INV/2026-27/0001`, draft/cancelled rejection guardrail, HTTP client router test).
   - Frontend `apps/web/lib/__tests__/invoices.test.tsx` (3 tests passing: dashboard KPIs, status filtering, invoice preview modal).
   - Full test suites: 142 / 142 Pytest tests passing (100% green); 111 / 111 Vitest tests passing across 26 test suites (100% green).
   - 0 errors / 0 warnings on Ruff and ESLint; Next.js production build cleanly compiled with 35 routes.

### Decisions

- **Invoice Numbering Scheme**: Recorded verbatim — Indian financial year prefixed, sequential gap-free (e.g. `INV/2026-27/0001`). Financial year calculated from April 1 to March 31.
- **Frozen Snapshot Principle**: Invoice is a frozen accounting document. Product names, HSN codes, quantities, unit prices, tax rates, and totals are permanently captured upon creation and never live-recalculated from the order or product catalog.
- **Idempotency Guarantee**: Generating an invoice twice for the same sales order returns the existing invoice and invoice number without creating a duplicate record or incrementing sequence numbers.
- **Strict Order Status Guardrail**: Only orders in status `confirmed` or later (`confirmed`, `packed`, `shipped`, `delivered`) can be invoiced; `draft` or `cancelled` orders are blocked.

### Key values for future steps

- Invoice Model: `Invoice`, `InvoiceItem` (`apps/api/app/models/billing.py`)
- Invoice Repository Interface: `apps/api/app/repositories/interfaces/invoice_repository.py`
- Invoice Repository Impl: `apps/api/app/repositories/impl/invoice_repository.py`
- Invoice Domain Service: `apps/api/app/services/invoice_service.py`
- Invoice Router: `apps/api/app/api/routers/invoices.py` (`POST /sales-orders/{id}/invoice`, `GET /invoices`, `GET /invoices/{id}`)
- Web Route: `/admin/invoices`
- Navigation: `nav.ts` -> `/admin/invoices` (`invoices:view`)

### Files Created

- `apps/api/app/schemas/invoices.py`
- `apps/api/app/repositories/interfaces/invoice_repository.py`
- `apps/api/app/repositories/impl/invoice_repository.py`
- `apps/api/app/services/invoice_service.py`
- `apps/api/app/api/routers/invoices.py`
- `apps/api/tests/test_invoices.py`
- `apps/web/app/admin/invoices/page.tsx`
- `apps/web/lib/__tests__/invoices.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/app/repositories/impl/product_repository.py`
- `apps/api/app/repositories/impl/sales_order_repository.py`
- `apps/web/app/admin/sales-orders/page.tsx`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`
- `memory.md`

---

### Step 10.2 — Payments & Accounts-Receivable Ledger

**Timestamp:** 2026-08-19T01:47:00Z
**Status:** COMPLETE

### What was done

1. **Pydantic V2 Schemas (`apps/api/app/schemas/billing.py` & `apps/api/app/schemas/invoices.py`)**:
   - Created `PaymentCreateRequest` (`amount`, `method`, `paid_at`, `note`), `PaymentResponse`, `LedgerEntryResponse`, `RetailerLedgerResponse`, `OverdueDetectionResponse`.
   - Enriched invoice schemas with `paid_amount`, `outstanding_balance`, and list of recorded `payments`.
2. **Repository Layer & Dependency Inversion (`apps/api/app/repositories/interfaces/payment_repository.py` & `apps/api/app/repositories/impl/payment_repository.py`)**:
   - Defined `PaymentRepositoryInterface` Protocol (`create_payment`, `get_payment_by_id`, `list_payments_by_invoice_id`, `list_payments_by_retailer_id`, `get_total_paid_for_invoice`).
   - Implemented `SqlAlchemyPaymentRepository` and `InMemoryPaymentRepository` supporting zero-IO in-memory unit testing.
   - Updated `InvoiceRepositoryInterface` and implementations with `update_invoice`, `list_by_retailer_id`, and `list_overdue_candidates`.
3. **Domain Services (`apps/api/app/services/payment_service.py` & `apps/api/app/services/ledger_service.py`)**:
   - `PaymentService`:
     - **Overpayment Guardrail**: Validates payment amount > 0 and <= outstanding balance (`total_amount - paid_amount`), raising HTTP 422 if exceeded.
     - **Invoice Status Thresholds**: Dynamically transitions invoice status: `unpaid` → `partially_paid` (when cumulative paid < total) → `paid` (when cumulative paid == total).
     - **Retailer Credit Balance Reduction**: DECREASES `retailers.credit_balance` by payment amount (`credit_balance` represents balance currently owed).
     - **Audit Logging**: Emits `payment_recorded` audit event with invoice and retailer balance diffs.
     - **Overdue Detection**: Scans unpaid/partially-paid invoices past configurable `due_days` (default 30 days) and transitions them to `overdue` (emitting `overdue_invoices_flagged` audit event).
   - `LedgerService`:
     - `get_retailer_ledger(retailer_id)`: Assembles chronological statement of every invoice (debit +amount) and payment (credit -amount) with running balance matching `retailers.credit_balance` exactly.
4. **API Routers & Dependency Injection (`apps/api/app/api/routers/invoices.py`, `apps/api/app/api/routers/retailers.py`, `apps/api/app/core/di.py`)**:
   - `POST /invoices/{id}/payments`: Permission-guarded (`invoices:manage`) payment recording.
   - `GET /invoices/{id}/payments`: Payment history retrieval.
   - `POST /invoices/detect-overdue`: On-demand overdue invoice scan with configurable `due_days` query parameter.
   - `GET /retailers/{id}/ledger`: Permission-guarded (`retailers:view` / `invoices:view`) chronological AR statement.
   - Wired DI providers in `di.py` (`get_payment_repository`, `get_payment_service`, `get_ledger_service`, enriched `get_invoice_service`).
5. **Frontend Web UI (`apps/web/app/admin/retailers/[id]/ledger/page.tsx`, `apps/web/app/admin/invoices/page.tsx`, `apps/web/app/admin/retailers/page.tsx`)**:
   - Built `/admin/retailers/[id]/ledger` Accounts-Receivable statement view with KPI summary cards (Current Balance Owed, Credit Line & Limit, Total Invoiced, Total Settled), credit line utilization gauge, CSV export, Print/PDF export, transaction type filter tabs (all, invoices, payments), and embedded Record Payment modal.
   - Enriched `/admin/retailers` table with credit balance / credit limit utilization chip and direct link to statement ledger.
   - Enriched `/admin/invoices` with Record Payment button, modal form, overdue scanning trigger, and payment settlements history timeline in the preview modal.
6. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_payments_and_ledger.py` (5 hermetic tests passing: partial vs full payment status transitions, paired running balance invariant matching `retailer.credit_balance` across mixed invoices/payments, overpayment blocking with clear 422 error, overdue detection scan, and router integration).
   - Frontend `apps/web/lib/__tests__/ledger.test.tsx` (3 tests passing: KPI cards and ledger table rendering, transaction type filtering, payment modal submission).
   - Full test suites: **147 / 147 Pytest tests passing (100% green)**; **114 / 114 Vitest tests passing across 27 test suites (100% green)**.
   - **0 errors on Ruff and ESLint**; Next.js production build cleanly compiled with 35 static/dynamic routes.

### Decisions

- **Paired AR Ledger Invariant (Verbatim Rule)**:
  - `Invoice confirmation (Step 9.1)` **INCREASES** `retailers.credit_balance` by invoice total.
  - `Payment (Step 10.2)` **DECREASES** `retailers.credit_balance` by payment amount (`credit_balance` represents amount currently owed).
  - The chronological ledger statement computes running balance: `running_balance += debit_amount (invoice)` and `running_balance -= credit_amount (payment)`. The final running balance matches `retailers.credit_balance` exactly.
- **Overdue Window**:
  - Configurable due-date window (default 30 days) flags unpaid or partially paid invoices older than 30 days as `overdue` to trigger alerts.
- **Strict Overpayment Prevention**:
  - Direct validation prevents any payment greater than the invoice's remaining `outstanding_balance` (`total_amount - paid_amount`).

### Key values for future steps

- Payment Model: `Payment` (`apps/api/app/models/billing.py`)
- Payment Repository Interface: `apps/api/app/repositories/interfaces/payment_repository.py`
- Payment Repository Impl: `apps/api/app/repositories/impl/payment_repository.py`
- Payment Domain Service: `apps/api/app/services/payment_service.py`
- Ledger Domain Service: `apps/api/app/services/ledger_service.py`
- Payment Endpoints: `POST /invoices/{id}/payments`, `GET /invoices/{id}/payments`, `POST /invoices/detect-overdue`
- Ledger Endpoint: `GET /retailers/{id}/ledger`
- Web Ledger Route: `/admin/retailers/[id]/ledger`

### Files Created

- `apps/api/app/schemas/billing.py`
- `apps/api/app/repositories/interfaces/payment_repository.py`
- `apps/api/app/repositories/impl/payment_repository.py`
- `apps/api/app/services/payment_service.py`
- `apps/api/app/services/ledger_service.py`
- `apps/api/tests/test_payments_and_ledger.py`
- `apps/web/app/admin/retailers/[id]/ledger/page.tsx`
- `apps/web/lib/__tests__/ledger.test.tsx`

### Files Modified

- `apps/api/app/schemas/invoices.py`
- `apps/api/app/repositories/interfaces/invoice_repository.py`
- `apps/api/app/repositories/impl/invoice_repository.py`
- `apps/api/app/services/invoice_service.py`
- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/invoices.py`
- `apps/api/app/api/routers/retailers.py`
- `apps/web/app/admin/invoices/page.tsx`
- `apps/web/app/admin/retailers/page.tsx`
- `apps/web/lib/__tests__/invoices.test.tsx`
- `codebase_audit.md`
- `memory.md`

---

## Step 10.3 — GST Compliance: HSN Codes & E-Invoice / E-Way Bill Integration

**Timestamp:** 2026-08-19T02:00:00Z
**Status:** COMPLETE

### What was done

1. **Mandatory HSN Code Enforcement (`apps/api/app/services/invoice_service.py`)**:
   - Enforced strict validation during invoice generation from sales orders.
   - If any line item's product lacks an HSN code (None, empty, or "N/A"), invoice generation is blocked with HTTP 422, explicitly naming the product and SKU (`Product '{name}' (SKU: {sku}) is missing a mandatory HSN code. Please update the product catalog with a valid HSN code before generating a GST tax invoice.`).
   - For valid products, the HSN code is permanently captured in the immutable `invoice_items.hsn_code` snapshot.
2. **Statutory E-Invoice (IRN) & E-Way Bill Engine (`apps/api/app/services/einvoice_service.py`)**:
   - Built `EinvoiceService` following DIP with `EInvoiceProviderInterface` protocol.
   - Implemented `SandboxGspProvider` providing realistic, deterministic GST IRP simulation:
     - Generates 64-character SHA-256 hexadecimal IRN from `SellerGSTIN + DocType + DocNo + DocDate + TotInvVal`.
     - Generates 16-digit timestamped Acknowledgment Number and signed QR code containing essential B2B tax payload (Seller GSTIN, Buyer GSTIN, Doc No, Tot Val, Item HSNs).
     - Generates 12-digit statutory E-Way Bill Number and calculates validity duration based on transit distance (1 day per 200 km).
   - Ensured idempotency: repeating IRN generation on an existing invoice immediately returns the persisted statutory identifiers without duplicates.
   - Integrated with `AdminAuditLog` to track IRN and E-Way Bill generation events.
3. **API Endpoints & Configuration (`apps/api/app/api/routers/invoices.py`, `apps/api/app/core/config.py`, `apps/api/app/core/di.py`)**:
   - `GET /invoices/einvoice/config`: Exposes current statutory threshold guidelines, sandbox status, and GSP provider settings.
   - `POST /invoices/{invoice_id}/generate-irn`: Generates or retrieves statutory IRN and signed QR code.
   - `POST /invoices/{invoice_id}/generate-eway-bill`: Generates 12-digit E-Way Bill for road transit.
   - Environment variables documented in `.env.example`: `EINVOICE_ENABLED`, `GSP_PROVIDER`, `GSP_API_KEY`, `GSP_API_SECRET`, `EWAY_BILL_THRESHOLD_INR`.
4. **Frontend UI Enhancements (`apps/web/app/admin/products/page.tsx`, `apps/web/app/admin/invoices/page.tsx`)**:
   - **Product Catalog**: Added `HSN / GST` column displaying green code badge or amber `HSN Missing` warning badge; added live warning notice below HSN input in product create/edit modal.
   - **Invoices Dashboard & Preview**:
     - Added statutory threshold banner (explaining ₹5 Cr annual turnover requirement & sandbox availability).
     - Rendered Government GST E-Invoice container in invoice preview modal displaying 64-hex IRN with one-click copy, Acknowledgment number, and Signed QR code badge.
     - Added "Generate E-Invoice (IRN)" on-demand action.
     - Added E-Way Bill status badge and "Generate E-Way Bill" modal form (Vehicle No, Transporter Name, Distance in km).
     - Rendered HSN/SAC column in invoice line items table.
5. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_einvoice_and_hsn.py` (5 tests passing: missing HSN blocking with 422, valid HSN snapshot, 64-hex IRN generation, E-Way Bill validity duration, and HTTP API endpoints).
   - Frontend `apps/web/lib/__tests__/invoices.test.tsx` (4 tests passing: invoice list rendering, status filtering, HSN display & print action, on-demand IRN generation).
   - Full test suites: **152 / 152 Pytest tests passing (100% green)**; **115 / 115 Vitest tests passing across 27 test suites (100% green)**.
   - **0 errors on Ruff and ESLint**; Next.js production build cleanly compiled with 35 static/dynamic routes.

### Decisions

- **Statutory Turnover Threshold & Deferral Policy**:
  - E-invoicing is legally required in India only above the government-mandated turnover threshold (currently ₹5 Crore+ annual B2B turnover).
  - For businesses below the threshold, the system operates seamlessly in sandbox mode or can be completely deferred (`EINVOICE_ENABLED=false`) with zero runtime overhead or recurring costs.
- **GSP Choice & Cost Structure**:
  - Real-world production GST e-invoicing requires registration with an authorized GST Suvidha Provider (e.g. Masters India, ClearTax, IRIS) with recurring per-invoice or monthly subscription fees.
  - WareFlow isolates this behind `EInvoiceProviderInterface`, allowing instant switching between Sandbox, Direct IRP, or GSP APIs.
- **Strict HSN Pre-flight Validation**:
  - Invoices cannot be generated if any item lacks an HSN code, preventing downstream GST filing rejections and invalid tax returns.

### Key values for future steps

- E-Invoice Domain Service: `EinvoiceService` (`apps/api/app/services/einvoice_service.py`)
- GSP Sandbox Provider: `SandboxGspProvider` (`apps/api/app/services/einvoice_service.py`)
- E-Invoice Endpoints: `GET /invoices/einvoice/config`, `POST /invoices/{id}/generate-irn`, `POST /invoices/{id}/generate-eway-bill`
- Product HSN Column: `apps/web/app/admin/products/page.tsx`
- Invoice E-Invoice/E-Way Bill Preview & Modal: `apps/web/app/admin/invoices/page.tsx`

### Files Created

- `apps/api/app/services/einvoice_service.py`
- `apps/api/tests/test_einvoice_and_hsn.py`

### Files Modified

- `apps/api/.env.example`
- `apps/api/app/core/config.py`
- `apps/api/app/core/di.py`
- `apps/api/app/schemas/billing.py`
- `apps/api/app/schemas/invoices.py`
- `apps/api/app/repositories/interfaces/invoice_repository.py`
- `apps/api/app/repositories/impl/invoice_repository.py`
- `apps/api/app/services/invoice_service.py`
- `apps/api/app/api/routers/invoices.py`
- `apps/web/app/admin/products/page.tsx`
- `apps/web/app/admin/invoices/page.tsx`
- `apps/web/lib/__tests__/invoices.test.tsx`
- `codebase_audit.md`
- `memory.md`

---

## Step 11.1 — Retailer Portal Auth & Scoped Access

**Timestamp:** 2026-08-19T02:35:00Z
**Status:** COMPLETE

### What was done

1. **Retailer Authentication & Identity Models (`apps/api/app/models/portal.py`, `apps/api/app/models/__init__.py`)**:
   - Created `RetailerUser` model representing portal user accounts linked to a specific `retailer_id` (`retailers.id`).
   - Created `RetailerPortalInvite` model storing cryptographic invitation tokens, target retailer mapping, expiration timestamps, and acceptance state.
2. **Strict Server-Side Data Wall & Dependency Guards (`apps/api/app/core/security.py`)**:
   - Extended `CurrentUser` with `account_type: str = "staff"` ("staff" | "retailer") and `retailer_id: str | None = None`.
   - Updated `get_current_user` to inspect Firebase claims / database records and assign `account_type="retailer"` with explicit `retailer_id` and an empty staff permission set.
   - Updated `require_permission` to strictly reject non-staff callers (`account_type != "staff"`) with 403 Forbidden.
   - Added `require_staff` to block retailers from accessing admin endpoints.
   - Added `require_portal_retailer` to block staff accounts from customer portal endpoints.
   - Added `require_own_retailer(retailer_id)` ensuring a retailer cannot access or probe any order, invoice, or ledger record outside their own `retailer_id`.
3. **Domain Services & Repositories (`apps/api/app/services/portal_auth_service.py`, `apps/api/app/services/retailer_service.py`, `apps/api/app/repositories/impl/retailer_user_repository.py`)**:
   - Extended `RetailerService` with `invite_portal_access(retailer_id, payload, actor_id)`: validates retailer existence, generates secure invite tokens with 7-day expiration, provisions Firebase Auth user, and logs `retailer_portal_invite_sent` to audit repository.
   - Implemented `PortalAuthService`: handles portal bootstrap and enforces server-side ownership filters on `list_retailer_orders`, `get_retailer_order`, and `list_retailer_invoices`.
   - Added `InMemoryProfileRepository` in `apps/api/app/repositories/impl/profile_repository.py` for DIP unit test isolation.
4. **API Endpoints (`apps/api/app/api/routers/retailers.py`, `apps/api/app/api/routers/portal.py`)**:
   - `POST /retailers/{id}/invite-portal-access`: Guarded by `retailers:manage` (Owner/Manager only).
   - `POST /portal/auth/bootstrap`: Binds Firebase token & invite token to active retailer account.
   - `GET /portal/me`: Returns authenticated retailer identity, pricing tier, credit limit, and available balance.
   - `GET /portal/orders` & `GET /portal/orders/{id}`: Returns sales orders strictly scoped to caller's `retailer_id`.
   - `GET /portal/invoices` & `GET /portal/invoices/{id}`: Returns invoices strictly scoped to caller's `retailer_id`.
   - `GET /portal/ledger`: Returns full chronological AR ledger statement strictly scoped to caller's `retailer_id`.
5. **Frontend Retailer Portal Shell & UI (`apps/web/app/portal/`)**:
   - `apps/web/app/portal/layout.tsx`: Dedicated liquid glass shell without admin sidebars, featuring brand badge, live credit line status chip, navigation links (Catalog, My Orders, Invoices & Ledger, Appearance), and Sign Out button.
   - `apps/web/app/portal/login/page.tsx`: Retailer authentication page supporting email/password, invite token pre-fill (`?invite=...` & `?email=...`), and Google OAuth sign-in with clear staff account rejection banner.
   - `apps/web/app/portal/catalog/page.tsx`: Wholesale catalog shell.
   - `apps/web/app/portal/orders/page.tsx`: Scoped orders dashboard.
   - `apps/web/app/portal/invoices/page.tsx`: Scoped invoices and chronological accounts-receivable ledger statement.
6. **Automated Testing & QA Verification**:
   - Backend `apps/api/tests/test_retailer_portal_auth.py` (6 tests passing: invite token generation, bootstrap binding & staff rejection, own orders/invoices viewing, cross-retailer 403 blocking probe, cross-boundary guards, and HTTP router endpoints).
   - Frontend `apps/web/lib/__tests__/portal-auth.test.tsx` (3 tests passing: login form rendering, invite acceptance mode, and scoped navbar rendering).
   - Full test suites: **158 / 158 Pytest tests passing (100% green)**; **118 / 118 Vitest tests passing across 28 test suites (100% green)**.
   - **0 errors on ESLint**; Next.js production build compiled 39 routes cleanly.

### Decisions

- **Complete Server-Side Data Wall over Client-Side Hiding**:
  - Retailers have a completely different permission universe from staff. Security is enforced in the DB/service layer via `retailer_id` filtering and `require_own_retailer`, preventing IDOR or parameter tampering.
- **Dedicated `/portal` Shell & Login**:
  - Distinct `/portal/login` and `/portal/*` route tree ensures retailers never see internal warehouse/admin navigation, and staff accounts attempting to access `/portal` are cleanly redirected.

### Key values for future steps

- Portal Router: `/portal` (`apps/api/app/api/routers/portal.py`)
- Portal Auth Service: `PortalAuthService` (`apps/api/app/services/portal_auth_service.py`)
- Retailer User Repository: `RetailerUserRepository` (`apps/api/app/repositories/interfaces/retailer_user_repository.py`)
- Security Guards: `require_portal_retailer`, `require_own_retailer`, `require_staff` (`app.core.security`)
- Portal Frontend Entry: `/portal/login`, `/portal/catalog`, `/portal/orders`, `/portal/invoices`

### Files Created

- `apps/api/app/models/portal.py`
- `apps/api/app/schemas/portal.py`
- `apps/api/app/repositories/interfaces/retailer_user_repository.py`
- `apps/api/app/repositories/impl/retailer_user_repository.py`
- `apps/api/app/services/portal_auth_service.py`
- `apps/api/app/api/routers/portal.py`
- `apps/api/tests/test_retailer_portal_auth.py`
- `apps/web/app/portal/layout.tsx`
- `apps/web/app/portal/login/page.tsx`
- `apps/web/app/portal/catalog/page.tsx`
- `apps/web/app/portal/orders/page.tsx`
- `apps/web/app/portal/invoices/page.tsx`
- `apps/web/lib/__tests__/portal-auth.test.tsx`

- `apps/web/lib/__tests__/portal-auth.test.tsx`

### Files Modified

- `apps/api/app/models/__init__.py`
- `apps/api/app/schemas/retailers.py`
- `apps/api/app/repositories/impl/profile_repository.py`
- `apps/api/app/services/retailer_service.py`
- `apps/api/app/core/security.py`
- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/retailers.py`
- `apps/api/app/main.py`
- `codebase_audit.md`
- `memory.md`

---

## Step 11.2 — Product Catalog (Tier-Priced, Searchable)

**Timestamp:** 2026-08-19T06:10:00Z
**Status:** COMPLETE

### What was done

1. **Reused Core Pricing & Stock Services (`apps/api/app/services/portal_auth_service.py`)**:
   - Extended `PortalAuthService` by injecting `ProductRepository`, `StockRepository`, and `PricingEngineService` (from Phase 5 and Phase 7).
   - Implemented `_calculate_product_availability(product, on_hand)`: categorizes stock into privacy-preserving bands (`"Out"` if stock <= 0, `"Low"` if stock <= reorder point / 10, `"Available"` otherwise) — avoiding leakage of exact warehouse stock quantities to external retailers.
   - Implemented `_build_catalog_item(product, pricing_tier, cat_map)`: evaluates the retailer's assigned tier pricing strategy (`Standard` 0%, `Silver` 5%, `Gold` 10%) to compute line discounts and effective unit prices dynamically.
   - Implemented `get_retailer_catalog(current_user, category_id, search, skip, limit)` and `get_catalog_categories(current_user)`.
2. **Catalog Schemas (`apps/api/app/schemas/portal.py`)**:
   - Added `PortalCatalogProductResponse` (fields: `id`, `sku`, `name`, `description`, `content_details`, `image_url`, `category_id`, `category_name`, `unit`, `base_price`, `effective_price`, `discount_percentage`, `pricing_tier`, `availability`, `hsn_code`).
   - Added `PortalCategoryResponse` (fields: `id`, `name`).
3. **API Endpoints (`apps/api/app/api/routers/portal.py`)**:
   - `GET /portal/catalog`: Returns wholesale catalog items with tier-adjusted prices and privacy-safe availability bands. Guarded by `require_portal_retailer`.
   - `GET /portal/categories`: Returns distinct product categories for client filter tabs. Guarded by `require_portal_retailer`.
4. **Frontend Wholesale Catalog UI (`apps/web/app/portal/catalog/page.tsx`)**:
   - Implemented 4.x liquid glass product card grid with light-edge specular refraction, category tags, SKU badges, and HSN codes.
   - Live effective tier price display with strike-through base wholesale rate and discount chips (e.g. `5% OFF (Silver Tier)`).
   - Stock availability pills: Emerald `Available` with pulsing green dot, Amber `Low Stock`, Rose `Out of Stock`.
   - Instant client-side search across SKU, name, description, and category.
   - Category filter pills, stock status selector tabs, and multiple sorting options (A-Z, Z-A, Price Low-to-High, Price High-to-Low, Highest Discount).
   - Interactive "Ask a Question" inquiry modal with message input and toast notification.
   - Interactive "Add to Order" quick order modal with quantity increment/decrement counter and dynamic line total calculation.
5. **Testing & QA Verification**:
   - Backend `apps/api/tests/test_portal_catalog.py` (4 tests: tier pricing discount comparison for Gold/Silver/Standard, privacy-safe availability bands without quantity leakage, search/category filtering, and HTTP RBAC guards).
   - Frontend `apps/web/lib/__tests__/portal-catalog.test.tsx` (7 tests: catalog header rendering, tier price calculations, privacy availability badges, instant search filtering, category filtering, Ask Question modal, and Quick Order modal).
   - Full test suites: **162 / 162 Pytest tests passing (100% green)**; **125 / 125 Vitest tests passing across 29 test suites (100% green)**.
   - **0 ESLint errors/warnings**; Next.js production build compiled cleanly.

### Decisions

- **Availability Band Privacy Rule**:
  - Exact warehouse stock quantities (e.g. `total_on_hand`, batch breakdowns) are strictly obscured from retailers.
  - Only `"Available" | "Low" | "Out"` status is sent in `PortalCatalogProductResponse.availability` to avoid leaking sensitive warehouse levels externally.
- **Zero Duplicate Pricing Logic**:
  - Reused `PricingEngineService.calculate_line_price` directly with the retailer's `pricing_tier` claim, ensuring single source of truth for pricing calculations across both backend sales orders and frontend portal catalog.

### Key values for future steps

- Portal Catalog Endpoint: `GET /portal/catalog` (`apps/api/app/api/routers/portal.py`)
- Portal Categories Endpoint: `GET /portal/categories` (`apps/api/app/api/routers/portal.py`)
- Catalog Page: `apps/web/app/portal/catalog/page.tsx`
- Availability statuses: `"Available" | "Low" | "Out"`

### Files Created

- `apps/api/tests/test_portal_catalog.py`
- `apps/web/lib/__tests__/portal-catalog.test.tsx`

### Files Modified

- `apps/api/app/schemas/portal.py`
- `apps/api/app/services/portal_auth_service.py`
- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/portal.py`
- `apps/api/app/repositories/impl/stock_repository.py`
- `apps/web/app/portal/catalog/page.tsx`
- `apps/web/lib/__tests__/portal-auth.test.tsx`
- `codebase_audit.md`
- `memory.md`

---

## Step 11.3 — Product Inquiries (Easy Inquiry & Staff Response Flow)

**Timestamp:** 2026-08-19T12:00:00Z
**Status:** COMPLETE

### What was done

1. **Backend Schemas & Models (`apps/api/app/schemas/inquiries.py`)**:
   - `CreateInquiryRequest`: `{ product_id: str, message: str }`.
   - `RespondInquiryRequest`: `{ response: str }`.
   - `ProductInquiryResponse`: Complete schema containing inquiry ID, product details (`product_name`, `product_sku`), retailer information (`retailer_name`), message, lifecycle status (`open` | `responded` | `closed`), staff response, `created_at`, and `responded_at`.
2. **Persistence Abstraction & Repositories (`apps/api/app/repositories/`)**:
   - `InquiryRepositoryInterface` and `InquiryRepository` (SQLAlchemy & InMemory implementations for testing/DIP).
   - `NotificationRepositoryInterface` and `NotificationRepository` (SQLAlchemy & InMemory implementations).
3. **NotificationService Dispatch (`apps/api/app/services/notification_service.py`)**:
   - Reused existing `Notification` model to create in-app notification records and emit structured notification event logs to all users linked to the target retailer account upon staff response.
4. **Inquiry Business Logic Service (`apps/api/app/services/inquiry_service.py`)**:
   - `create_retailer_inquiry`: Validates product existence, binds `retailer_id` from the caller's verified `CurrentUser`, creates `ProductInquiry` with status `open`.
   - `list_retailer_inquiries`: Strict tenant data wall scoping inquiries exclusively to the authenticated retailer in chronological order.
   - `list_staff_inquiries`: Staff inbox queries filterable by `status` (`open`/`responded`) and `product_id`.
   - `respond_to_inquiry`: Records staff response text, updates status to `responded`, marks `responded_at` timestamp, and triggers `NotificationService.notify_retailer_inquiry_responded`.
5. **API Endpoints & Router Registration**:
   - `POST /portal/inquiries`: Guarded by `require_portal_retailer` (201 Created).
   - `GET /portal/inquiries`: Guarded by `require_portal_retailer` (200 OK).
   - `GET /inquiries`: Guarded by `require_staff` (200 OK, staff inbox).
   - `PATCH /inquiries/{inquiry_id}/respond`: Guarded by `require_staff` (200 OK).
   - Registered `inquiries.router` in `apps/api/app/main.py` and wired DI providers in `apps/api/app/core/di.py`.
6. **Frontend Web UI (`apps/web`)**:
   - `apps/web/app/portal/catalog/page.tsx`: Connected `InquiryModal` to `POST /portal/inquiries` with live token auth, loading spinners, and error alerts.
   - `apps/web/app/admin/inquiries/page.tsx`: Built full staff inquiry inbox using `AppLayout`, `ListViewTemplate`, stat cards (Total Inquiries, Pending Action Open, Responded), search bar, status filter pills, and `GlassModal` response dialog.
   - `apps/web/lib/nav.ts`: Added "Product Inquiries" navigation item under Wholesale Operations.
7. **Testing & QA Verification**:
   - Backend `apps/api/tests/test_inquiries.py`: 5 tests covering submission, 404 validation, strict retailer data wall isolation, staff inbox filtering, staff response + notification dispatch, and HTTP RBAC guards.
   - Frontend `apps/web/lib/__tests__/inquiries.test.tsx`: 4 tests covering staff inbox rendering, status filtering, staff response mutation, and portal catalog inquiry modal submission.
   - Test suites: **167 / 167 Pytest tests passing (100% green)**; **129 / 129 Vitest tests passing across 30 test files (100% green)**.
   - **0 ESLint errors/warnings**; Next.js production build compiled cleanly across 40 routes.

### Decisions

- **NotificationService Reuse (SOLID OCP)**:
  - Reused the centralized `NotificationService` and `Notification` persistence layer rather than creating bespoke communication channels.
- **Strict Retailer Tenant Isolation**:
  - `GET /portal/inquiries` and `POST /portal/inquiries` enforce `current_user.retailer_id` on the server side, ensuring retailers cannot view or submit inquiries on behalf of other accounts.

### Key values for future steps

- Portal Inquiry Submission API: `POST /portal/inquiries`
- Retailer Inquiries List API: `GET /portal/inquiries`
- Staff Inquiry Inbox API: `GET /inquiries`
- Staff Inquiry Response API: `PATCH /inquiries/{id}/respond`
- Staff Inbox Route: `/admin/inquiries`

### Files Created

- `apps/api/app/schemas/inquiries.py`
- `apps/api/app/repositories/interfaces/inquiry_repository.py`
- `apps/api/app/repositories/impl/inquiry_repository.py`
- `apps/api/app/repositories/interfaces/notification_repository.py`
- `apps/api/app/repositories/impl/notification_repository.py`
- `apps/api/app/services/notification_service.py`
- `apps/api/app/services/inquiry_service.py`
- `apps/api/app/api/routers/inquiries.py`
- `apps/api/tests/test_inquiries.py`
- `apps/web/app/admin/inquiries/page.tsx`
- `apps/web/lib/__tests__/inquiries.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/main.py`
- `apps/api/app/api/routers/portal.py`
- `apps/web/app/portal/catalog/page.tsx`
- `apps/web/lib/nav.ts`
- `apps/web/lib/__tests__/purchase-returns.test.tsx`
- `codebase_audit.md`
- `memory.md`

---

## Step 11.4 — Self-Service Order Placement & Retailer Order/Invoice History

**Timestamp:** 2026-08-19T12:15:00Z
**Status:** COMPLETE

### What was done

1. **Backend Schemas & Models (`apps/api/app/schemas/portal.py`)**:
   - Added `PortalOrderItemRequest` (`product_id: str`, `qty: float > 0`).
   - Added `PortalCreateOrderRequest` (`items: list[PortalOrderItemRequest]`).
   - Added `PortalOrderPlacementResponse` (`id`, `so_number`, `status`, `total_amount`, `auto_confirmed`, `message`, `reason`, `items_count`, `created_at`).
2. **Order Placement Orchestration (`apps/api/app/services/portal_auth_service.py`)**:
   - Implemented `place_retailer_order`: Enforces server-side `current_user.retailer_id` extraction (never client-supplied, preventing cross-tenant spoofing).
   - Reuses `SalesOrderService.create_order` and `SalesOrderService.confirm_order` verbatim (Zero Duplicated Logic).
   - If stock & credit limits are satisfied: order auto-confirms immediately with FIFO batch allocation and credit reservation.
   - If stock is insufficient or credit limit is exceeded: order remains safely in `DRAFT` status with clear explanation message, and dispatches a notification via `NotificationService` for operations staff manual review.
3. **API Endpoints (`apps/api/app/api/routers/portal.py`)**:
   - `POST /portal/orders`: Submits wholesale order, guarded by `require_portal_retailer` (201 Created).
   - Verified `GET /portal/orders` and `GET /portal/orders/{id}` strict data wall enforcement.
4. **Client-Side Cart Management (`apps/web/lib/portal-cart.ts`)**:
   - Built cart state manager with `localStorage` persistence (`wareflow_portal_cart`) and real-time custom event broadcasting (`wareflow_cart_updated` / `storage`).
   - Utility functions: `getCartItems`, `saveCartItems`, `addToCart`, `updateCartQuantity`, `removeFromCart`, `clearCart`, and `getCartTotal`.
5. **Frontend Web UI (`apps/web`)**:
   - `apps/web/app/portal/layout.tsx`: Added Cart navigation link (`/portal/cart`) with dynamic reactive cart item count badge.
   - `apps/web/app/portal/catalog/page.tsx`: Connected `QuickOrderModal` confirm action directly to `addToCart`.
   - `apps/web/app/portal/cart/page.tsx`: Interactive wholesale cart review with quantity steppers, subtotal computation, order submit mutation, and auto-confirmed success / draft review notice cards.
   - `apps/web/app/portal/orders/page.tsx`: Upgraded orders history table with `GlassCard`, `GlassBadge`, stat cards (Total Placed, Active In-Flight, Cumulative Value), search filter, status tabs, and `GlassModal` for detailed order line items inspection.
   - `apps/web/app/portal/invoices/page.tsx`: Verified read-only AR invoices and running account ledger view.
6. **Testing & QA Verification**:
   - Backend `apps/api/tests/test_portal_orders.py`: 4 tests validating auto-confirmation with FIFO deduction, draft status fallback with staff notification on credit limit excess, draft fallback on insufficient stock, and strict multi-tenant data wall isolation.
   - Frontend `apps/web/lib/__tests__/portal-orders.test.tsx`: 6 tests validating cart mutations, subtotal math, empty cart rendering, successful auto-confirmed order placement, draft review warning, and order history filtering.
   - Full test suites: **171 / 171 Pytest tests passing (100% green)**; **135 / 135 Vitest tests passing across 31 test suites (100% green)**.
   - **0 ESLint errors/warnings**; Next.js production build compiled cleanly across 41 routes.

### Decisions

- **Zero Duplicated Order Logic (Phase 11 Closing Proof)**:
  - Reused `SalesOrderService.create_order()` and `SalesOrderService.confirm_order()` verbatim without creating a parallel order processing engine. The portal serves as an authenticated external front door to the same domain services.
- **Server-Side Tenant Identity Enforcement**:
  - `retailer_id` is always bound from `current_user.retailer_id` on the server, guaranteeing that retailers cannot place orders or view histories belonging to other accounts.
- **Portal Payment Recording Out of Scope for v1**:
  - Retailer invoice and ledger views are strictly read-only in v1; payment recording remains staff-only.

### Key values for future steps

- Portal Order Submission API: `POST /portal/orders`
- Portal Orders List API: `GET /portal/orders`
- Portal Order Detail API: `GET /portal/orders/{id}`
- Portal Cart Route: `/portal/cart`
- Portal Orders Route: `/portal/orders`
- Portal Invoices Route: `/portal/invoices`

### Files Created

- `apps/api/tests/test_portal_orders.py`
- `apps/web/lib/portal-cart.ts`
- `apps/web/app/portal/cart/page.tsx`
- `apps/web/lib/__tests__/portal-orders.test.tsx`

### Files Modified

- `apps/api/app/schemas/portal.py`
- `apps/api/app/services/portal_auth_service.py`
- `apps/api/app/api/routers/portal.py`
- `apps/web/app/portal/layout.tsx`
- `apps/web/app/portal/catalog/page.tsx`
- `apps/web/app/portal/orders/page.tsx`
- `apps/web/lib/__tests__/portal-catalog.test.tsx`
---

## Step 12.1 — Delivery Assignment & Status Board

**Timestamp:** 2026-08-19T12:40:00Z
**Status:** COMPLETE

### What was done

1. **Delivery Data Model & Schema Definition (`apps/api`)**:
   - Built `Delivery` model in `apps/api/app/models/delivery.py` with columns `id`, `sales_order_id`, `driver_name`, `vehicle_no`, `status` (`DeliveryStatusEnum`: `assigned`, `out_for_delivery`, `delivered`, `failed`), `dispatched_at`, `delivered_at`, `notes`, and `created_at`, plus bidirectional relationship with `SalesOrder`.
   - Defined Pydantic schemas in `apps/api/app/schemas/deliveries.py` (`DeliveryAssignRequest`, `DeliveryStatusUpdateRequest`, `DeliveryResponse`).
2. **Repository Architecture (`apps/api`)**:
   - Created `DeliveryRepositoryInterface` protocol in `apps/api/app/repositories/interfaces/delivery_repository.py`.
   - Implemented `SqlAlchemyDeliveryRepository` (with `joinedload` on `sales_order.retailer` and `sales_order.customer`) and `InMemoryDeliveryRepository` in `apps/api/app/repositories/impl/delivery_repository.py`.
   - Registered providers in `apps/api/app/core/di.py`.
3. **Delivery Domain Service (`apps/api/app/services/delivery_service.py`)**:
   - `assign_delivery`: Verifies sales order status is `PACKED` (or `SHIPPED`), creates/updates delivery record with driver and vehicle in `ASSIGNED` status, advances order to `SHIPPED`, and writes audit log.
   - `update_delivery_status`: Supports state transitions:
     - `out_for_delivery`: Sets `dispatched_at = now()`.
     - `delivered`: Sets `delivered_at = now()` and automatically updates parent `sales_order.status = DELIVERED`.
     - `failed`: Strictly requires a non-empty `notes` field explaining why; keeps the sales order at `SHIPPED` without completing it and triggers an alert.
   - `get_delivery`, `get_delivery_by_order`, `list_deliveries` (supporting status/date filters and driver isolation).
4. **FastAPI Endpoints (`apps/api`)**:
   - `POST /sales-orders/{id}/delivery` & `GET /sales-orders/{id}/delivery` in `apps/api/app/api/routers/sales_orders.py`.
   - `GET /deliveries`, `GET /deliveries/{id}`, and `PATCH /deliveries/{id}/status` in `apps/api/app/api/routers/deliveries.py`.
   - Included `deliveries.router` in `apps/api/app/main.py`.
5. **Frontend Delivery Kanban Board & Integration (`apps/web`)**:
   - Built `/admin/deliveries/page.tsx` with 4 status columns (`Assigned`, `Out for Delivery`, `Delivered`, `Exceptions / Failed`), KPI summary cards (Assigned, In Transit, Delivered, Exceptions), search and driver filter, status transition buttons ("Start Delivery", "Delivered", "Failed", "Reschedule"), and "Assign Delivery" modal with packed sales order selector.
   - Added inline delivery tracking banner and direct board navigation to the sales order details modal in `apps/web/app/admin/sales-orders/page.tsx`.
   - Added "Delivery & Logistics" navigation link to `apps/web/lib/nav.ts` under Wholesale Operations.
6. **Testing & QA Verification**:
   - Backend `apps/api/tests/test_deliveries.py`: 6 tests validating 422 block on assigning non-packed orders, auto-advance to `shipped` on assign, dispatch timestamp recording, auto-advance to `delivered` on delivery completion, mandatory failure notes with order preserved at `shipped`, and full HTTP router integration.
   - Frontend `apps/web/lib/__tests__/deliveries.test.tsx`: 6 Vitest tests validating Kanban column rendering, KPI metric cards, card search filtering, status progression actions, failure notes validation, and assign delivery modal submission.
   - Full test suites: **177 / 177 Pytest tests passing (100% green)**; **141 / 141 Vitest tests passing across 32 test suites (100% green)**.
   - **0 ESLint errors/warnings**; Next.js production build compiled cleanly across 42 routes.

### Decisions

- **Delivery-Status-Drives-Order-Status Rule**:
  - Marking a delivery `delivered` automatically advances the parent `sales_order.status` to `delivered` in a single atomic transaction.
- **Strict Failure Handling & Preservation of Shipped State**:
  - Failing a delivery requires explanatory notes and keeps the sales order at status `shipped` (never falsely marked complete) while notifying operations for rescheduling.
- **Dispatch Guard**:
  - Only sales orders in `PACKED` (or already `SHIPPED`) status can be assigned for delivery; draft or confirmed orders are blocked with 422.

### Key values for future steps

- Delivery Assign API: `POST /sales-orders/{id}/delivery`
- Delivery Status Update API: `PATCH /deliveries/{id}/status`
- Deliveries List API: `GET /deliveries`
- Delivery Detail API: `GET /deliveries/{id}`
- Delivery Board Route: `/admin/deliveries`

### Files Created

- `apps/api/app/schemas/deliveries.py`
- `apps/api/app/repositories/interfaces/delivery_repository.py`
- `apps/api/app/repositories/impl/delivery_repository.py`
- `apps/api/app/services/delivery_service.py`
- `apps/api/app/api/routers/deliveries.py`
- `apps/api/tests/test_deliveries.py`
- `apps/web/app/admin/deliveries/page.tsx`
- `apps/web/lib/__tests__/deliveries.test.tsx`

### Files Modified

- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/sales_orders.py`
- `apps/api/app/main.py`
- `apps/web/app/admin/sales-orders/page.tsx`
- `apps/web/lib/nav.ts`
- `codebase_audit.md`
- `memory.md`

### Step 12.2 — Packing Slip & Pick List Generation

**Timestamp:** 2026-08-19T07:25:00Z
**Status:** COMPLETE

### What was done

1. **Pick List Generation (`apps/api/app/services/export_service.py`)**:
   - Implemented `generate_pick_list(sales_order_id)` producing high-contrast, staff-facing A4 PDFs using ReportLab flowables.
   - Formatted large-print checkboxes `[   ]` per line for physical floor ticking.
   - Automatically groups line items by warehouse location (handling multi-warehouse split orders cleanly).
   - Displays SKU, Product Name, Pick Qty, Unit of Measure, Bin/Aisle Location, and picker sign-off block.
   - Strictly enforces **ZERO pricing information** (no rates, unit prices, tax amounts, or monetary totals).

2. **Customer Packing Slip Generation (`apps/api/app/services/export_service.py`)**:
   - Implemented `generate_packing_slip(sales_order_id)` producing clean, professional customer-facing delivery manifests.
   - Renders distributor compliance header (Legal Entity Name, Address, 15-char GSTIN, 14-digit FSSAI License, Phone, Email).
   - Renders destination Ship-To consignee details and dispatch/driver transport metadata.
   - Formatted line items table with verification checkboxes, items count, and receiver goods acknowledgment signature block.
   - Strictly enforces **ZERO pricing information** (packing slip is a physical verification manifest, not a tax invoice).

3. **FastAPI Endpoints (`apps/api/app/api/routers/sales_orders.py`)**:
   - Added `GET /sales-orders/{id}/packing-slip.pdf` streaming PDF bytes with `Content-Disposition: inline; filename="packing-slip-{id}.pdf"`.
   - Added `GET /sales-orders/{id}/pick-list.pdf` streaming PDF bytes with `Content-Disposition: inline; filename="pick-list-{id}.pdf"`.
   - Protected with standard `orders:view` permission checks.

4. **Web UI Integration (`apps/web/app/admin/sales-orders/page.tsx`)**:
   - Added "Print Pick List" and "Print Packing Slip" actions in the sales order detail modal alongside existing invoice generation.
   - Integrated direct browser opening/printing via `handlePrintPickList` and `handlePrintPackingSlip`.

5. **Automated Testing & Verification**:
   - Added comprehensive Pytest test suite (`apps/api/tests/test_packing_slip_and_pick_list.py`) covering pick list checkboxes, multi-warehouse grouping, packing slip headers, HTTP streaming endpoints, and strictly asserting zero price presence.
   - Added Vitest tests in `apps/web/lib/__tests__/sales-orders.test.tsx` verifying modal buttons and export triggers.
   - All 181 backend Pytest tests passing 100% green.
   - All 142 frontend Vitest tests passing 100% green.
   - ESLint and Next.js production builds passing with zero errors.

### SOLID Principles Applied

- **Single Responsibility Principle (SRP)**: Dedicated `ExportService` handles PDF document layout and generation exclusively, keeping `SalesOrderService` and `DeliveryService` clean of document rendering details.
- **Open/Closed Principle (OCP)**: Document generators consume repository interfaces; new document styles or formats can be introduced without modifying sales order business logic.
- **Interface Segregation Principle (ISP)**: Document endpoints depend only on granular export query needs without imposing extra write dependencies.
- **Dependency Inversion Principle (DIP)**: `ExportService` receives repository interfaces via FastAPI dependency injection container (`get_export_service`).

### Key values for future steps

- Pick List Export API: `GET /sales-orders/{id}/pick-list.pdf`
- Packing Slip Export API: `GET /sales-orders/{id}/packing-slip.pdf`
- Document Generator: `ExportService` (`apps/api/app/services/export_service.py`)

### Files Created

- `apps/api/app/services/export_service.py`
- `apps/api/tests/test_packing_slip_and_pick_list.py`

### Files Modified

- `apps/api/requirements.txt`
- `apps/api/app/core/di.py`
- `apps/api/app/api/routers/sales_orders.py`
- `apps/api/app/repositories/impl/sales_order_repository.py`
- `apps/web/app/admin/sales-orders/page.tsx`
- `apps/web/lib/__tests__/sales-orders.test.tsx`
- `codebase_audit.md`
- `memory.md`

## Step 13.1 — Notification Engine (Strategy Pattern: channels)
**Timestamp:** 2026-08-19T07:40:00Z
**Status:** COMPLETE

### What was done
- Created `NotificationPayload` and `BaseNotificationChannel` strategy interface defining `send(payload) -> bool`.
- Implemented `InAppChannel` writing to both PostgreSQL `notifications` table (system of record) and Firestore `notifications/{uid}/items/{id}` path (realtime mirror).
- Implemented `EmailChannel` integrating Resend API for transactional HTML alert emails with development simulation logging fallback.
- Upgraded `NotificationService` to fan out notifications across requested channels (`notify(user_id, type, title, body, channels=[...])`) with delivery status tracking and dynamic channel registration (`register_channel`), preserving full backward compatibility.
- Updated `NotificationRepositoryInterface`, `NotificationRepository` (SQLAlchemy), and `InMemoryNotificationRepository` to support `list_for_user_paginated`, `count_unread`, `mark_as_read`, and `mark_all_as_read`.
- Created FastAPI endpoints `GET /notifications`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all` with Pydantic request/response schemas.
- Enhanced web `Topbar` component with live unread badge, dropdown list, mark-all-read action, real-time Firestore `onSnapshot` listener, and in-app floating toast alerts.
- Added comprehensive backend Pytest tests (channel fanout, OCP extensibility with `StubSmsChannel`, Firestore realtime mirror, unread counts, HTTP endpoints) and frontend Vitest tests.

### Decisions
- Channel pattern recorded as a reference OCP example: adding new channels (e.g. `SmsChannel`, `WhatsAppChannel`) requires zero changes to `NotificationService`.
- Firestore used narrowly for realtime notification delivery only (`notifications/{uid}/items/{id}`) — Postgres stays the system of record for everything, including notification history and pagination.

### Key values for future steps
- Notification Service: `NotificationService` (`apps/api/app/services/notification_service.py`)
- InApp Channel: `InAppChannel` (`apps/api/app/services/notification_channels/in_app_channel.py`)
- Email Channel: `EmailChannel` (`apps/api/app/services/notification_channels/email_channel.py`)
- Notifications API: `GET /notifications`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`
- Realtime Firestore Path: `notifications/{uid}/items/{id}`

---

## Step 13.2 — Low-Stock, Reorder-Point, Expiring-Batch & Overdue-Invoice Alerts
**Timestamp:** 2026-08-19T07:55:00Z
**Status:** COMPLETE

### What was done
- Created `BaseAlertRule` interface (`apps/api/app/services/alert_rules/base.py`) with `rule_name`, `evaluate(context)`, and `evaluate_entity(entity_id, context)` methods.
- Implemented 4 concrete alert rule strategies adhering strictly to OCP & SRP:
  - `LowStockRule`: Flags products where aggregate on-hand stock <= `reorder_point`, calculates suggested replenishment quantity (`reorder_qty` or 2x reorder point), and links to `/admin/purchase-orders`.
  - `CriticalStockRule`: Triggers urgent alerts for stockouts (`0` balance) or critical depletion (<= 25% of `reorder_point`), blocking fulfillment.
  - `ExpiringBatchRule`: Identifies stock batches with positive remaining quantity expiring in <= 30 days, providing quarantine / markdown recommendations and linking to `/admin/stock/ledger`.
  - `OverdueInvoiceRule`: Detects unpaid or partially paid invoices with `due_date < today` (or defaulting to invoice date + credit term), computes days overdue and total balance due, linking to `/admin/retailers/{id}/ledger`.
- Added `AlertLog` table and `AlertLogRepositoryInterface` (`apps/api/app/repositories/interfaces/alert_log_repository.py`) with SQLAlchemy and InMemory implementations to enforce a strict 24-hour deduplication guard (`has_recent_alert`), preventing alert spam across repetitive evaluation sweeps.
- Upgraded `AlertEngineService` (`apps/api/app/services/alert_engine_service.py`) to orchestrate operational rules and FSSAI regulatory compliance (`ExpiringLicenseRule`), dispatching alerts through `NotificationService` across in-app and email channels.
- Integrated `AlertScheduler` (`apps/api/app/core/alert_scheduler.py`) using APScheduler `BackgroundScheduler` running periodic scans (default 30 min) managed via FastAPI `lifespan` in `apps/api/app/main.py`.
- Added fast inline alert triggers in `SalesOrderService.confirm_order` and `StockService.adjust_stock` so inventory deductions immediately evaluate affected product thresholds within seconds without waiting for background scheduler ticks.
- Created comprehensive test suite in `apps/api/tests/test_alert_rules.py` testing each rule strategy, 24-hour deduplication suppression, sales order confirmation inline triggers, and scheduler lifecycle.
- All 193 backend Pytest tests, 146 frontend Vitest tests, and Next.js production build passing 100% green.

### Decisions
- Strategy Pattern for Alert Rules (OCP): New alerts (e.g. supplier fulfillment delays, price spike anomalies) can be added as standalone classes extending `BaseAlertRule` with zero changes to `AlertEngineService`.
- 24-Hour Deduplication Window: Repeated evaluation cycles within 24 hours check `alert_logs` table before sending notifications to avoid notification fatigue.
- Hybrid Trigger Architecture: 30-minute periodic APScheduler scan acts as a safety net, while event hooks on stock and sales order operations fire alerts instantly.

### Key values for future steps
- Alert Engine: `AlertEngineService` (`apps/api/app/services/alert_engine_service.py`)
- Alert Rules: `apps/api/app/services/alert_rules/`
- Alert Scheduler: `AlertScheduler` (`apps/api/app/core/alert_scheduler.py`)
- Alert Logs: `AlertLog` (`apps/api/app/models/notification.py`), `AlertLogRepository` (`apps/api/app/repositories/impl/alert_log_repository.py`)
- Endpoints: `POST /alerts/evaluate`, `GET /alerts/compliance`

---

## Step 13.3 — WhatsApp Notification Channel
**Timestamp:** 2026-08-19T08:15:00Z
**Status:** COMPLETE

### What was done
- Created `WhatsAppClient` (`apps/api/app/services/whatsapp_client.py`) as the single isolated point for Meta WhatsApp Business Cloud API calls (`https://graph.facebook.com/v21.0/{phone_number_id}/messages`).
- Implemented phone number normalization (`normalize_phone_number`) stripping non-digit characters and prepending country code `91` for standard 10-digit Indian numbers.
- Built `WhatsAppChannel` (`apps/api/app/services/notification_channels/whatsapp_channel.py`) implementing `BaseNotificationChannel`:
  - Maps stock/restock/reorder notifications to `wareflow_stock_available` template.
  - Maps order/dispatch/delivery notifications to `wareflow_goods_ready` template.
  - Maps general alerts with standard title/body parameters.
- Added environment variable gating: when `WHATSAPP_ACCESS_TOKEN` or `WHATSAPP_PHONE_NUMBER_ID` is unset, `WhatsAppChannel` logs a clear simulation notice and returns without crashing the application.
- Registered `WhatsAppChannel` into `get_notification_service()` and `alert_engine_factory()` in `apps/api/app/core/di.py` with zero changes to `NotificationService` (OCP proof).
- Added comprehensive unit tests in `apps/api/tests/test_whatsapp_channel.py` (phone normalization, template mapping, successful Cloud API dispatch, 400/401 error handling, unset env simulation, and `NotificationService` integration).
- All 201 backend Pytest tests, 146 frontend Vitest tests, and Next.js lint pass 100% green.

### Decisions
- Strategy Pattern for Notification Channels: WhatsApp is registered as a third pluggable channel (`InAppChannel`, `EmailChannel`, `WhatsAppChannel`).
- Meta Cloud API Free Tier Guard: Meta provides 1,000 free service conversations/month; email remains the always-available free fallback.
- Pre-Approved Templates: Business-initiated WhatsApp messages strictly use pre-approved templates (`wareflow_stock_available`, `wareflow_goods_ready`) with positional parameters.

### Key values for future steps
- WhatsApp Client: `WhatsAppClient` (`apps/api/app/services/whatsapp_client.py`)
- WhatsApp Channel: `WhatsAppChannel` (`apps/api/app/services/notification_channels/whatsapp_channel.py`)
- Registered Templates: `wareflow_stock_available`, `wareflow_goods_ready`
- Env Vars: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`

---

## Step 13.4 — Retailer Restock Subscriptions & Availability Alerts
**Timestamp:** 2026-08-19T11:05:00Z
**Status:** COMPLETE

### What was done
- **Stock Subscription Repository & Domain Service**:
  - Implemented `StockSubscriptionRepositoryInterface` and implementations (`SqlAlchemyStockSubscriptionRepository`, `InMemoryStockSubscriptionRepository`).
  - Created `StockSubscriptionService` managing subscribe, unsubscribe, active subscriber listing, and per-retailer subscription count aggregation.
- **Smart Alert Engine Strategy (`RestockAlertRule`)**:
  - Built `RestockAlertRule` implementing `BaseAlertRule`.
  - Evaluates active subscriptions for products crossing from zero/low stock to available (`current_stock > 0`).
  - Dispatches targeted notifications via `NotificationService` across subscriber's preferred channel (`whatsapp`, `email`, or `both`) using `wareflow_stock_available` template.
  - Automatically deactivates fulfilled subscriptions (`is_active=False`, `notified_at=now`) to prevent spamming until re-subscription.
  - Suppressed duplicate staff broadcasts for subscriber-directed restock alerts in `AlertEngineService`.
- **Inline Stock Replenishment Trigger**:
  - Connected inline restock alert evaluation to `StockService.receive_stock` and `adjust_stock` after inbound stock movements.
- **REST Endpoints & Dependency Injection**:
  - `POST /products/{product_id}/subscribe` (creates or reactivates subscription).
  - `DELETE /products/{product_id}/subscribe?retailer_id=...` (deactivates subscription).
  - `GET /products/{product_id}/subscribers` (staff-visible demand insight).
  - `GET /retailers/{retailer_id}/subscriptions` (retailer subscription list).
  - `GET /retailers/subscriptions/counts` (map of retailer_id -> count of active subscriptions).
  - Wired factories in `apps/api/app/core/di.py`.
- **Web UI Quick-Actions & Badges**:
  - `apps/web/app/admin/products/page.tsx`: Added "Alert" quick-action button in the product catalog table, opening a `GlassModal` enabling staff to subscribe a retailer on their behalf during phone calls with channel selector (WhatsApp, Email, Both) and manage active product subscribers.
  - `apps/web/app/admin/retailers/page.tsx`: Added "Restock Alerts" column with active subscription counts badge.
- **Tests & Verification**:
  - Added backend test suite in `apps/api/tests/test_stock_subscriptions_and_restock.py` (lifecycle, restock notification & auto-deactivation, HTTP endpoints, inline `StockService.receive_stock` trigger).
  - Added frontend test suite in `apps/web/lib/__tests__/stock-subscriptions-ui.test.tsx` (product catalog alert button, retailer subscriptions badge, channel preference selectors).
  - All 205 backend Pytest tests, 149 frontend Vitest tests, and Next.js build pass 100% green.

### Decisions
- **Auto-Unsubscribe on Fulfillment**: Once restock alert is delivered to a retailer, `is_active` is set to `False` with timestamp in `notified_at`. A retailer resubscribes if they want back-in-stock alerts for future depletion cycles.
- **Targeted Notification Channel Routing**: Subscriber's preference (`whatsapp`, `email`, `both`) is strictly respected during dispatch.
- **Phone Call Quick-Action Support**: Internal staff can search and subscribe retailers directly from the product catalog table during incoming phone queries.

---

## Step 13.5 — Supplier Ready-for-Dispatch Signal → Owner Notification
**Timestamp:** 2026-08-19T12:45:00Z
**Status:** COMPLETE

### What was done
- **Supplier Access Token Repository**:
  - Created `SupplierAccessTokenRepositoryInterface` (`apps/api/app/repositories/interfaces/supplier_access_token_repository.py`).
  - Implemented `SqlAlchemySupplierAccessTokenRepository` and `InMemorySupplierAccessTokenRepository` (`apps/api/app/repositories/impl/supplier_access_token_repository.py`).
- **Supplier Portal Schemas & Domain Service**:
  - Created `apps/api/app/schemas/supplier_portal.py` (`SupplierPortalPOResponse`, `SupplierPortalPOItemResponse`, `ReadyForDispatchResponse`).
  - Implemented `SupplierPortalService` (`apps/api/app/services/supplier_portal_service.py`) managing 30-day token generation, expiration checks (410 Gone), read-only PO projection, PO status transition to `ready_for_dispatch`, single-use token invalidation, and multi-channel notification dispatch.
- **Purchase Order Service Integration**:
  - Injected `SupplierPortalService` into `PurchaseOrderService` to auto-generate magic links upon PO transition to `ordered`.
  - Added `magic_link_token` field to `PurchaseOrderResponse`.
- **Public API Router**:
  - Implemented unauthenticated endpoints in `apps/api/app/api/routers/supplier_portal.py`:
    - `GET /supplier-portal/{token}`: Returns read-only PO summary and item breakdown.
    - `POST /supplier-portal/{token}/ready-for-dispatch`: Signals consignment readiness, invalidates token, and alerts staff.
  - Registered router in `apps/api/app/main.py` and DI container in `apps/api/app/core/di.py`.
- **Config & Environment**:
  - Added `frontend_url: str = "http://localhost:3000"` to `Settings` in `apps/api/app/core/config.py` and `FRONTEND_URL` in `apps/api/.env.example`.
- **Frontend Pages & UI Enhancements**:
  - Created public, mobile-first supplier portal page `apps/web/app/supplier/po/[token]/page.tsx` with glassmorphic cards, item breakdown, and "Mark Consignment Ready for Dispatch" action.
  - Updated `apps/web/app/admin/purchase-orders/page.tsx`:
    - Added `ready_for_dispatch` badge with `<Truck />` icon.
    - Added "Ready for Pickup" status filter tab and updated KPI metrics.
    - Enabled "Receive Goods" quick-action on `ready_for_dispatch` orders.
    - Added copyable "Supplier Magic Link" banner inside PO details modal.
- **Tests & Verification**:
  - Added backend test suite `apps/api/tests/test_supplier_portal.py` (5 tests covering token generation, expiration, single-use invalidation, status transition, notifications, and public HTTP endpoints).
  - Added frontend test suite `apps/web/lib/__tests__/supplier-portal-ui.test.tsx` (3 tests covering badge styling, magic link copy action, and ready for dispatch button).
  - All 210 backend Pytest tests, 152 frontend Vitest tests, and Next.js build pass 100% green.

### Decisions
- **Zero-Login Supplier Flow**: Suppliers need no accounts or passwords; a secure 48-byte URL-safe cryptographic token provides scoped, single-purpose access.
- **Single-Use Invalidation**: Once marked ready for dispatch, the token is permanently removed to prevent replay actions.
- **Multi-Channel Notification Dispatch**: WhatsApp + Email notifications are dispatched to all active staff holding `inventory:manage` permissions (or Owner role) using the `wareflow_goods_ready` template.

---

## Step 13.6 — SMS Notification Channel (Fallback)
**Timestamp:** 2026-08-19T13:05:00Z
**Status:** COMPLETE

### What was done
- **SMS Client & Fallback Channel (`SmsChannel`)**:
  - Implemented `SmsClient` (`apps/api/app/services/sms_client.py`) supporting Twilio REST API with phone number normalization (defaulting to +91 for 10-digit Indian numbers), single-segment 160-character length truncation (`truncate_sms_text`), and graceful simulation mode when unconfigured (`SMS_PROVIDER_API_KEY` / `TWILIO_ACCOUNT_SID` absent).
  - Implemented `SmsChannel` (`apps/api/app/services/notification_channels/sms_channel.py`) adhering to the Strategy pattern (`BaseNotificationChannel`), formatting high-priority concise messages for low-stock warnings, order confirmations, and PO dispatch readiness.
  - Zero modifications required to `NotificationService` (OCP proof).
- **Per-User / Per-Retailer Opt-In Channel Preferences**:
  - Created `NotificationPreference` model (`apps/api/app/models/notification.py`) with `notification_preferences` table storing `sms_enabled` (False by default — strict opt-in), `in_app_enabled`, `email_enabled`, `whatsapp_enabled`, `critical_stock_sms`, `order_updates_sms`, and `dispatch_ready_sms`.
  - Implemented `NotificationPreferenceRepositoryInterface` and implementations (`SqlAlchemyNotificationPreferenceRepository`, `InMemoryNotificationPreferenceRepository`).
  - Implemented `NotificationPreferenceService` (`apps/api/app/services/notification_preference_service.py`).
  - Added REST endpoints in `apps/api/app/api/routers/notifications.py`: `GET /notifications/preferences`, `PUT /notifications/preferences`, `GET/PUT /notifications/preferences/{entity_type}/{entity_id}`.
- **Config & Environment**:
  - Added `sms_provider`, `sms_provider_api_key`, `twilio_account_sid`, `twilio_auth_token`, and `twilio_from_number` to `Settings` (`apps/api/app/core/config.py`) and `.env.example`.
- **Tests & Verification**:
  - Added backend test suite `apps/api/tests/test_sms_channel.py` (6 tests covering phone normalization, 160-char truncation, unconfigured simulation, critical event formatting, OCP `NotificationService` integration, preference opt-in logic, and HTTP endpoints).
  - Added frontend test suite `apps/web/lib/__tests__/sms-preferences-ui.test.tsx` (2 tests covering opt-in toggles and category checkboxes).
  - Full suite verification: 216/216 backend Pytest tests pass, 154/154 frontend Vitest tests pass, Next.js build clean.

### Decisions
- **Strict Opt-In & Length Discipline for SMS**: Because outbound SMS incurs per-segment carrier costs and strict character limits (160 characters), SMS delivery is disabled by default and reserved exclusively for high-priority operational events (critical stock depletion for warehouse owners, confirmed orders for retailers). Rich formatting and marketing messages are strictly avoided.
- **Graceful Unconfigured Simulation**: In sandbox/dev environments without active Twilio trial credits or API keys, `SmsClient` and `SmsChannel` log simulated delivery and return `True` without breaking the alert engine.
- **Provider Choice & Trial Limits**: Twilio REST API was selected for its standard E.164 compliance and free trial credits ($15 sandbox credit, ~$0.0079/SMS in US/India). Pay-as-you-go Indian SMS gateways (e.g. Fast2SMS / MSG91) can be swapped seamlessly via the same `SmsClient` abstraction.

### Key values for future steps
- SMS Channel: `SmsChannel` (`apps/api/app/services/notification_channels/sms_channel.py`)
- SMS Client: `SmsClient` (`apps/api/app/services/sms_client.py`)
- Notification Preference Repo: `NotificationPreferenceRepositoryInterface` (`apps/api/app/repositories/interfaces/notification_preference_repository.py`)
- Notification Preference Service: `NotificationPreferenceService` (`apps/api/app/services/notification_preference_service.py`)
- Preference Endpoints: `GET /notifications/preferences`, `PUT /notifications/preferences`, `GET/PUT /notifications/preferences/{entity_type}/{entity_id}`

---

## Step 14.1 — Demand Forecasting Service (pluggable strategy)
**Timestamp:** 2026-08-19T13:20:00Z
**Status:** COMPLETE

### What was done
- **ForecastStrategy Interface & Pluggable Algorithms (OCP)**:
  - Created `ForecastStrategy` interface and `ForecastResult` dataclass (`apps/api/app/services/forecasting/base.py`).
  - Implemented `MovingAverageForecast` (`apps/api/app/services/forecasting/moving_average.py`): default strategy bucketing outbound movements into trailing 4 weekly windows with linearly increasing weights (1, 2, 3, 4) and statistical confidence scoring.
  - Implemented `ExponentialSmoothingForecast` (`apps/api/app/services/forecasting/exponential_smoothing.py`): second concrete strategy with recursive smoothing ($\alpha = 0.35$).
  - Created package exports in `apps/api/app/services/forecasting/__init__.py`.
- **Forecast Model & 24h Caching Repository Layer**:
  - Created `Forecast` model (`apps/api/app/models/forecast.py`) in `forecasts` table with `expires_at` column for 24-hour cache TTL and trend telemetry.
  - Created `ForecastRepositoryInterface` (`apps/api/app/repositories/interfaces/forecast_repository.py`).
  - Implemented `SqlAlchemyForecastRepository` and `InMemoryForecastRepository` (`apps/api/app/repositories/impl/forecast_repository.py`).
- **Forecasting Domain Service**:
  - Implemented `ForecastingService` (`apps/api/app/services/forecasting_service.py`) coordinating strategy execution, caching lookups, and catalog-wide top/slow mover summary aggregation.
  - Added DI container wiring in `apps/api/app/core/di.py` (`get_forecast_repository`, `get_forecasting_service`).
- **Pydantic Schemas & REST Endpoints**:
  - Created `ProductForecastResponse`, `ForecastSummaryItem`, `ForecastSummaryResponse` (`apps/api/app/schemas/forecast.py`).
  - Added endpoint `GET /products/{id}/forecast` in `apps/api/app/api/routers/products.py` supporting `horizon_days`, `strategy` override, and `force_refresh`.
  - Added endpoint `GET /analytics/forecast-summary` in `apps/api/app/api/routers/analytics.py` returning top movers and slow movers.
  - Registered `analytics` router in `apps/api/app/main.py`.
- **Configuration & Environment**:
  - Added `forecast_strategy` (default `"moving_average"`) and `forecast_cache_ttl_hours` (default `24`) to `Settings` (`apps/api/app/core/config.py`) and `.env.example`.
- **Testing & Verification**:
  - Created `apps/api/tests/test_forecasting.py` with 6 comprehensive test cases verifying exact mathematical accuracy against hand-computed values on 2 products, OCP strategy swapping without touching caller code, honest insufficient data handling on brand new items with 0 history, 24-hour caching behavior, and API endpoints.
  - Full test suite: 222/222 backend Pytest tests pass (100% green), 154/154 frontend Vitest tests pass (100% green).

### Decisions
- **Pluggable Statistical Strategy over External AI API**: Chose pure mathematical algorithms (Weighted Moving Average & Exponential Smoothing) behind a Strategy interface instead of external paid ML APIs. This delivers instant, zero-latency, explainable, cost-free forecasting with zero cloud lock-in while preserving seamless drop-in extensibility for future models.
- **24-Hour Database Cache TTL**: Forecasting runs over historical stock movements which change incrementally; caching results per product in the `forecasts` table for 24h ensures sub-millisecond API response times while `force_refresh=True` allows instant recalculation when needed.
- **Honest Insufficient Data Response**: Products without outbound history return `status="insufficient_data"` with 0.0 confidence and a clear diagnostic message rather than fabricating misleading numbers.

### Key values for future steps
- Strategy Interface: `ForecastStrategy` (`apps/api/app/services/forecasting/base.py`)
- Moving Average Strategy: `MovingAverageForecast` (`apps/api/app/services/forecasting/moving_average.py`)
- Exponential Smoothing Strategy: `ExponentialSmoothingForecast` (`apps/api/app/services/forecasting/exponential_smoothing.py`)
- Forecasting Service: `ForecastingService` (`apps/api/app/services/forecasting_service.py`)
- Forecast Repo Interface: `ForecastRepositoryInterface` (`apps/api/app/repositories/interfaces/forecast_repository.py`)
- Cache TTL: 24 hours (`FORECAST_CACHE_TTL_HOURS=24`)
- Endpoints: `GET /products/{id}/forecast`, `GET /analytics/forecast-summary`

---

## Step 14.2 — Dynamic Reorder Suggestions & Dead Stock Detection

**Timestamp:** 2026-08-19T13:30:00Z
**Status:** COMPLETE

### What was done
- **Reorder Suggestion Engine (`ReorderSuggestionService`)**:
  - Implemented dynamic reorder suggestion generation based on current on-hand stock, product `min_stock_level`, `reorder_quantity`, supplier lead time buffer, and Step 14.1 `ForecastingService` predicted daily demand.
  - Formula: `suggested_reorder_qty = max(product.reorder_quantity or 1, math.ceil(daily_demand * lead_time_buffer_days))` with fallback to `min_stock_level * 2` when no velocity data exists.
  - Urgency categorization:
    - `critical`: current stock == 0 (stockout condition).
    - `high`: current stock <= `min_stock_level * 0.5`.
    - `medium`: current stock <= `min_stock_level`.
  - Filter by `supplier_id` and `urgency` query parameters.
- **One-Click Pre-filled Draft Purchase Order Creation**:
  - Added `POST /analytics/reorder-suggestions/create-po` which bundles suggested reorder items for a given supplier and creates a real `PurchaseOrder` in `draft` status with line items pre-populated with suggested quantities and product cost prices.
- **Dead Stock Detection Service (`DeadStockService`)**:
  - Scans active product catalog for stagnant stock with positive on-hand inventory but zero outbound movements (`OUT`, `sales_shipment`, `sale`) over a configurable trailing window ($N$ days, default 90).
  - Calculates `tied_up_capital = current_stock * cost_price`, `days_since_last_sale`, and `total_dead_capital_locked`.
  - Excludes products with active sales movements within the window.
  - Ranks products descending by tied-up capital.
- **Pydantic Schemas & REST Endpoints**:
  - Created `ReorderSuggestionItem`, `ReorderSuggestionsResponse`, `CreatePOFromSuggestionsRequest`, `CreatePOFromSuggestionsResponse`, `DeadStockItem`, `DeadStockResponse` (`apps/api/app/schemas/analytics.py`).
  - Added endpoints in `apps/api/app/api/routers/analytics.py`:
    - `GET /analytics/reorder-suggestions`
    - `POST /analytics/reorder-suggestions/create-po`
    - `GET /analytics/dead-stock`
  - Wired DI factories in `apps/api/app/core/di.py` (`get_reorder_suggestion_service`, `get_dead_stock_service`).
- **Testing & Verification**:
  - Created comprehensive test suite in `apps/api/tests/test_reorder_and_dead_stock.py` (4 tests) covering hand-computed mathematical verification of reorder recommendations, lead time buffering, draft PO auto-generation from suggestions, dead stock detection and window exclusion, and HTTP endpoints.
  - Full test suite: 226/226 backend Pytest tests pass (100% green), 154/154 frontend Vitest tests pass (100% green).

### Decisions
- **Lead Time Buffered Reorder Formula**: Integrated Step 14.1 demand forecasts directly into reorder logic. If a product sells 5 units/day and supplier lead time is 7 days, the buffer recommends ordering at least 35 units to ensure zero stockouts during transit.
- **Urgency Classification Model**: Differentiated stockout (`critical`), severe depletion (`high`), and low stock (`medium`) so warehouse operators can triage procurement orders effectively.
- **Dead Stock Working Capital Ranking**: Sorted dead inventory by `tied_up_capital` rather than just unit quantity, empowering business owners to prioritize liquidation or discounting campaigns where cash is most tied up.

### Key values for future steps
- Reorder Suggestion Service: `ReorderSuggestionService` (`apps/api/app/services/reorder_suggestion_service.py`)
- Dead Stock Service: `DeadStockService` (`apps/api/app/services/dead_stock_service.py`)
- Endpoints:
  - `GET /analytics/reorder-suggestions`
  - `POST /analytics/reorder-suggestions/create-po`
  - `GET /analytics/dead-stock`


## [Step 14.3] — Anomaly Detection & Owner Insight Narratives

### What was done
- **Statistical Order Anomaly Detection ($3\sigma$)**: Implemented `AnomalyDetectionService` which flags sales order lines as `is_unusual` if the quantity exceeds $\text{mean} + 3\sigma$ of that buyer's (retailer/customer) historical orders for that product.
- **Advisory UI Badging (Non-Blocking)**: Flagged orders surface an amber `⚠️ Unusual Size` badge in the Sales Orders DataTable and an anomaly review advisory card inside the Order Detail modal with line-item 3σ badges and explanation reasons. High order sizes never block draft creation or confirmation.
- **Weekly Executive Insight Narrative Engine**: Implemented `InsightNarratorService` generating grounded weekly executive briefs summarizing trailing 7-day revenue, confirmed orders, velocity leaders, and tied-up dead stock capital. Uses Groq LLM when `GROQ_API_KEY` is present, with deterministic template fallback when unset or timing out.
- **7-Day Token Discipline & Caching**: Weekly insights are cached for 7 days in memory with `is_cached=True` and `expires_at`, with on-demand cache bypass using `?force_refresh=true`.
- **REST Endpoints**:
  - `GET /analytics/weekly-insight`
  - `GET /analytics/anomalies/order/{order_id}`
- **Owner Dashboard UI**: Added a glassmorphic AI Executive Intelligence Briefing card on `/dashboard` showcasing headline, grounded 2-3 sentence brief, quantitative verified metrics, and on-demand refresh trigger.
- **Test Suites**:
  - Backend: `apps/api/tests/test_anomaly_detection_and_insights.py` (6 tests covering 10x order spike, edge cases, deterministic grounding, 7-day caching, and API routes).
  - Frontend: `apps/web/lib/__tests__/anomaly-and-insights-ui.test.tsx` (3 tests covering table badge, modal advisory banner, and dashboard executive card).

### SOLID Principles Applied
- **SRP (Single Responsibility Principle)**: `AnomalyDetectionService` owns statistical $z$-score evaluation; `InsightNarratorService` owns KPI metric compilation and LLM/template prompting.
- **DIP (Dependency Inversion Principle)**: `AnomalyDetectionService` depends strictly on `SalesOrderRepositoryInterface.get_historical_order_quantities(...)`.
- **OCP (Open/Closed Principle)**: Pluggable AI generation with deterministic fallback ensures identical dashboard functionality without hard external API lock-in.

### Files Created/Modified
- Created: `apps/api/tests/test_anomaly_detection_and_insights.py`
- Created: `apps/web/lib/__tests__/anomaly-and-insights-ui.test.tsx`
- Modified: `apps/api/app/schemas/analytics.py`
- Modified: `apps/api/app/services/anomaly_detection_service.py`
- Modified: `apps/api/app/services/insight_narrator.py`
- Modified: `apps/api/app/api/routers/analytics.py`
- Modified: `apps/api/app/core/di.py`
- Modified: `apps/api/app/repositories/impl/sales_order_repository.py`
- Modified: `apps/web/app/admin/sales-orders/page.tsx`
- Modified: `apps/web/app/dashboard/page.tsx`

### Key values for future steps
- Anomaly Detection Service: `AnomalyDetectionService` (`apps/api/app/services/anomaly_detection_service.py`)
- Insight Narrator Service: `InsightNarratorService` (`apps/api/app/services/insight_narrator.py`)
- Endpoints:
  - `GET /analytics/weekly-insight`
  - `GET /analytics/anomalies/order/{order_id}`

---

## Step 15.1 — Owner Analytics Dashboard (KPIs + Charts)

**Timestamp:** 2026-08-21T02:10:00Z
**Status:** COMPLETE

### What was done
- **Single Round-Trip Owner Analytics API (`GET /analytics/dashboard`)**:
  - Implemented `OwnerDashboardService` synthesizing enterprise wholesale telemetry:
    - **Monthly Wholesale Revenue**: Current calendar month sales from active/delivered orders (`confirmed`, `packed`, `shipped`, `delivered`).
    - **Month-End Inventory Valuation**: Total on-hand physical units and cost-valuation (`on_hand * cost_price`).
    - **Active Order Pipelines**: Open POs count (`draft`, `ordered`, `ready_for_dispatch`, `partially_received`) and Open SOs count (`draft`, `confirmed`, `packed`, `shipped`).
    - **Stock Health SKUs**: Low stock ($0 < \text{on\_hand} \le \text{reorder\_point}$) and Critical stock ($\text{on\_hand} \le 0$) counts.
    - **Outstanding Receivables & Aging**: Unpaid balance totals on non-cancelled invoices and overdue count ($due\_date < today$).
    - **Top 5 Fastest-Moving Products**: Trailing 30-day velocity leaders ranked by units and revenue.
    - **Top 5 Dead Stock Risks**: Capital tied up in inactive inventory (60+ days without outbound movement).
    - **30-Day Movement Timeseries**: Inbound receipts vs outbound dispatches daily buckets.
    - **Low-Stock Quick-List Action Queue**: Deficits, supplier names, urgency badges (`critical`, `high`, `medium`), and restock CTAs.
    - **Overdue Invoices Action Queue**: Invoice numbers, retailer names, overdue days, balance due, and collection links.
    - **Empty State Detection**: Zero crash on clean deployments, returning zeroed defaults and guided onboarding flag.
- **Frontend Dashboard UI (`apps/web/app/dashboard/page.tsx`)**:
  - Wired live `OwnerDashboardResponse` into `DashboardTemplate`:
    - Top KPI summary cards for Monthly Sales Revenue, Month-End Inventory Valuation & Units, Stock Health alerts, and Outstanding Receivables.
    - Recharts interactive 30-day AreaChart with smooth linear gradients, dual-line legend, tooltips, and responsive layout.
    - Top 5 Fastest-Moving velocity list and Dead Stock capital risk cards.
    - Low-Stock Quick-List widget with supplier names and "+ Restock PO" actions.
    - Overdue Receivables Queue widget with overdue days and "Collect Payment" links.
    - AI Executive Intelligence Briefing card with on-demand refresh.
    - Guided `EmptyState` component for brand-new deployments.
- **Test Suites**:
  - Backend: `apps/api/tests/test_owner_dashboard.py` (4 tests verifying fresh deployment empty state, exact hand-calculated KPI metrics, 30-day movement bucket aggregation, and FastAPI TestClient integration).
  - Frontend: `apps/web/lib/__tests__/owner-dashboard-ui.test.tsx` (2 tests verifying KPI numbers, Recharts chart container, quick lists, top movers, and guided empty state).

### SOLID Principles Applied
- **SRP (Single Responsibility Principle)**: `OwnerDashboardService` focuses solely on aggregating and computing wholesale telemetry metrics from existing domain repositories.
- **DIP (Dependency Inversion Principle)**: `OwnerDashboardService` depends on repository abstractions (`StockRepositoryInterface`, `ProductRepositoryInterface`, `SalesOrderRepositoryInterface`, `PurchaseOrderRepositoryInterface`, `InvoiceRepositoryInterface`, `SupplierRepositoryInterface`).
- **Zero Database Schema Bloat**: Derives all analytics dynamically from existing tables without unnecessary cache tables or redundant schema mutations.

### Files Created/Modified
- Created: `apps/api/app/services/owner_dashboard_service.py`
- Created: `apps/api/tests/test_owner_dashboard.py`
- Created: `apps/web/lib/__tests__/owner-dashboard-ui.test.tsx`
- Modified: `apps/api/app/schemas/analytics.py`
- Modified: `apps/api/app/core/di.py`
- Modified: `apps/api/app/api/routers/analytics.py`
- Modified: `apps/api/app/repositories/impl/stock_repository.py`
- Modified: `apps/web/app/dashboard/page.tsx`

### Key values for future steps
- Owner Dashboard Service: `OwnerDashboardService` (`apps/api/app/services/owner_dashboard_service.py`)
- DI Factory: `get_owner_dashboard_service` in `apps/api/app/core/di.py`
- Endpoint: `GET /analytics/dashboard` (Returns `OwnerDashboardResponse`)

---

## Step 15.2 — Accounts-Receivable Aging Report

**Timestamp:** 2026-08-24T13:45:00Z
**Status:** COMPLETE

### What was done
- **AR Aging Analytics Backend Service (`GET /analytics/ar-aging`)**:
  - Implemented `ARAgingService` in `apps/api/app/services/ar_aging_service.py` to aggregate unpaid/partially-paid wholesale invoices against the live reference date (`as_of`).
  - Divided receivables into standardized aging buckets:
    - **Current (Within Terms)**: Due in future or today (`days_overdue <= 0`).
    - **1–30 Days Overdue**: `1 <= days_overdue <= 30`.
    - **31–60 Days Overdue**: `31 <= days_overdue <= 60`.
    - **61–90 Days Overdue**: `61 <= days_overdue <= 90`.
    - **90+ Days Overdue (Critical Risk)**: `days_overdue >= 91`.
  - Computes per-retailer metrics: `current`, `bucket_1_30`, `bucket_31_60`, `bucket_61_90`, `bucket_90_plus`, `total_overdue`, `total_outstanding`, `oldest_invoice_date`, `invoice_count`, and authorized `credit_limit`.
  - Calculates portfolio-wide summary totals: `total_current`, `total_bucket_1_30`, `total_bucket_31_60`, `total_bucket_61_90`, `total_bucket_90_plus`, `total_overdue`, `total_outstanding`, `total_retailers`, and `overdue_retailers_count`.
  - Added query param `include_zero_balance: bool = True` allowing clear zeroed representation of accounts with zero debt or clean filtering.
  - Registered `get_ar_aging_service` dependency injection factory in `apps/api/app/core/di.py` and exposed `GET /analytics/ar-aging` in `apps/api/app/api/routers/analytics.py`.
- **AR Aging Report Web UI (`/admin/analytics/ar-aging`)**:
  - Built comprehensive glassmorphic reporting interface in `apps/web/app/admin/analytics/ar-aging/page.tsx`:
    - Top row of 6 KPI summary cards (`Total Outstanding`, `Current`, `1–30d`, `31–60d`, `61–90d`, `90+d Critical`).
    - Proportional visual distribution bar with multi-colored bucket segments (Emerald, Amber, Orange, Rose, Crimson).
    - Search toolbar with real-time text query, bucket quick filter pills, and "Hide Zero Balance" toggle.
    - Full bucketed data table with column sortability, formatted currency values (₹), credit line indicators, critical alert badges for 90+ days delinquent accounts, and direct "Ledger" links into `/admin/retailers/[id]/ledger` (Step 9.2 / 10.2).
    - CSV export feature (`Export CSV`) generating downloadable timestamped reports.
  - Added "AR Aging Report" under Wholesale Operations / GST Invoices in `apps/web/lib/nav.ts`.
- **Test Suites**:
  - Backend: `apps/api/tests/test_ar_aging.py` (3 tests covering fresh deployment empty state, exact hand-calculated 2-retailer mixed-age invoice bucket checks, zero-balance toggle, and FastAPI TestClient integration). All 239 backend tests passing.
  - Frontend: `apps/web/lib/__tests__/ar-aging-ui.test.tsx` (4 tests covering KPI cards, distribution bar, search, bucket filtering, zero-balance toggle, and clean empty state). All 163 frontend tests passing.

### Decisions
- **Aging Bucket Boundaries**: Fixed cutoff windows at 30/60/90-day increments:
  - Current: $\text{due\_date} \ge \text{as\_of}$ ($\text{days\_overdue} \le 0$)
  - 1–30 Days: $1 \le \text{days\_overdue} \le 30$
  - 31–60 Days: $31 \le \text{days\_overdue} \le 60$
  - 61–90 Days: $61 \le \text{days\_overdue} \le 90$
  - 90+ Days: $\text{days\_overdue} \ge 91$
- **Default Credit Terms Fallback**: Invoices without an explicit `due_date` default to `invoice_date + 30 days`.
- **Direct Ledger Navigation**: Retailer names and table actions directly link to `/admin/retailers/${retailer_id}/ledger` for seamless collection workflows.

### Key values for future steps
- AR Aging Service: `ARAgingService` (`apps/api/app/services/ar_aging_service.py`)
- DI Factory: `get_ar_aging_service` in `apps/api/app/core/di.py`
- Endpoint: `GET /analytics/ar-aging` (Returns `ARAgingReportResponse`)
- Web Route: `/admin/analytics/ar-aging`
- Aging Cutoffs: 30 days (`1-30`), 60 days (`31-60`), 90 days (`61-90`), 91+ days (`90+`)

---

## Step 15.3 — Excel / PDF Export

**Timestamp:** 2026-08-24T14:20:00Z
**Status:** COMPLETE

### What was done
- **Excel & PDF Export Backend Service (`ExportService`)**:
  - Implemented complete `ExportService` in `apps/api/app/services/export_service.py` supporting both ReportLab PDF generation and openpyxl Excel spreadsheet generation:
    - **Pick List PDF (`GET /sales-orders/{id}/pick-list.pdf`)**: Internal warehouse document with batch checkboxes, storage zone grouping, and strict zero-pricing guardrails.
    - **Packing Slip PDF (`GET /sales-orders/{id}/packing-slip.pdf`)**: Customer-facing shipment delivery manifest with consignee address, dispatch logistics info, line items, and receiver signature block.
    - **Purchase Order PDF (`GET /purchase-orders/{id}/pdf`)**: Vendor-facing procurement order with company header from `BusinessSettings`, vendor contact block, item table, and procurement signatory.
    - **Sales Order PDF (`GET /sales-orders/{id}/pdf`)**: Wholesale sales order confirmation with customer pricing tier, line item amounts, and tax breakdown.
    - **GST Tax Invoice PDF (`GET /invoices/{id}/pdf`)**: Official statutory tax invoice document with HSN codes, CGST/SGST/IGST breakdown, E-Invoice IRN & QR code details, E-Way Bill references, bank remittance details, and authorized signatory.
    - **Stock Overview Excel (`GET /stock/overview.xlsx`)**: Formatted multi-column workbook containing SKU, product name, category, UoM, on-hand units, cost/wholesale price, valuation, reorder thresholds, health status, and automated Excel `SUM()` formula totals.
    - **Stock Movement Ledger Excel (`GET /stock/movements.xlsx`)**: Formatted ledger sheet with movement IDs, UTC timestamps, transaction types (`IN`, `OUT`, `ADJUSTMENT`), product SKUs, quantities, and reference links.
    - **AR Aging Report Excel (`GET /analytics/ar-aging.xlsx`)**: Structured aged receivables matrix with retailer IDs, credit limits, 30/60/90+ day bucket columns, total overdue, outstanding amounts, and summary formulas.
  - Added dependency `openpyxl>=3.1.0,<4.0.0` to `apps/api/requirements.txt`.
  - Wired `get_export_service` dependency injection factory in `apps/api/app/core/di.py`.
  - Exposed all 6 endpoints across the router layer (`purchase_orders.py`, `sales_orders.py`, `invoices.py`, `stock.py`, `analytics.py`).
- **Frontend Export Integration**:
  - Enhanced `apiClient.downloadBlob(endpoint, filename)` helper in `apps/web/lib/api-client.ts` with automatic object URL creation, DOM download triggering, and clean URL revocation.
  - Added export buttons across administrative interfaces:
    - `apps/web/app/admin/purchase-orders/page.tsx`: Added "PDF" export button in table actions column.
    - `apps/web/app/admin/sales-orders/page.tsx`: Added "PDF" export button in table actions column and modal footer.
    - `apps/web/app/admin/invoices/page.tsx`: Added "PDF" export button in table actions and "Download Official GST PDF" in invoice preview modal.
    - `apps/web/app/admin/inventory/page.tsx`: Added "Export Excel (.xlsx)" toolbar action in `ListViewTemplate`.
    - `apps/web/app/admin/stock/ledger/page.tsx`: Added "Export Excel (.xlsx)" action in `ListViewTemplate`.
    - `apps/web/app/admin/analytics/ar-aging/page.tsx`: Added "Export Excel (.xlsx)" action next to CSV export.
- **Verification & QA**:
  - Backend pytest suite: `apps/api/tests/test_export_service.py` (7 tests verifying PDF generation, byte stream sizes, Excel headers, sheet names, and Excel formula generation). Full backend suite passing: 246/246 tests passing.
  - Frontend Vitest suite: `apps/web/lib/__tests__/export-service.test.ts` (4 tests verifying blob downloads and error handling). Full frontend suite passing: 40/40 test files (167 tests) passing.
  - Next.js production build: Succeeded with 0 errors across all 43 static/dynamic routes.

### SOLID Principles Applied
- **Single Responsibility Principle (SRP)**: `ExportService` solely manages file format formatting and binary byte stream rendering, leaving database queries and business calculations to repositories and domain services.
- **Open/Closed Principle (OCP)**: Document builders can be extended with new file formats (e.g. CSV, XML) without modifying existing PDF/Excel logic.
- **Dependency Inversion Principle (DIP)**: `ExportService` depends exclusively on repository interfaces (`SalesOrderRepositoryInterface`, `PurchaseOrderRepositoryInterface`, `InvoiceRepositoryInterface`, etc.) injected via `apps/api/app/core/di.py`.

### Key values for future steps
- Document Service: `ExportService` (`apps/api/app/services/export_service.py`)
- DI Factory: `get_export_service` in `apps/api/app/core/di.py`
- Endpoints:
  - `GET /purchase-orders/{id}/pdf` (`application/pdf`)
  - `GET /sales-orders/{id}/pdf` (`application/pdf`)
  - `GET /invoices/{id}/pdf` (`application/pdf`)
  - `GET /stock/overview.xlsx` (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
  - `GET /stock/movements.xlsx` (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
  - `GET /analytics/ar-aging.xlsx` (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)

---

## Step 15.4 — Global Admin Search

**Timestamp:** 2026-08-24T14:40:00Z
**Status:** COMPLETE

### What was done
- **Backend Global Search Engine (`GET /search?q=`)**:
  - Implemented `SearchService` in `apps/api/app/services/search_service.py` performing unified querying across 6 core wholesale domain models:
    - Products (matched by SKU and product name)
    - Sales Orders (matched by SO number, retailer name, or customer name)
    - Purchase Orders (matched by PO number and supplier name)
    - Invoices (matched by invoice number and buyer name)
    - Retailers (matched by store name, contact person, and phone)
    - Suppliers (matched by supplier name, contact person, and phone)
  - Implemented multi-tier relevance scoring algorithm:
    - **Score 100.0**: Exact natural key match (exact SKU, exact SO number, exact PO number, exact Invoice number)
    - **Score 95.0**: Exact entity/product name match
    - **Score 85.0**: Prefix match on natural key
    - **Score 75.0**: Prefix match on name
    - **Score 50.0**: Substring match anywhere in identifier, name, or metadata
  - Created schema `SearchResponse` and `SearchResultItem` in `apps/api/app/schemas/search.py`.
  - Registered `get_search_service` in `apps/api/app/core/di.py` injecting repository abstractions.
  - Exposed `GET /search` in `apps/api/app/api/routers/search.py` and mounted to FastAPI app in `main.py`.
- **Frontend Command Palette UI (`SearchCommandPalette`)**:
  - Implemented `SearchCommandPalette.tsx` in `apps/web/components/SearchCommandPalette.tsx`:
    - Full keyboard navigation: `ArrowDown`/`ArrowUp` to cycle selection, `Enter` to navigate (`router.push`), `Escape` to close.
    - Debounced search query handler calling `GET /search?q=`.
    - Liquid glassmorphism modal design with category icons (Package, ShoppingCart, Truck, Receipt, Store, Building2) and status badges.
    - Keyboard shortcut hint bar (`↑↓ Navigate`, `↵ Select`, `ESC Close`).
  - Added persistent search trigger bar in `apps/web/components/Topbar.tsx` with `⌘K` / `Ctrl+K` indicator.
  - Added global `Cmd+K` / `Ctrl+K` keydown event listener in `Topbar.tsx` to open the palette from anywhere across the admin dashboard.
- **Verification & QA**:
  - Backend pytest suite: `apps/api/tests/test_search.py` (7/7 tests passing for exact SKU, retailer name, invoice number, orders, prefix ranking, and TestClient integration). Total backend tests: 253/253 passing.
  - Frontend Vitest suite: `apps/web/lib/__tests__/search-ui.test.tsx` (5/5 tests passing for Topbar trigger, Cmd+K keypress, API query & rendering, arrow navigation, and Escape dismissal). Total frontend tests: 41 test suites (172 tests) passing.
  - Next.js production build: Succeeded in 3.4s with 0 errors across all 43 static/dynamic routes.

### Decisions
- **Search Ranking Approach**: Simple relevance tiers (Exact identifier 100 > Exact name 95 > Prefix identifier 85 > Prefix name 75 > Substring 50). At this scale (thousands of wholesale rows), plain SQL / in-memory querying is sufficient and avoids third-party paid search service dependencies (free-tier guardrail).
- **Global Command Palette**: Triggered via `Cmd+K` / `Ctrl+K` or topbar search box, ensuring mouse-free keyboard navigation.

### Key values for future steps
- Search Service: `SearchService` (`apps/api/app/services/search_service.py`)
- DI Factory: `get_search_service` in `apps/api/app/core/di.py`
- Endpoint: `GET /search?q={query}&limit={limit}` (Returns `SearchResponse`)
- Frontend Component: `SearchCommandPalette` (`apps/web/components/SearchCommandPalette.tsx`)

---

## Step 16.1 — Profitability & Inventory Turnover Analytics

**Timestamp:** 2026-08-24T14:56:00Z
**Status:** COMPLETE

### What was done
- **Profitability Analytics (`ProfitabilityService` + `GET /analytics/profitability`)**:
  - Implemented tier-adjusted gross margin calculations weighted by actual line item sales and quantities across customizable periods (`7d`, `30d`, `90d`, `12m`, `all`).
  - Supported multi-dimensional rollups by `product`, `category`, and `retailer`.
  - Margin formulas:
    - `Revenue = units_sold * actual_selling_price` (actual selling price from sales order line items incorporates retailer tier discounts: Gold, Silver, Bronze, Standard, Walk-in)
    - `Cost = units_sold * product.cost_price`
    - `Gross Margin (INR) = Revenue - Cost`
    - `Gross Margin (%) = (Gross Margin INR / Revenue) * 100` (if Revenue > 0 else 0.0%)
- **Inventory Turnover Analytics (`TurnoverService` + `GET /analytics/turnover`)**:
  - Implemented continuous velocity tracking sitting between normal sales movement and dead stock detection.
  - Turnover formulas:
    - `Average On-Hand = current_on_hand + (units_sold_in_period / 2.0)`
    - `Turnover Ratio = units_sold_in_period / Average On-Hand`
    - `Days of Stock on Hand = (Average On-Hand / units_sold_in_period) * days_in_period`
  - Turnover Banding Thresholds:
    - **Healthy**: `turnover_ratio >= 1.0` or (`days_of_stock <= 30.0` and `units_sold > 0`) -> Active inventory velocity.
    - **Slowing**: `0.3 <= turnover_ratio < 1.0` or (`30.0 < days_of_stock <= 90.0` and `units_sold > 0`) -> Early warning before dead stock.
    - **At-Risk**: `turnover_ratio < 0.3` or `days_of_stock > 90.0` or (`units_sold == 0` and `current_on_hand > 0`) -> Stagnant sitting capital.
- **Frontend Analytics Interfaces**:
  - `/admin/analytics/profitability`: Grouped view with Product/Category/Retailer dimension pills, time window tabs (7D/30D/90D/1Y/All), summary KPI cards, and sortable margin table with color-coded progress bars.
  - `/admin/analytics/turnover`: Ranked inventory turnover table (slowest first), velocity health status filter pills (Healthy, Slowing, At-Risk), KPI cards, and direct management links to `/admin/products`.
  - Added Profitability and Turnover links to `apps/web/lib/nav.ts`.
- **Verification & QA**:
  - Backend pytest suite: `apps/api/tests/test_profitability_and_turnover.py` (6/6 tests passing for hand-computed margin checks across tiers, category rollups, retailer rollups, and turnover velocity ranking). Full backend suite: 259/259 tests passing.
  - Frontend Vitest suite: `apps/web/lib/__tests__/profitability-turnover-ui.test.tsx` (4/4 tests passing). Full frontend suite: 42 test suites (176 tests) passing.
  - Next.js production build: Succeeded in 1.8s across all 45 routes with 0 errors.

### Decisions
- **Turnover as Continuous Early Warning**: While dead stock detection (Step 12.2) provides a binary flag (0 movement for 90+ days), inventory turnover ratio provides a continuous velocity signal (0.3 - 1.0x slowing, <0.3x at-risk) allowing proactive price adjustments or promotions weeks before dead stock lock-up occurs.
- **Tier-Adjusted Frozen Order Pricing**: Uses frozen sales order line item unit prices to compute actual gross profit captured across different buyer tiers.

### Key values for future steps
- Services: `ProfitabilityService` (`apps/api/app/services/profitability_service.py`), `TurnoverService` (`apps/api/app/services/turnover_service.py`)
- DI Factories: `get_profitability_service`, `get_turnover_service` in `apps/api/app/core/di.py`
- Endpoints:
  - `GET /analytics/profitability?group_by=product|category|retailer&period=30d`
  - `GET /analytics/turnover?period=30d`
- Pages: `/admin/analytics/profitability`, `/admin/analytics/turnover`

---

### Step 16.2 — Supplier & Retailer Performance + Warehouse Breakdown + Shrinkage Tracking

**Timestamp:** 2026-08-24T20:53:00Z
**Status:** COMPLETE

### What was done
- **Supplier Performance Analytics (`SupplierPerformanceService` + `GET /analytics/supplier-performance`)**:
  - Implemented supplier vendor scoring across on-time delivery rate, fulfillment accuracy, return rate, and total procurement spend.
  - Metrics:
    - `On-Time Delivery Rate = (On-time completed POs / Total completed POs) * 100%` (where `receipt_date <= po.expected_date`)
    - `Fulfillment Accuracy = (Total units received / Total units ordered) * 100%`
    - `Return Rate = (Total returned units from purchase returns / Total units received) * 100%`
    - `Quality Banding`: `excellent` (On-time ≥90%, Accuracy ≥95%, Return ≤2%), `good` (On-time ≥75%, Accuracy ≥85%, Return ≤5%), `needs_improvement` (otherwise).
- **Retailer Performance & Churn Risk (`RetailerPerformanceService` + `GET /analytics/retailer-performance`)**:
  - Implemented B2B retail buyer rankings by revenue, average order value (AOV), and ordering frequency trends.
  - Calculated ordering interval: `span_days / (order_count - 1)` (or fallback 30.0d).
  - **Churn-Risk Heuristic**: Flags `is_churn_risk = True` when `days_since_last_order > 2 * avg_order_gap_days` and `order_count >= 2`.
  - Trend Detection: `increasing` (recent order gap significantly shorter than historical average), `decreasing` (recent order gap longer than average), `steady` (consistent pace).
- **Warehouse Holdings & Throughput Breakdown (`WarehouseAnalyticsService` + `GET /analytics/warehouse-breakdown`)**:
  - Aggregated multi-facility stock valuation, total units stored, and 30-day inbound/outbound physical flow from stock movements ledger.
  - Calculated per-warehouse `valuation_share_pct = (warehouse_val / company_total_val) * 100%`.
- **Shrinkage & Damage Write-Off Tracking (`ShrinkageService` + `GET /analytics/shrinkage`)**:
  - Aggregated negative inventory adjustment movements (`type="adjustment"`, `quantity < 0`, reasons: damage, loss, theft, spoilage, discrepancy).
  - Calculated monetary write-off value: `abs(quantity) * product.cost_price`.
  - Calculated shrinkage rate: `(total_shrinkage_value / (total_stock_value + total_shrinkage_value)) * 100%`.
  - Supported grouping by `"product"` SKU and `"category"`, across time windows (7d, 30d, 90d, 12m, all).
- **Frontend Analytics Dashboards**:
  - `/admin/analytics/suppliers`: Vendor performance leaderboard, KPI cards, rating badges, search and sortable table.
  - `/admin/analytics/retailers`: Retailer revenue ranking, KPI cards, churn-risk warning chips, velocity trend indicators, and ledger navigation.
  - `/admin/analytics/warehouses`: Facility inventory holding cards, valuation share progress bars, and 30d flow metrics.
  - `/admin/analytics/shrinkage`: Damage write-off dashboard, product/category toggle, period filters, and loss share bars.
  - Updated navigation in `apps/web/lib/nav.ts` with dedicated "Analytics & Intelligence" section.
- **Verification & QA**:
  - Backend pytest suite: `apps/api/tests/test_performance_and_warehouse_analytics.py` (5/5 tests passing). Full backend suite: 264/264 tests passing.
  - Frontend Vitest suite: `apps/web/lib/__tests__/step-16-2-analytics-ui.test.tsx` (4/4 tests passing). Full frontend suite: 43 test suites (180 tests) passing.
  - Next.js production build: Succeeded across all 49 routes with 0 errors.

### Decisions
- **Churn-Risk Heuristic Protocol**: Recorded as a *tunable, explicitly-approximate signal — not a prediction, a flag worth a human look*. When a retailer's dormancy interval exceeds 2x their established cadence, a human sales rep should proactively reach out before the customer is lost.
- **Quality Banding for Suppliers**: Multi-variable grading prevents vendors with high fulfillment accuracy but chronic delivery delays from receiving top tier ratings.
- **Shrinkage Valuation at Cost Price**: Shrinkage reflects direct capital loss of procurement cost rather than unrealized potential retail margin.

### Key values for future steps
- Services:
  - `SupplierPerformanceService` (`apps/api/app/services/supplier_performance_service.py`)
  - `RetailerPerformanceService` (`apps/api/app/services/retailer_performance_service.py`)
  - `WarehouseAnalyticsService` (`apps/api/app/services/warehouse_analytics_service.py`)
  - `ShrinkageService` (`apps/api/app/services/shrinkage_service.py`)
- DI Factories: `get_supplier_performance_service`, `get_retailer_performance_service`, `get_warehouse_analytics_service`, `get_shrinkage_service` in `apps/api/app/core/di.py`
- Endpoints:
  - `GET /analytics/supplier-performance`
  - `GET /analytics/retailer-performance`
  - `GET /analytics/warehouse-breakdown`
  - `GET /analytics/shrinkage?group_by=product|category&period=30d`
- Pages: `/admin/analytics/suppliers`, `/admin/analytics/retailers`, `/admin/analytics/warehouses`, `/admin/analytics/shrinkage`

---

## Step 16.3 — Period Comparisons & Scheduled Owner Reports

**Timestamp:** 2026-08-24T23:00:00Z
**Status:** COMPLETE

### What was done
- **Core Period Comparison Engine (`ComparisonService`)**:
  - Implemented pure delta math (`compute_metric_delta`) supporting exact percentage deltas (`((current - prior) / prior) * 100`), absolute value deltas, polarity inversion for inverted metrics (e.g. shrinkage loss where drop = favorable), and robust handling of zero-prior / zero-current edge cases.
  - Implemented multi-window scorecard generation for 6 key wholesale metrics (`revenue`, `gross_margin`, `stock_valuation`, `turnover_rate`, `units_sold`, `shrinkage_value`) across 4 standard periods (`7d`, `30d`, `90d`, `12m`).
- **Automated Scheduled Weekly Owner Report Engine (`ScheduledReportService`)**:
  - Aggregates rolling weekly wholesale performance: total revenue & growth vs prior week, blended gross profit margin %, real-time stock holding valuation, 30-day inventory turnover velocity, safety-stock breach count, and overdue accounts receivable balance.
  - Compiles top 5 fast-moving revenue drivers, top slow-moving stagnant capital products, actionable operational highlights, and an executive narrative summary paragraph.
  - Implemented 1-page ReportLab PDF generator (`build_pdf`) with modern navy/slate styling, enterprise typography, structured metric tables, operational advisory callouts, and page budget discipline.
  - Implemented multi-channel dispatch (`dispatch_weekly_report` & `send_weekly_report_now`) delivering the report to all Owner/Manager profiles via Email (HTML body + PDF attachment), WhatsApp template message with key metric bullet points, and persistent In-App notifications.
- **Async Alert Scheduler Integration**:
  - Configured `AlertScheduler` with APScheduler Monday morning cron trigger (`CronTrigger(day_of_week="mon", hour=2, minute=30, timezone="UTC")`) invoking `weekly_report_factory` to automatically generate and dispatch executive reports at the start of each business week.
- **FastAPI Endpoints**:
  - `GET /analytics/period-comparisons?period=30d`: Scorecard of 6 key enterprise metrics with prior-period deltas.
  - `GET /analytics/weekly-report/latest`: Current compiled weekly executive summary and actionable highlights.
  - `GET /analytics/weekly-report/pdf`: Direct PDF binary stream download for owner executive reporting.
  - `POST /analytics/weekly-report/send-now`: Manual on-demand report generation and multi-channel dispatch.
- **Frontend UI & Components**:
  - `apps/web/components/analytics/ComparisonBadge.tsx`: Reusable micro-component rendering trend indicators (▲, ▼, —), emerald/rose/zinc coloring with polarity inversion (`higherIsBetter`), prior value tooltips, and custom size/formatting props.
  - `apps/web/app/admin/analytics/page.tsx`: Central Analytics & BI Landing Hub featuring:
    - Real-time period comparison selector (`7D`, `30D`, `90D`, `12M`).
    - 6 Live enterprise KPI cards with `ComparisonBadge`.
    - Weekly Executive Briefing card with executive narrative, actionable alerts feed, fast movers, and slow movers.
    - PDF download and "Send Report Now" dispatch actions with toast notifications.
    - Specialized navigation directory with direct links to all 8 BI modules.
  - Attached `ComparisonBadge` to KPI metric cards in `/admin/analytics/profitability`.
- **Quality Assurance & Verification**:
  - Backend pytest suite: `apps/api/tests/test_period_comparisons_and_scheduled_reports.py` (5/5 tests passing). Full backend suite: 269/269 tests passing.
  - Frontend Vitest suite: `apps/web/lib/__tests__/step-16-3-comparison-and-reports-ui.test.tsx` (11/11 tests passing). Full frontend suite: 44 test suites (191 tests) passing.
  - Next.js production build: Succeeded across all 50 routes with 0 errors.

### Decisions
- **Zero-Prior Delta Math**: When prior value is 0 and current > 0, delta percentage is set to `+100.0%` with clear string formatting, avoiding `DivisionByZero` runtime errors.
- **ReportLab Flowable 1-Page Layout**: Enforced strict vertical spacing (`Spacer(1, 4)` to `Spacer(1, 8)`) and table paddings to guarantee the weekly executive report fits cleanly on a single high-impact page without page overflow.
- **Idempotent Multi-Channel Dispatch**: `send-now` generates identical data and narrative payload to the scheduled cron job, ensuring deterministic owner reporting across scheduled and manual triggers.

### Key values for future steps
- Services:
  - `ComparisonService` (`apps/api/app/services/comparison_service.py`)
  - `ScheduledReportService` (`apps/api/app/services/scheduled_report_service.py`)
- DI Factories: `get_comparison_service`, `get_scheduled_report_service`, `weekly_report_factory` in `apps/api/app/core/di.py`
- Endpoints:
  - `GET /analytics/period-comparisons`
  - `GET /analytics/weekly-report/latest`
  - `GET /analytics/weekly-report/pdf`
  - `POST /analytics/weekly-report/send-now`
- UI Component: `ComparisonBadge` (`apps/web/components/analytics/ComparisonBadge.tsx`)
- Central Hub Page: `/admin/analytics` (`apps/web/app/admin/analytics/page.tsx`)
- Cron Schedule: Every Monday at 02:30 UTC via `AlertScheduler`

---

## Step 17.1 — Google Places Lead Scanner (schema + scheduled scan)
**Timestamp:** 2026-08-25T01:45:00Z
**Status:** COMPLETE

### What was done
- **Database Schema & Models (`leads`, `lead_scan_runs`)**:
  - Created `Lead` and `LeadScanRun` SQLAlchemy models with `LeadCategoryEnum` (`gruh_udyog`, `snack_store`, `grocery_kirana`, `other`), unique `place_id` index, `is_new` boolean default, `contacted` tracking, `contact_notes`, and optional `converted_retailer_id` FK.
  - Created Alembic migration `0007_leads_and_scan_runs.py` and registered models in `app.models.__init__.py`.
- **Repository Abstraction Layer (DIP)**:
  - Created `LeadRepositoryInterface` protocol defining methods: `get_lead_by_place_id`, `get_all_place_ids`, `create_lead`, `update_lead`, `list_leads`, `create_scan_run`, `list_scan_runs`, and `mark_lead_contacted`.
  - Implemented `SqlAlchemyLeadRepository` with query optimizations and `InMemoryLeadRepository` for zero-IO testing.
- **Google Places Lead Scanner Engine (`GooglePlacesLeadService`)**:
  - Implemented `scan(center_lat, center_lng, radius_km)` querying Google Places API (New v1) across text searches (`gruh udyog`, `home industry food`, `kirana store`, `grocery store`, `namkeen shop`, `snacks shop`, `farsan shop`, `general store`) and nearby searches (`grocery_or_supermarket`, `convenience_store`).
  - Implemented idempotent first-seen-ever upsert logic: newly discovered `place_id` records are created with `is_new=True`; previously seen leads update location/contact details while `is_new` is strictly preserved (never re-flagged).
  - Wired notification dispatch via `NotificationService` (In-App, WhatsApp, Email) when `new_count > 0` to notify business owners to view newly opened leads.
- **Background Scheduler Integration (APScheduler)**:
  - Configured `AlertScheduler` with weekly lead scan cron trigger running Sundays at 03:00 UTC (configurable via `LEAD_SCAN_INTERVAL_DAYS`, default 7 days) around configured coordinates (`23.01185905490891, 72.53806563827865`, radius 15km).
- **FastAPI Endpoints (`app/api/routers/leads.py`)**:
  - `POST /leads/scan-now`: Immediate on-demand scan guarded by `leads.scan` permission.
  - `GET /leads`: Paginated, filterable lead list guarded by `leads.view` permission.
  - `PATCH /leads/{id}/contacted`: Update contact status & notes guarded by `leads.manage` permission.
  - `GET /leads/scan-history`: Scan audit history list guarded by `leads.view` permission.
- **Testing & Verification**:
  - Pytest suite: `apps/api/tests/test_leads_scanner.py` (21/21 tests passing).
  - Full backend test suite: 290/290 tests passing.
  - Full frontend Vitest suite: 44/44 test files (191 tests) passing.
  - Next.js production build: Succeeded across all 50 routes with 0 errors.

### Decisions
- **Definition of 'New'**: 'New' is strictly defined as *never seen in our database before*, rather than recently opened in physical reality. This distinction accounts for Google's indexing latency and prevents false assumptions.
- **Scan Keywords & Types Verbatim List**:
  - Keywords: `gruh udyog`, `home industry food`, `kirana store`, `grocery store`, `namkeen shop`, `snacks shop`, `farsan shop`, `general store`
  - Nearby types: `grocery_or_supermarket`, `convenience_store`
  - Cadence: Weekly default (Sundays 03:00 UTC), configurable via `LEAD_SCAN_INTERVAL_DAYS`.
- **Idempotent Multi-Scan Protection**: Existing leads update mutable details (name, phone, address, location coordinates, Google Maps URI) on subsequent scans, but `is_new` is never re-armed, ensuring zero redundant notification spam.

### Key values for future steps
- Models: `Lead`, `LeadCategoryEnum`, `LeadScanRun` (`apps/api/app/models/lead.py`)
- Service: `GooglePlacesLeadService` (`apps/api/app/services/places_lead_scanner.py`)
- Repository Interface: `LeadRepositoryInterface` (`apps/api/app/repositories/interfaces/lead_repository.py`)
- Repositories: `SqlAlchemyLeadRepository`, `InMemoryLeadRepository` (`apps/api/app/repositories/impl/lead_repository.py`)
- DI Factories: `get_lead_repository`, `get_lead_service` in `apps/api/app/core/di.py`
- Endpoints:
  - `POST /leads/scan-now`
  - `GET /leads`
  - `PATCH /leads/{id}/contacted`
  - `GET /leads/scan-history`
- Env Vars: `GOOGLE_PLACES_API_KEY`, `LEAD_SCAN_INTERVAL_DAYS`, `LEAD_SCAN_CENTER_LAT`, `LEAD_SCAN_CENTER_LNG`, `LEAD_SCAN_RADIUS_KM`

---

## Step 17.2 — Interactive Lead Map (existing shops + highlighted new ones)
**Timestamp:** 2026-08-25T02:00:00Z
**Status:** COMPLETE

### What was done
- **Backend API Query Expansion (`apps/api/app/api/routers/leads.py` & Repositories)**:
  - Extended `LeadRepositoryInterface`, `SqlAlchemyLeadRepository`, and `InMemoryLeadRepository` to support full-text search (`search` across lead name and address) and geographic bounding box filters (`min_lat`, `max_lat`, `min_lng`, `max_lng`).
  - Updated `GET /leads` endpoint to accept `search`, `min_lat`, `max_lat`, `min_lng`, `max_lng` query parameters.
  - Added unit and endpoint tests verifying search and bounding box queries in `apps/api/tests/test_leads_scanner.py` (23/23 tests passing).
- **Frontend Interactive Map & Discovery Components (`apps/web/components/leads/`)**:
  - `LeadInfoWindow.tsx`: Detail glass card displaying shop name, category badge, glowing NEW badge, address, direct phone link (`tel:` protocol), directions link to Google Maps, and inline form for recording contact outcome notes.
  - `LeadMap.tsx`: Google Maps JavaScript API embed (free-tier guardrails) customized with WareFlow dark luxury map styling, custom SVG category pins (Amber `#F59E0B` for Gruh Udyog, Rose `#F43F5E` for Snack Store, Emerald `#10B981` for Kirana/Grocery, Violet `#8B5CF6` for Retail/Other), glowing radar pulse rings for `is_new=true` leads, central warehouse hub circle (15km radius), and accessible interactive spatial canvas schematic fallback for offline/test environments.
  - `LeadFilterSidebar.tsx`: Search input, category filter tabs with dynamic counts, 'New Shops Only' isolation toggle switch, contacted filter pills, and scrollable cards synchronized with map pin selection.
  - `LeadDiscoveryView.tsx`: Master coordinator with top telemetry KPI cards (Total Discovered, New Shops, Outreach Pending, Contacted Coverage), mobile map/list switcher, on-demand scan modal triggering `POST /leads/scan-now`, and floating `LeadInfoWindow` overlay.
- **Pages & Navigation**:
  - `apps/web/app/admin/leads/map/page.tsx`: Production lead discovery map page with `PageHeader` and `Growth Radar` badge.
  - `apps/web/app/admin/leads/page.tsx`: Redirect route pointing to `/admin/leads/map`.
  - `apps/web/lib/nav.ts`: Added `Lead Discovery Map` (`/admin/leads/map`) to `NAVIGATION_SECTIONS`.
  - `apps/web/.env.example`: Added `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`.
- **Testing & Verification**:
  - Created `apps/web/lib/__tests__/lead-map-ui.test.tsx` (7/7 tests passing) testing map pins, sidebar mirroring, filter toggles, search, info window, `tel:`/directions links, and scan trigger.
  - Full frontend Vitest suite: 45/45 test files (198 tests) passing.
  - Full backend pytest suite: 292/292 tests passing.
  - Next.js production build: Succeeded across all 52 routes with 0 errors.

### Decisions
- **Spatial Fallback Schematic**: Included an interactive SVG/HTML canvas schematic fallback inside `LeadMap.tsx` when `window.google` is absent or in test environments. This guarantees 100% deterministic test coverage and graceful offline user experience.
- **Direct Phone Protocol Link**: Used standard `<a href="tel:{phone}">` enabling 1-tap direct dialing on mobile devices and VoIP softphone integration on desktop.
- **Client-Side Free-Tier Guardrails**: Google Maps JavaScript API runs client-side within the free tier $200 monthly credit pool shared with Places API.

### Key values for future steps
- Route: `/admin/leads/map`
- Components: `LeadDiscoveryView`, `LeadMap`, `LeadInfoWindow`, `LeadFilterSidebar` in `apps/web/components/leads/`
- Navigation: `Lead Discovery Map` (`/admin/leads/map`) under Wholesale Operations in `apps/web/lib/nav.ts`
- Client Key: `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`

---

## Step 17.3 — Lead Contact Tracking & Convert-to-Retailer
**Timestamp:** 2026-08-25T02:05:00Z
**Status:** COMPLETE

### What was done
- **Backend API & Repositories (`apps/api/`)**:
  - `LeadRepositoryInterface`, `SqlAlchemyLeadRepository`, and `InMemoryLeadRepository`:
    - Updated `mark_lead_contacted(lead_id: str, notes: str | None = None, contacted: bool = True)` to immediately clear `is_new = False` upon being marked contacted.
    - Added `get_lead_by_id(lead_id: str) -> Lead | None` and `link_converted_retailer(lead_id: str, retailer_id: str) -> Lead | None` which sets `converted_retailer_id`, `contacted = True`, and `is_new = False`.
  - Pydantic Schemas (`apps/api/app/schemas/leads.py`):
    - Added `ConvertLeadToRetailerRequest` (name, contact_person, phone, email, address, gstin, pricing_tier, credit_limit) and `ConvertLeadToRetailerResponse` (message, lead, retailer).
    - Updated `MarkContactedRequest` with optional `contacted: bool = True` and `notes: str | None`.
  - Router Endpoints (`apps/api/app/api/routers/leads.py`):
    - `PATCH /leads/{lead_id}` and `PATCH /leads/{lead_id}/contacted`: updates contact status, notes, and clears `is_new` flag.
    - `POST /leads/{lead_id}/convert-to-retailer`: validates lead is not already converted (HTTP 400 if already converted), invokes `RetailerService.create_retailer` with pre-filled details (reusing Phase 7 wholesale account registration), links `converted_retailer_id` to lead, and marks `contacted = True` and `is_new = False`.
  - Pytest Suite (`apps/api/tests/test_leads_scanner.py`):
    - Added 4 new test cases covering clearing `is_new` when contacted, successful conversion to retailer with pre-filled fields, blocking duplicate conversions with 400 error, and 404 handling.
    - Total 27/27 lead tests passing (296/296 full backend suite passing).
- **Frontend Lead Management & Conversion UI (`apps/web/components/leads/`)**:
  - `ConvertToRetailerModal.tsx`: Modern glass modal dialog pre-filling Business Name, Phone, and Address from lead, with configurable fields for Contact Person, Email, GSTIN, Pricing Tier (Standard/Silver/Gold), and Credit Limit (INR), sending `POST /leads/{id}/convert-to-retailer`.
  - `LeadInfoWindow.tsx`:
    - Added "Convert to Wholesale Retailer" button triggering convert modal.
    - Added "Converted Retailer" badge and direct link button "View Retailer Account" (`/admin/retailers/{id}/ledger` or `/admin/retailers`) when already converted.
    - Added immediate clearing of `is_new` highlight upon contact update.
  - `LeadFilterSidebar.tsx`:
    - Added Converted status filter pill (`All • Pending • Contacted • Converted`) with dynamic count.
    - Rendered Converted Retailer badge on converted lead cards in sidebar list.
  - `LeadDiscoveryView.tsx`:
    - Added Converted Retailers KPI metric card to top telemetry strip.
    - Integrated `ConvertToRetailerModal` and state synchronization on conversion and contact.
  - Vitest Suite (`apps/web/lib/__tests__/lead-map-ui.test.tsx`):
    - Added comprehensive tests for Convert button, Converted Retailer badge & ledger link, `ConvertToRetailerModal` form submission, and Converted filter tab.
    - Total 11/11 lead UI tests passing (202/202 full frontend vitest suite passing).
- **Production Build**:
  - `pnpm --filter web build` succeeded across all 52 routes with 0 errors.

### Decisions
- **Unified Conversion Pipeline**: Reused Phase 7's `RetailerService.create_retailer` within `POST /leads/{id}/convert-to-retailer`, ensuring all validation (pricing tiers, GSTIN format, initial credit limits) and audit logs are consistently applied to converted leads.
- **Attention Management**: Marking a lead contacted or converted automatically sets `is_new = False`, immediately removing the pulsing radar glow and "New" badge so sales reps focus attention on uncontacted prospects.
- **Duplicate Conversion Guardrail**: Once converted, a lead cannot be converted again (prevented at both backend router level with 400 error and frontend UI with disabled state and direct link to the resulting retailer account).

### Key values for future steps
- Lead Converted Retailer Field: `leads.converted_retailer_id`
- Conversion Endpoint: `POST /leads/{lead_id}/convert-to-retailer`
- Contact Tracking Endpoint: `PATCH /leads/{lead_id}/contacted` or `PATCH /leads/{lead_id}`
- Conversion UI: `<ConvertToRetailerModal>` in `apps/web/components/leads/ConvertToRetailerModal.tsx`

---

## Step 18.1 — Barcode/QR Generation & Camera Scanning

**Timestamp:** 2026-08-25T04:45:00Z
**Status:** COMPLETE

### What was done

- **Backend Barcode & QR Engine (`apps/api/app/services/barcode_service.py`)**:
  - Implemented GS1 modulo-10 EAN-13 check digit calculator: `calculate_ean13_checksum(digits12: str) -> int`.
  - Implemented internal EAN-13 generator: `generate_internal_ean13(prefix="20", sequence_id=None) -> str` using restricted circulation prefix `20` + random/sequence 10 digits + modulo-10 checksum.
  - Implemented `BarcodeService.render_barcode_png(code: str, options=None) -> bytes` rendering high-resolution EAN-13 (with Code128 fallback for arbitrary alphanumeric SKUs) in-memory using `python-barcode` + Pillow `ImageWriter`.
  - Implemented `BarcodeService.render_qr_code_png(data: str, box_size=8, border=2) -> bytes` rendering crisp 2D matrix QR codes.
- **Product Model & Repository Barcode Resolution**:
  - Added `get_by_barcode(barcode: str) -> Product | None` in `ProductRepositoryInterface`, `InMemoryProductRepository`, and `SqlAlchemyProductRepository`.
  - Updated `ProductService.create_product`: if `payload.barcode` is omitted or empty, auto-generates a valid internal 13-digit EAN-13 barcode (`20...`).
  - Added `ProductService.get_product_by_barcode(barcode: str)` resolving product by barcode with fallback lookup against SKU.
  - Added `ProductService.get_product_barcode_image(product_id: str)` and `get_product_qr_image(product_id: str)` returning PNG byte streams.
- **FastAPI Endpoints (`apps/api/app/api/routers/products.py`)**:
  - `GET /products/by-barcode/{barcode}`: Instantly resolves and returns product schema for scanner lookups.
  - `GET /products/{id}/barcode.png`: Returns high-resolution scannable PNG barcode image with `image/png` content-type.
  - `GET /products/{id}/qr.png`: Returns high-resolution 2D matrix QR code PNG image with `image/png` content-type.
- **Comprehensive Backend Pytest Suite (`apps/api/tests/test_barcodes.py`)**:
  - Added 14 unit and integration tests verifying EAN-13 check digit calculation, internal barcode structure, PNG image headers (`\x89PNG`), Code128 fallback, auto-generation on creation, and all 3 new endpoints.
  - Full backend pytest suite: **310/310 tests passing**.
- **Frontend Camera Scanning & Label Generation Components (`apps/web/components/barcode/`)**:
  - `BarcodeScannerModal.tsx`:
    - Integrated client-side scanner using `html5-qrcode` (`Html5Qrcode`).
    - Triple-mode interface: Live camera feed with laser reticle animation & camera flip toggle, image file upload scanner (`scanFile`), and manual barcode/SKU entry.
    - Synthesized Web Audio API scan confirmation beep on detection for warehouse floor feedback.
    - Instant API resolution against `/products/by-barcode/{code}` with matched product banner.
  - `ProductLabelSheetModal.tsx`:
    - Multi-label sheet printing engine supporting standard formats (A4 - 24 labels 3×8 grid, A4 - 14 labels 2×7 grid, Single Sticker 50×30mm).
    - Configurable label count (1–96), price inclusion toggle, SKU inclusion toggle, and 1D Barcode vs 2D QR switcher.
    - Crisp `@media print` layout preventing cuts and ensuring monochrome contrast.
  - `ProductBarcodeCard.tsx`:
    - Interactive 1D Barcode and 2D QR preview card with one-click PNG downloads, copy code button, and print label sheet trigger.
- **Integrated Warehouse Floor Scanning Across Views**:
  - Product Catalog (`/admin/products`): Added topbar "Scan Barcode" button, "Label" action button in table rows, and inline "Scan via Camera" button for product creation/edit form.
  - Inventory Overview (`/admin/inventory`): Added "Scan Barcode" button next to Excel export to instantly filter and highlight matching stock items.
  - Stock Adjustment (`/admin/stock/adjust`): Added "Scan Barcode" button next to Product dropdown to instantly select target damaged/audited product.
  - Stock Transfer (`/admin/stock/transfer`): Added "Scan Barcode" button next to Product select to instantly locate source product batches.
- **Frontend Vitest Suite & Build**:
  - `apps/web/lib/__tests__/barcode-scanner.test.tsx`: Tested mode switching, manual input lookup, cancel handlers, label sheet rendering, and barcode card switching.
  - Full frontend vitest suite: **209/209 tests passing**.
  - Production build: `pnpm --filter web build` completed cleanly across all 52 routes with 0 errors.

### Decisions

- **GS1 Restricted Circulation Prefix (20)**: Internal warehouse barcodes use GS1 prefix `20` reserved globally for internal enterprise use. This prevents collision with commercial manufacturer EAN-13 prefixes (such as Indian `890` prefix).
- **Graceful Code128 Fallback**: If a product has an alphanumeric SKU instead of a 12/13-digit numeric code, `render_barcode_png` transparently falls back to Code128 format rather than crashing.
- **Pure Client-Side Zero-Cost Camera Scanning**: Uses `html5-qrcode` executing directly in the browser with Web Workers, requiring 0 external cloud scanning APIs and remaining 100% free-tier compliant.
- **In-Memory Image Streaming**: Barcode and QR code PNGs are rendered directly to memory buffers using `io.BytesIO` and streamed via FastAPI `Response(content=..., media_type="image/png")` without creating temporary files on disk.

### Key values for future steps

- Barcode Service: `apps/api/app/services/barcode_service.py`
- Barcode Lookup API: `GET /products/by-barcode/{barcode}`
- Barcode PNG Render API: `GET /products/{id}/barcode.png`
- QR Code PNG Render API: `GET /products/{id}/qr.png`
- Scanner Component: `<BarcodeScannerModal>` in `apps/web/components/barcode/BarcodeScannerModal.tsx`
- Label Sheet Modal: `<ProductLabelSheetModal>` in `apps/web/components/barcode/ProductLabelSheetModal.tsx`
- Barcode Card Component: `<ProductBarcodeCard>` in `apps/web/components/barcode/ProductBarcodeCard.tsx`

---

## Step 18.2 — Bulk CSV Import / Export
**Timestamp:** 2026-08-25T04:45:00Z
**Status:** COMPLETE

### What was done
- Built `ProductImportService` in `apps/api/app/services/import_service.py` implementing:
  - Header normalization and parsing for CSV files with line-level index tracking.
  - Pydantic validation via `ProductImportRow` and dry-run preview classification (`create`, `update`, `reject`).
  - Actionable error reporting (missing SKU/name, invalid/negative wholesale & cost prices, malformed thresholds).
  - Transactional upsert execution by SKU with auto-creation of missing categories, auto EAN-13 generation for blank barcodes, and audit log generation (`product_created`, `product_updated`).
  - Standard CSV template generation with FMCG wholesale product examples.
  - Full catalog export to CSV with UTF-8 BOM encoding.
- Registered `get_product_import_service()` in `apps/api/app/core/di.py`.
- Added FastAPI endpoints in `apps/api/app/api/routers/products.py`:
  - `POST /products/import?dry_run=true|false`: Multipart CSV upload with dry-run preview and upsert commit modes.
  - `GET /products/export.csv`: Full catalog CSV export.
  - `GET /products/template.csv`: Standardized sample CSV template download.
- Created Next.js Bulk Import interface in `apps/web/app/admin/products/import/page.tsx`:
  - Drag-and-drop CSV dropzone with format validation.
  - Summary KPI cards (Total Rows, Creates, Updates, Rejections).
  - Filterable dry-run validation preview table with color-coded badges, error callouts, and line numbers.
  - Confirm & commit workflow with user confirmation and post-commit success overview.
  - Download template and export catalog buttons wired to `apiClient.downloadBlob`.
- Added "Import / Export CSV" button in `/admin/products` top action bar.
- Tested with 10 unit and API integration tests in `apps/api/tests/test_csv_import_export.py` and 5 Vitest tests in `apps/web/lib/__tests__/product-import-ui.test.tsx`.
- Verified all 320 backend pytest tests passing, all 214 frontend vitest tests passing (47 test files), and 53 Next.js routes built cleanly.

### Decisions
- **Preview-Before-Commit Pattern for Bulk Operations**: All bulk catalog and operational CSV imports execute a dry-run validation pass returning line-by-line classification (`create`, `update`, `reject`) with explicit error reasons before committing changes to the database.
- **Idempotent Upsert-by-SKU**: SKU acts as the natural key for upserting products. Repeatedly importing the same CSV file updates existing records safely without duplicating records or throwing conflict errors.
- **On-the-fly Category & Barcode Handling**: CSV rows with new category names automatically create the category record in the repository, and rows with blank barcodes auto-generate internal enterprise EAN-13 barcodes.

### Key values for future steps
- Product Import Service: `apps/api/app/services/import_service.py`
- Product Import API: `POST /products/import?dry_run=true|false`
- Product Export API: `GET /products/export.csv`
- Product CSV Template API: `GET /products/template.csv`
- Web Import Page: `/admin/products/import` (`apps/web/app/admin/products/import/page.tsx`)
- Required CSV Columns: `sku`, `name`, `wholesale_price`
- Optional CSV Columns: `cost_price`, `category`, `unit`, `hsn_code`, `barcode`, `reorder_point`, `reorder_qty`, `description`

---

## Step 19.1 — PWA Shell, Caching & Local Queue
**Timestamp:** 2026-08-25T04:53:00Z
**Status:** COMPLETE

### What was done
- Built an installable PWA application shell:
  - Created Web App Manifests in `apps/web/public/manifest.json` and `apps/web/app/manifest.ts` declaring standalone display, orientation, theme colors (`#8b5cf6`, `#090d16`), and app icons.
  - Hand-rolled Service Worker in `apps/web/public/sw.js` implementing:
    - Pre-caching static app shell (`/offline`, `/dashboard`, `/admin/inventory`, `/admin/products`, `/admin/stock/adjust`, `/admin/stock/transfer`).
    - Cache-first strategy for static assets (`/_next/static/`, images, fonts, SVGs).
    - Stale-while-revalidate strategy for catalog and stock overview GET requests (`/products`, `/stock`, `/categories`) so warehouse staff can browse inventory during WiFi dead spots.
    - Navigation fallback to `/offline` fallback page.
  - Created glassmorphic offline fallback page in `apps/web/app/offline/page.tsx` with cached operations overview and retry connection button.
- Implemented IndexedDB-backed offline action queue in `apps/web/lib/offline-queue.ts` via `idb`:
  - `enqueueOfflineAction`, `getAllQueueItems`, `getPendingQueueCount`, `removeQueueItem`, `resolveConflict`, `clearCompletedItems`.
  - `flushOfflineQueue`: Dispatches pending items in FIFO order, detects 409/422 balance and conflict responses from server, and marks items with `conflict` status and `conflict_details`.
- Built PWA UI components:
  - `apps/web/components/pwa/OfflineBanner.tsx`: Floating glass banner displaying real-time offline status, pending count, and drawer trigger.
  - `apps/web/components/pwa/SyncQueueModal.tsx`: Real-time sync modal with pending/synced/conflict stats, "Sync Now" button, and interactive conflict cards offering "Discard" or "Re-apply Against Current Stock".
  - `apps/web/components/pwa/PwaProvider.tsx`: Global context managing service worker lifecycle, window online/offline listeners, auto-sync on reconnection, and global modal state.
  - Wrapped `RootLayout` with `<PwaProvider>` in `apps/web/app/layout.tsx`.
  - Added Sync Queue indicator button with live counter badge to `apps/web/components/Topbar.tsx`.
- Tested with 5 queue engine unit tests in `apps/web/lib/__tests__/offline-queue.test.ts` and 4 UI tests in `apps/web/lib/__tests__/pwa-ui.test.tsx`.
- Verified all 320 backend pytest tests passing, all 223 frontend vitest tests passing across 49 test files, and all 55 Next.js routes built cleanly.

### Decisions
- **Deliberate Offline Scope Boundary**: Offline queuing is strictly scoped to high-velocity floor operations:
  1. `stock_adjustment` (`POST /stock/adjustments`)
  2. `stock_transfer` (`POST /stock/transfers`)
  3. `barcode_scan_lookup` (cached product lookups & scan events)
  Financial and multi-user transactional flows (`sales_order_confirmed`, `receive_po`, `invoice_generation`, `payments`, `credit_limit_updates`) remain strictly online-only to prevent credit over-extension, duplicate sequential GST tax invoice numbering, and multi-user batch deduction race conditions.
- **Explicit Conflict Surfacing**: When an offline action encounters server-side batch balance changes or validation rejections, sync flags the item as `conflict` and surfaces an interactive conflict card rather than silently dropping or overwriting data.
- **Stale-While-Revalidate Caching for Floor Lookups**: Staff walking into deep warehouse dead spots can instantly browse cached product prices, SKUs, barcodes, and stock levels without spinning loaders.

### Key values for future steps
- PWA Service Worker: `apps/web/public/sw.js`
- Web Manifest: `apps/web/public/manifest.json`, `apps/web/app/manifest.ts`
- Offline Fallback Page: `/offline` (`apps/web/app/offline/page.tsx`)
- Offline Queue Engine: `apps/web/lib/offline-queue.ts`
- Sync Modal: `<SyncQueueModal>` in `apps/web/components/pwa/SyncQueueModal.tsx`
- Offline Banner: `<OfflineBanner>` in `apps/web/components/pwa/OfflineBanner.tsx`
- PWA Context: `usePwa` from `apps/web/components/pwa/PwaProvider.tsx`

---

## Step 20.1 — Award-Benchmark Screen Audit (Design · Usability · Creativity · Content)
**Timestamp:** 2026-08-25T05:28:00Z
**Status:** COMPLETE

### What was done
- Conducted a comprehensive award-benchmark evaluation across all 48 active production routes defined in `docs/SITEMAP.md`.
- Scored each screen across all 4 official Awwwards / FWA evaluation pillars: Design (1–10), Usability (1–10), Creativity (1–10), and Content (1–10).
- Cross-referenced side-by-side against three tier-1 B2B / SaaS benchmarks:
  - **Linear.app**: Obsidian canvas, subtle 1px border refractions, and instant keyboard-first command palette (`Cmd+K`).
  - **Stripe Dashboard**: Monospaced tabular alignment (`font-mono tabular-nums`) for currency and quantities, clear badge taxonomy, multi-status filters, and CSV/PDF tooling.
  - **Raycast / Attio**: Specular liquid glass panels (`backdrop-blur-2xl`), multi-sensory feedback (scanner audio beeps), and non-destructive offline conflict resolution.
- Compiled the complete evaluation matrix in `docs/UX_AUDIT.md`.
- Formulated an actionable punch list for Step 20.2 (Visual Polish & Typography Alignment) and Step 20.3 (Micro-Interactions & Performance Optimization).
- Updated `codebase_audit.md` with UX Audit baseline notes.

### Decisions
- **Strict 4-Pillar Evaluation Standard**: Every view must satisfy the same criteria evaluated by Awwwards/FWA juries rather than subjective aesthetic impressions.
- **Zero Below-7 Threshold Baseline**: No screen scored below the 7.0 baseline; 29 screens achieved high excellence scores (>= 8.8).
- **Targeted Micro-Polish Punch List**: Step 20.2 and 20.3 will execute focused improvements on tabular numeric alignment (`font-mono tabular-nums`), contextual empty state illustrations, and entrance animation choreography.

### Key values for future steps
- UX Audit Document: `docs/UX_AUDIT.md`
- Master Sitemap: `docs/SITEMAP.md`
- Visual Polish Targets: Tabular figures in `DataTable.tsx`, empty states across `/admin/*`, and hover sheen performance.






























