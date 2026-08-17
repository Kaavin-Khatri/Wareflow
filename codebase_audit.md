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

| Layer              | Technology           | Version   |
| ------------------ | -------------------- | --------- |
| Frontend framework | Next.js (App Router) | 16.3.1    |
| Frontend language  | TypeScript           | 5.9.3     |
| UI library         | React                | 19.2.8    |
| CSS framework      | Tailwind CSS         | 4.3.3     |
| Test Runner (web)  | Vitest               | 4.1.10    |
| Backend framework  | FastAPI              | >=0.115.0 |
| Backend language   | Python               | 3.14.6    |
| ORM                | SQLAlchemy           | >=2.0.0   |
| Migrations         | Alembic              | >=1.13.0  |
| Validation         | Pydantic             | >=2.0.0   |
| Test Runner (api)  | Pytest + pytest-cov  | >=8.0.0   |

## Services

| Service  | Role                              | Project/ID           | Region                 | Tier            | Connection Mode                                                                                 |
| -------- | --------------------------------- | -------------------- | ---------------------- | --------------- | ----------------------------------------------------------------------------------------------- |
| Supabase | Postgres DB (system of record)    | yappumzftktliybmztgg | Seoul (ap-northeast-2) | Free (t3a.nano) | **Split**: Port 6543 (transaction pooler) at runtime, Port 5432 (session pooler) for migrations |
| Firebase | Auth (Google/Apple/Email)         | wareflow-d17a4       | —                      | Free (Spark)    | Client SDK + Server Admin SDK                                                                   |
| Resend   | Email alerts (low-stock, reorder) | —                    | —                      | Free (3k/mo)    | HTTPS API                                                                                       |
| Groq     | LLM API (AI features)             | —                    | —                      | Free            | HTTPS API                                                                                       |
| Vercel   | Frontend hosting (Next.js)        | pending              | —                      | Free (Hobby)    | —                                                                                               |
| Render   | Backend hosting (FastAPI)         | pending              | —                      | Free            | —                                                                                               |

### Supabase Connection Modes Explained:

1. **Runtime (`DATABASE_URL`, Port 6543)**: Connects to Supavisor transaction pooler with SQLAlchemy `NullPool`. Because Supabase handles pooling on the server, client-side pooling causes double-pooling and connection limits exhaustion. `NullPool` opens connections on demand and returns them immediately.
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
| `ALLOWED_ORIGINS`                   | CORS allowed origins list/csv                 | No          |
| `DATABASE_URL`                      | Supabase transaction pooler (port 6543)       | No (secret) |
| `DIRECT_DATABASE_URL`               | Supabase migration session pooler (port 5432) | No (secret) |
| `SUPABASE_URL`                      | Supabase project URL                          | No          |
| `SUPABASE_SERVICE_ROLE_KEY`         | Supabase admin secret key                     | No (secret) |
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Path to Firebase Admin SDK JSON               | No (secret) |
| `RESEND_API_KEY`                    | Resend email API key                          | No (secret) |
| `GROQ_API_KEY`                      | Groq LLM API key                              | No (secret) |

## File Tree

