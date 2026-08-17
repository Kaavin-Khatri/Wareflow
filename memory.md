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
- All __init__.py files for SOLID layer packages
- .gitignore, apps/web/.env.example, apps/api/.env.example
- memory.md, codebase_audit.md
