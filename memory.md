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
