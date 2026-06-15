# Local Deployment Guide — Project Meridian (Windows 10)

This guide brings up the full Meridian stack locally: PostgreSQL 17, the Python/FastAPI backend, and the React/Vite UI. Follow the sections in order on a fresh machine, or jump to a specific section if you are re-deploying after a reset.

---

## 1. Prerequisites

The versions below are pinned and confirmed working on this machine. Install exactly these versions to avoid unexpected behaviour.

| Tool | Required version | Installer |
|---|---|---|
| Python | **3.11.9** | [python.org/downloads](https://www.python.org/downloads/release/python-3119/) — tick "Add Python to PATH" |
| Node.js | **v24.14.0** | [nodejs.org/en/download](https://nodejs.org/en/download/) — includes npm 11 |
| PostgreSQL | **17** (17.10+) | [enterprisedb.com/downloads/postgres-postgresql-downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) — Windows x86-64 |
| Git | any recent | [git-scm.com](https://git-scm.com) |

### 1a. Add PostgreSQL binaries to PATH

The installer does **not** add the `bin` folder to your system PATH by default. Without this, `psql`, `pg_dump`, and `createdb` are not runnable from the terminal.

1. Open **Start → Edit the system environment variables → Environment Variables**.
2. Under **System variables**, select `Path` and click **Edit**.
3. Click **New** and add: `C:\Program Files\PostgreSQL\17\bin`
4. Click **OK** on all dialogs.
5. Open a **new** PowerShell window and confirm: `psql --version` → should print `psql (PostgreSQL) 17.x`.

---

## 2. Clone (or open) the repository

```powershell
# If cloning fresh:
git clone <repo-url> e:\AIWorkSpace\HR_Module
cd e:\AIWorkSpace\HR_Module

# If already cloned, just ensure you are on main:
cd e:\AIWorkSpace\HR_Module
git checkout main
git pull
```

All subsequent commands in this guide assume `e:\AIWorkSpace\HR_Module` is your working directory unless stated otherwise.

---

## 3. Python virtual environment and dependencies

### 3a. Create the virtualenv

```powershell
python -m venv .venv
```

This creates `.venv\` at the repo root. The `.venv\` folder is already git-ignored.

### 3b. Activate (only needed for interactive shell sessions)

```powershell
.\.venv\Scripts\Activate.ps1
```

If you see an execution-policy error, run once as Administrator:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3c. Install pinned runtime + dev dependencies

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt -r requirements-dev.txt
```

Key packages installed:

| Package | Pinned version | Purpose |
|---|---|---|
| fastapi | 0.136.3 | API framework |
| uvicorn | 0.49.0 | ASGI server |
| SQLAlchemy | 2.0.50 | ORM / query builder |
| alembic | 1.18.4 | Schema migrations |
| psycopg[binary] | 3.3.4 | PostgreSQL driver (psycopg3) |
| pydantic | 2.13.4 | Request/response validation |
| PyYAML | 6.0.3 | Config file loading |
| pytest | 9.0.3 | Test runner |
| pytest-cov | 7.1.0 | Coverage |

---

## 4. PostgreSQL setup

### 4a. Verify the service is running

```powershell
Get-Service -Name "postgresql-x64-17"
```

Expected output: `Status = Running`. If it shows `Stopped`:

```powershell
Start-Service -Name "postgresql-x64-17"
```

To make it start automatically on boot:
```powershell
Set-Service -Name "postgresql-x64-17" -StartupType Automatic
```

### 4b. Create the application database user

Connect as the PostgreSQL superuser (`postgres`). You will be prompted for the password you set during installation.

```powershell
psql -h localhost -U postgres
```

Inside the `psql` prompt, run these SQL statements. Replace `your_password` with a password of your choice — you will use it in step 5.

```sql
-- Create the dedicated app user
CREATE USER meridian_dev WITH PASSWORD 'your_password';

-- Create the development database
CREATE DATABASE meridian OWNER meridian_dev;

-- Create the test database (used by pytest only)
CREATE DATABASE meridian_test OWNER meridian_dev;

-- Grant schema creation rights (Alembic creates schemas on first run)
ALTER USER meridian_dev CREATEDB;

\q
```

### 4c. Verify connectivity

```powershell
psql -h localhost -U meridian_dev -d meridian -c "SELECT current_user, current_database();"
```

You should see `meridian_dev | meridian`. If it prompts for a password, enter the one you chose above.

---

## 5. Configure database connection strings

Create the file `src\.env` (this file is git-ignored and must not be committed):

```powershell
New-Item -Path "src\.env" -ItemType File
```

Open `src\.env` in any text editor and add these two lines, substituting your password from step 4b:

```
MERIDIAN_DATABASE_URL=postgresql+psycopg://meridian_dev:your_password@localhost:5432/meridian
MERIDIAN_TEST_DATABASE_URL=postgresql+psycopg://meridian_dev:your_password@localhost:5432/meridian_test
```

**Important:** The driver prefix is `postgresql+psycopg` (psycopg3 — not `psycopg2`). Do not use `localhost/` without the port; always specify `:5432`.

---

## 6. Apply the database schema

You have two paths. **Path A (Alembic)** is the canonical method and must be used when contributing. **Path B (DDL bootstrap)** is faster for a read-only local setup.

### Path A — Alembic migrations (recommended)

Runs all 16 migration revisions (0001 → 0016) against the `meridian` database:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Expected last line: `INFO  [alembic.runtime.migration] Running upgrade ... -> 0016_migration_program`.

Verify the applied revision:
```powershell
.\.venv\Scripts\python.exe -m alembic current
```
Should show `0016_migration_program (head)`.

**Always verify the down-path works** before committing a new migration:
```powershell
.\.venv\Scripts\python.exe -m alembic downgrade -1
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### Path B — DDL standalone bootstrap (faster, scratch only)

Use this only to build a scratch inspection database from the pre-generated DDL files. **Do not use this on the `meridian` database you already migrated via Path A.**

```powershell
# Create a separate scratch database
psql -h localhost -U postgres -c "CREATE DATABASE meridian_scratch OWNER meridian_dev;"

# Load all 16 schemas (must run from the SQL/DDL directory because of \ir directives)
psql -h localhost -U meridian_dev -d meridian_scratch -v ON_ERROR_STOP=1 -f SQL\DDL\run_all.sql

# Stamp Alembic so future migrations apply cleanly
$env:MERIDIAN_DATABASE_URL = "postgresql+psycopg://meridian_dev:your_password@localhost:5432/meridian_scratch"
.\.venv\Scripts\python.exe -m alembic stamp head
```

---

## 7. Load the demo seed dataset (optional)

The `SQL/` folder contains a coherent 9-person demo cast that exercises every module. This is **not required** for running tests (tests generate their own data), but is useful for manual UI exploration.

Prerequisites: Alembic must already be at head on the `meridian` database (step 6).

```powershell
# Run from the repo root — \ir directives are relative to the file's directory
psql -h localhost -U meridian_dev -d meridian -v ON_ERROR_STOP=1 -f SQL\run_all.sql
```

Expected last line: `--- demo dataset loaded ---`

To reload from scratch (wipes all seeded rows, preserves the audit_event chain):
```powershell
psql -h localhost -U meridian_dev -d meridian -v ON_ERROR_STOP=1 -f SQL\00_reset.sql
psql -h localhost -U meridian_dev -d meridian -v ON_ERROR_STOP=1 -f SQL\run_all.sql
```

---

## 8. Run the test suite

The test suite connects to `meridian_test` and recreates schemas from `Base.metadata` on every session — it does **not** use Alembic. Each test gets a truncated-clean session. PostgreSQL must be running.

```powershell
# Full suite (237 tests, ~30 s on a local machine)
.\.venv\Scripts\python.exe -m pytest

# Single module
.\.venv\Scripts\python.exe -m pytest src/test/core_hr

# Single named test
.\.venv\Scripts\python.exe -m pytest src/test/core_hr/test_core_hr.py::test_CORE_rehire_bridges_original_hire_date

# With coverage report
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing
```

A clean run should end with `237 passed, 0 failed`. If you see `MERIDIAN_TEST_DATABASE_URL is not set`, the `src\.env` file is missing or has a typo — revisit step 5.

---

## 9. Start the backend API server

The Platform Core FastAPI app is the HTTP entry point for policy decisions, audit verification, and the records-of-processing catalog. Other service modules are called in-process; this surface is what the UI and external consumers hit.

```powershell
.\.venv\Scripts\python.exe -m uvicorn platform_core.api:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

Flag | Meaning
---|---
`--app-dir src` | Adds `src/` to `sys.path` so all packages resolve correctly
`--reload` | Auto-restarts on code changes (development only — omit for a stable session)
`--host 127.0.0.1` | Binds to localhost only (safe for local dev)
`--port 8000` | Default; change if 8000 is occupied

Verify the server is healthy:
```powershell
# In a second terminal:
curl http://127.0.0.1:8000/v1/catalog/records-of-processing
```

You should receive a JSON body with a `register` array. The interactive API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Key API endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/policy/decide` | POST | Central policy decision point |
| `/v1/audit/verify` | GET | Verify audit hash chain integrity |
| `/v1/catalog/records-of-processing` | GET | GDPR records-of-processing register |

---

## 10. Start the UI dev server

The React frontend lives in `UI/`. Switch to that directory before running npm commands.

### 10a. Install Node dependencies (first time, or after `package.json` changes)

```powershell
cd UI
npm install
```

### 10b. Start the Vite development server

```powershell
npm run dev
```

Vite will print something like:
```
  VITE v6.x.x  ready in 400 ms
  ➜  Local:   http://localhost:5173/
```

Open [http://localhost:5173](http://localhost:5173) in your browser. The UI serves the 16-screen shell with demo data loaded from `UI/src/store.tsx` (the API integration layer is the next development phase — the REST calls are not yet wired).

### 10c. Other UI commands

```powershell
# Type-check + production build (must stay green before committing UI changes)
npm run build

# ESLint
npm run lint

# Preview the production build locally
npm run preview
```

---

## 11. Verify the full stack

With both servers running, confirm end-to-end operation:

```powershell
# 1. Policy API responds
curl http://127.0.0.1:8000/v1/policy/decide `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"subject_id":"u1","roles":["employee"],"capability":"person.read"}'

# 2. Audit chain is intact
curl http://127.0.0.1:8000/v1/audit/verify
# Expect: {"intact": true, "firstBrokenSeq": null, ...}

# 3. UI loads
Start-Process "http://localhost:5173"
```

---

## 12. Common issues

### `MERIDIAN_DATABASE_URL is not set`
`src\.env` is missing or not being found. The file must be at `e:\AIWorkSpace\HR_Module\src\.env` (not the repo root). Verify with:
```powershell
Test-Path "e:\AIWorkSpace\HR_Module\src\.env"
```

### `psql: error: connection to server ... failed: FATAL: password authentication failed`
The password in `src\.env` does not match the one you set in PostgreSQL. Reset it:
```powershell
psql -h localhost -U postgres -c "ALTER USER meridian_dev WITH PASSWORD 'your_new_password';"
```
Then update `src\.env` to match.

### `could not connect to server: Connection refused`
The PostgreSQL service is not running. Start it:
```powershell
Start-Service -Name "postgresql-x64-17"
```

### `permission denied to create schema`
The `meridian_dev` user was not granted `CREATEDB`. Fix with:
```powershell
psql -h localhost -U postgres -c "ALTER USER meridian_dev CREATEDB;"
```

### Port 8000 already in use
Either stop the other process or start uvicorn on a different port:
```powershell
.\.venv\Scripts\python.exe -m uvicorn platform_core.api:app --app-dir src --reload --port 8001
```

### `npm run build` fails with TypeScript errors
Run `npm run lint` first to isolate ESLint issues. For type errors: `npx tsc --noEmit` shows the full error list. The build must be green before committing UI changes.

### Alembic `Can't locate revision identified by ...`
The migration chain is broken. Show current state and force-stamp to recover:
```powershell
.\.venv\Scripts\python.exe -m alembic history --verbose
.\.venv\Scripts\python.exe -m alembic stamp head   # only if you are certain the schema matches 0016
```

---

## Quick-start reference card

Once set up, a typical dev session is:

```powershell
# Terminal 1 — backend
cd e:\AIWorkSpace\HR_Module
.\.venv\Scripts\python.exe -m uvicorn platform_core.api:app --app-dir src --reload

# Terminal 2 — UI
cd e:\AIWorkSpace\HR_Module\UI
npm run dev

# Terminal 3 — tests (on demand)
cd e:\AIWorkSpace\HR_Module
.\.venv\Scripts\python.exe -m pytest
```

Services at a glance:

| Service | URL | Notes |
|---|---|---|
| Backend API | http://127.0.0.1:8000 | FastAPI / uvicorn |
| API docs (Swagger) | http://127.0.0.1:8000/docs | Auto-generated |
| UI dev server | http://localhost:5173 | Vite HMR |
| PostgreSQL | localhost:5432 | Service: `postgresql-x64-17` |
