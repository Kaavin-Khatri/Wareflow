# WareFlow

**AI-assisted wholesale inventory management system.**

Manage stock, orders, invoices, and supplier relationships with smart demand forecasting, automated reorder alerts, and natural language inventory queries — all on free-tier infrastructure.

## Stack

| Layer        | Technology                                          |
| ------------ | --------------------------------------------------- |
| Frontend     | Next.js 16 (App Router, TypeScript, Tailwind CSS 4) |
| Backend      | FastAPI (Python, SOLID architecture)                |
| Database     | Supabase Postgres                                   |
| Auth         | Firebase (Google, Apple, Email/Password)            |
| Email Alerts | Resend                                              |
| AI           | Groq (LLaMA / Mixtral)                              |
| Hosting      | Vercel (web) + Render (API)                         |

## Quick Start

### Prerequisites

- Node.js >= 20 and pnpm >= 9
- Python >= 3.11
- Git

### 1. Clone & Install

```bash
git clone https://github.com/Kaavin-Khatri/Wareflow.git
cd Wareflow

# Frontend
pnpm install

# Backend
cd apps/api
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt  # for ruff + pytest
```

### 2. Environment Variables

```bash
# Frontend — copy and fill in real values
cp apps/web/.env.example apps/web/.env.local

# Backend — copy and fill in real values
cp apps/api/.env.example apps/api/.env
```

> See [codebase_audit.md](codebase_audit.md) for the full env var registry.

### 3. Run Both Apps

```bash
# Terminal 1 — Frontend (http://localhost:3000)
pnpm dev:web

# Terminal 2 — Backend (http://localhost:8000)
cd apps/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### 4. Verify

- Frontend: open [http://localhost:3000](http://localhost:3000)
- Backend: `curl http://localhost:8000/health` → `{"status": "ok"}`

## Project Structure

```
wareflow/
├── apps/
│   ├── web/           # Next.js frontend
│   └── api/           # FastAPI backend (SOLID layers)
│       └── app/
│           ├── api/routers/          # HTTP layer
│           ├── services/             # Business logic
│           ├── repositories/
│           │   ├── interfaces/       # ABC/Protocol contracts
│           │   └── impl/             # SQLAlchemy implementations
│           ├── schemas/              # Pydantic models
│           └── core/                 # Config, DI, security
├── memory.md          # Project history (append-only)
├── codebase_audit.md  # Living system state
└── docker-compose.yml # Optional local Postgres
```

## Linting, Formatting & Testing

```bash
# Frontend
pnpm lint:web           # ESLint
pnpm format             # Prettier (whole repo)
pnpm format:check       # Prettier check (CI)
pnpm test:web           # Vitest unit tests

# Backend
cd apps/api && .\.venv\Scripts\Activate.ps1
ruff check app/ tests/  # Lint
ruff format app/ tests/ # Format
pytest --cov=app        # Pytest with coverage
```

## Continuous Integration & Branch Protection

A GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every `push` and `pull_request` to `main`:

- **Web**: Prettier format check, ESLint, Vitest unit tests, Next.js production build
- **API**: Ruff lint, Ruff format check, Pytest with coverage

### Recommended Branch Protection Setup

Once CI runs for the first time on GitHub:

1. Go to your repo on GitHub → **Settings** → **Branches**.
2. Click **Add branch protection rule** (or edit rule for `main`).
3. Branch name pattern: `main`.
4. Enable **Require status checks to pass before merging**.
5. Select the checks: `Web (Lint, Format, Test, Build)` and `API (Lint, Format, Test with Coverage)`.
6. Click **Save changes**.

## Architecture

The backend enforces SOLID layering from day one:

**Routers** → **Services** → **Repository Interfaces** → **Repository Implementations**

- Routers handle HTTP only (request/response)
- Services contain business logic and depend on abstractions
- Repository interfaces define data-access contracts (Protocol/ABC)
- Implementations are wired via dependency injection in `core/di.py`

> See [codebase_audit.md](codebase_audit.md) for the full architecture diagram and current state.

## License

Private — all rights reserved.