```
wareflow/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI pipeline (lint, test, build)
├── package.json                    # Root monorepo config (pnpm workspaces)
├── pnpm-workspace.yaml             # Workspace definition
├── .prettierrc                     # Prettier config (line-length 100)
├── .prettierignore                 # Prettier ignore (skip api/, lockfiles)
├── .gitignore                      # Git ignore rules
├── docker-compose.yml              # Optional local Postgres (port 5433)
├── README.md                       # Quick-start guide
├── memory.md                       # Append-only project history
├── codebase_audit.md               # Living system state (this file)
├── apps/
│   ├── web/                        # Next.js frontend (:3000)
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.ts
│   │   ├── postcss.config.mjs
│   │   ├── eslint.config.mjs       # ESLint + eslint-config-prettier
│   │   ├── vitest.config.mts       # Vitest unit test configuration
│   │   ├── .env.example
│   │   ├── lib/
│   │   │   ├── api-client.ts       # Typed fetch wrapper with ApiError
│   │   │   └── __tests__/
│   │   │       └── api-client.test.ts
│   │   └── app/                    # App Router pages
│   │       ├── layout.tsx
│   │       ├── page.tsx
│   │       ├── globals.css
│   │       └── debug/              # Temporary handshake probe
│   │           └── page.tsx
│   └── api/                        # FastAPI backend (:8000)
│       ├── alembic.ini             # Alembic migration configuration
│       ├── alembic/                # Migration scripts
│       │   ├── env.py              # Migration runner with DIRECT_DATABASE_URL
│       │   ├── script.py.mako
│       │   └── versions/
│       │       ├── 0001_initial_schema_probe.py
│       │       └── 0002_core_wholesale_schema.py
│       ├── requirements.txt
│       ├── requirements-dev.txt    # ruff, pytest, pytest-cov, httpx
│       ├── pyproject.toml          # ruff & pytest config
│       ├── .env.example
│       ├── tests/                  # Pytest test suite
│       │   ├── test_di_and_health.py
│       │   └── test_models.py
│       └── app/
│           ├── main.py             # Application factory + ASGI entry
│           ├── api/
│           │   └── routers/        # HTTP layer (request/response only)
│           │       └── health.py   # Liveness & DB connectivity (/health, /health/db)
│           ├── db/
│           │   ├── base.py         # SQLAlchemy DeclarativeBase
│           │   └── session.py      # Engine (NullPool) + get_db_session dependency
│           ├── models/             # Domain ORM models
│           │   ├── __init__.py
│           │   ├── uom.py          # Units of Measure & Conversions
│           │   ├── catalog.py      # Categories & Products
│           │   ├── warehouse.py    # Warehouses & StockBatches
│           │   ├── supplier.py     # Suppliers & PurchaseOrders
│           │   ├── retailer.py     # Retailers & SalesOrders
│           │   ├── inventory.py    # StockMovements (Append-only Ledger)
│           │   └── notification.py # Alert Notifications
│           ├── services/           # Business logic (depends on abstractions)
│           │   └── product_service.py
│           ├── repositories/
│           │   ├── interfaces/     # Protocol/ABC contracts
│           │   │   └── product_repository.py
│           │   └── impl/           # Concrete implementations
│           │       └── product_repository.py
│           ├── schemas/            # Pydantic request/response models
│           └── core/
│               ├── config.py       # pydantic-settings configuration
│               └── di.py           # Dependency injection wiring
```

## Database Schema

| Table                     | Purpose                          | Columns                                                                                                                                                                                                                                                       | Indexes / Constraints                                           |
| ------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `units_of_measure`        | Measurement units (pcs, box, kg) | `id` (PK, str), `name`, `abbreviation`, `created_at`                                                                                                                                                                                                          | `UNIQUE(abbreviation)`                                          |
| `categories`              | Product hierarchy                | `id` (PK, str), `name`, `parent_id` (FK), `created_at`                                                                                                                                                                                                        | `FK(parent_id -> categories.id)`                                |
| `products`                | Core product catalog             | `id` (PK, str), `sku`, `name`, `description`, `content_details`, `image_url`, `hsn_code`, `category_id` (FK), `base_uom_id` (FK), `unit`, `cost_price`, `wholesale_price`, `reorder_point`, `reorder_qty`, `barcode`, `is_active`, `created_at`, `updated_at` | `UNIQUE(sku)`, `INDEX(sku)`, `INDEX(barcode)`                   |
| `product_uom_conversions` | Conversion factors per product   | `id` (PK, str), `product_id` (FK), `from_uom_id` (FK), `to_uom_id` (FK), `factor`, `created_at`                                                                                                                                                               | `UNIQUE(product_id, from_uom_id, to_uom_id)`                    |
| `warehouses`              | Storage facilities               | `id` (PK, str), `name`, `location`, `is_active`, `created_at`                                                                                                                                                                                                 | —                                                               |
| `stock_batches`           | FIFO batch tracking & expiry     | `id` (PK, str), `product_id` (FK), `warehouse_id` (FK), `batch_no`, `quantity`, `expiry_date`, `received_at`                                                                                                                                                  | `INDEX(product_id, warehouse_id)`                               |
| `suppliers`               | Manufacturers / vendors          | `id` (PK, str), `name`, `contact_person`, `phone`, `email`, `address`, `gstin`, `fssai_license_no`, `fssai_expiry_date`, `is_active`, `created_at`                                                                                                            | —                                                               |
| `purchase_orders`         | Procurement orders               | `id` (PK, str), `po_number`, `supplier_id` (FK), `status` (enum), `order_date`, `expected_date`, `total_amount`, `created_at`                                                                                                                                 | `UNIQUE(po_number)`, `INDEX(po_number)`                         |
| `purchase_order_items`    | PO line items                    | `id` (PK, str), `po_id` (FK), `product_id` (FK), `qty_ordered`, `qty_received`, `unit_cost`, `uom_id` (FK)                                                                                                                                                    | `FK(po_id -> purchase_orders.id CASCADE)`                       |
| `retailers`               | B2B wholesale buyers             | `id` (PK, str), `name`, `contact_person`, `phone`, `email`, `address`, `gstin`, `pricing_tier`, `credit_limit`, `credit_balance`, `is_active`, `created_at`                                                                                                   | —                                                               |
| `sales_orders`            | B2B sales orders                 | `id` (PK, str), `so_number`, `retailer_id` (FK), `status` (enum), `order_date`, `total_amount`, `created_at`                                                                                                                                                  | `UNIQUE(so_number)`, `INDEX(so_number)`                         |
| `sales_order_items`       | SO line items                    | `id` (PK, str), `so_id` (FK), `product_id` (FK), `qty`, `unit_price`, `uom_id` (FK)                                                                                                                                                                           | `FK(so_id -> sales_orders.id CASCADE)`                          |
| `stock_movements`         | Append-only inventory ledger     | `id` (PK, str), `product_id` (FK), `warehouse_id` (FK), `batch_id` (FK), `type` (enum), `quantity`, `reference_type`, `reference_id`, `created_by`, `created_at`                                                                                              | `INDEX(product_id)`, `INDEX(warehouse_id)`, `INDEX(created_at)` |
| `notifications`           | System alerts & notices          | `id` (PK, str), `user_id`, `type`, `title`, `body`, `is_read`, `created_at`                                                                                                                                                                                   | `INDEX(user_id)`                                                |

