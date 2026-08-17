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
│       │       └── 0001_initial_schema_probe.py
│       ├── requirements.txt
│       ├── requirements-dev.txt    # ruff, pytest, pytest-cov, httpx
│       ├── pyproject.toml          # ruff & pytest config
│       ├── .env.example
│       ├── tests/                  # Pytest test suite
│       │   └── test_di_and_health.py
│       └── app/
│           ├── main.py             # Application factory + ASGI entry
│           ├── api/
│           │   └── routers/        # HTTP layer (request/response only)
│           │       └── health.py   # Liveness & DB connectivity (/health, /health/db)
│           ├── db/
│           │   ├── base.py         # SQLAlchemy DeclarativeBase
│           │   └── session.py      # Engine (NullPool) + get_db_session dependency
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

| Table           | Purpose                     | Migration                   | Status              |
| --------------- | --------------------------- | --------------------------- | ------------------- |
| `_schema_probe` | Pipeline verification table | `0001_initial_schema_probe` | Applied to Supabase |

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
│  Schemas (app/schemas/)                            │
│  Pydantic models — pure data contracts             │
├──────────────────────────────────────────────────┤
│  Core & DB (app/core/, app/db/)                    │
│  Config, security, DI wiring, DB session manager   │
└──────────────────────────────────────────────────┘
```

**Rule:** Routers NEVER import repositories directly. Only services.

### Worked Dependency Inversion Pattern:

```python
# 1. Interface (Abstraction)
class ProductRepositoryInterface(Protocol):
    def get_by_id(self, product_id: str) -> dict | None: ...

# 2. Service (Depends only on Abstraction)
class ProductService:
    def __init__(self, repository: ProductRepositoryInterface) -> None:
        self._repo = repository

# 3. DI Container (Wired via FastAPI Depends)
def get_product_service(
    repo: ProductRepositoryInterface = Depends(get_product_repository)
) -> ProductService:
    return ProductService(repository=repo)
```

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

## Security

- Firebase ID tokens verified server-side by FastAPI via Firebase Admin SDK
- Tokens never trusted from client alone
- .env files git-ignored forever (Secrets Rule #1)
- .env.example updated with placeholders for every new var (Secrets Rule #2)
- CORS restricted to allowed origins loaded dynamically from `ALLOWED_ORIGINS` settings
- PostgreSQL connection passwords percent-encoded (`%40` for `@`) in connection strings

## Known Issues

- **Supabase Free Project Inactivity Pause**: Supabase free-tier projects automatically pause after ~1 week of inactivity. If API endpoints return connection errors after an idle period, unpause the project from the Supabase dashboard.