### Enums:

- `POStatusEnum`: `draft`, `ordered`, `ready_for_dispatch`, `partially_received`, `received`, `cancelled`
- `SOStatusEnum`: `draft`, `confirmed`, `packed`, `shipped`, `delivered`, `cancelled`
- `StockMovementTypeEnum`: `in`, `out`, `adjustment`, `transfer`, `return_in`, `return_out`

## API Endpoints

| Method | Path         | Description                                        | Auth Required |
| ------ | ------------ | -------------------------------------------------- | ------------- |
| GET    | `/health`    | Liveness probe returning status: "ok"              | No            |
| GET    | `/health/db` | Database probe executing `SELECT 1` via connection | No            |

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
│  Config, security, DI wiring, DB session manager   │
└──────────────────────────────────────────────────┘
```

**Rule:** Routers NEVER import repositories directly. Only services.

## Decisions

| Decision                    | Rationale                                                                                                |
| --------------------------- | -------------------------------------------------------------------------------------------------------- |
| Supabase = DB only          | Need SQL joins, transactions, referential integrity for accounting                                       |
| Firebase = Auth only        | Best-in-class free Google/Apple Sign-In with minimal setup                                               |
| SOLID from day one          | Prevents spaghetti; makes testing and swapping implementations easy                                      |
| Application factory         | Testable app creation, supports different configs per environment                                        |
| pydantic-settings           | Single source of truth for env vars, validates on startup                                                |
| Prettier (web)              | Consistent formatting, 100 char line width matching ruff                                                 |
| Ruff (api)                  | Fast Python linter+formatter, line-length 100, rules: E/W/F/I/B/UP/SIM/N                                 |
| eslint-config-prettier      | Disables ESLint rules that conflict with Prettier                                                        |
| Local PG on 5433            | Avoid conflicts with system Postgres; Supabase stays primary                                             |
| Typed API Client            | Type-safe fetch wrapper with ApiError extracting status & server message                                 |
| DIP Container               | Services receive repository Protocol interfaces via FastAPI Depends()                                    |
| CI on Day One               | GitHub Actions pipeline runs lint + format + test + build on every push                                  |
| Automated QA                | QA checklist items written as automated tests, enforced by CI                                            |
| Connection Split (Supabase) | Port 6543 (transaction pooler) + NullPool for runtime; port 5432 (session pooler) for Alembic migrations |
| Schema v1 Completeness      | Core tables (UOM conversions, batch tracking, supplier FSSAI, retailer credit) created upfront           |
| Append-only Stock Ledger    | `stock_movements` is single source of truth for inventory balances                                       |

## Security

- Firebase ID tokens verified server-side by FastAPI via Firebase Admin SDK
- Tokens never trusted from client alone
- .env files git-ignored forever (Secrets Rule #1)
- .env.example updated with placeholders for every new var (Secrets Rule #2)
- CORS restricted to allowed origins loaded dynamically from `ALLOWED_ORIGINS` settings
- PostgreSQL connection passwords percent-encoded (`%40` for `@`) in connection strings

## Known Issues

- **Supabase Free Project Inactivity Pause**: Supabase free-tier projects automatically pause after ~1 week of inactivity. If API endpoints return connection errors after an idle period, unpause the project from the Supabase dashboard.
