# Cloud Deployment Guide — Project Meridian on Render + Supabase

This guide deploys the full Meridian stack to the cloud:

| Layer | Service | Tier |
|---|---|---|
| Database | Supabase PostgreSQL | Free |
| Backend API | Render Web Service (Python) | Free |
| Frontend UI | Render Static Site | Free |

Follow the sections in order. Steps 1–3 run on your local machine; steps 4–7 are in the cloud dashboards.

---

## Free tier constraints — read before you start

| Constraint | Impact |
|---|---|
| Render Web Service (free) spins down after **15 min of inactivity** | First request after idle takes 30–60 s (cold start) |
| Render Web Service (free) has **512 MB RAM** | All 16 modules fit; don't add memory-heavy dependencies |
| Supabase free project **pauses after 7 days of inactivity** | Unpause manually from the Supabase dashboard before testing |
| Supabase free project has **500 MB storage** | Enough for this project; don't load large attachments |

---

## Architecture overview

```
Browser
  └─► Render Static Site (UI — React/Vite, SPA)
        └─► (future) Render Web Service (FastAPI/uvicorn, port auto-assigned)
                          └─► Supabase PostgreSQL (direct connection, port 5432)
```

> The UI currently uses in-memory mock data (`UI/src/data.ts`). The REST client wiring to the backend is the next development phase. The backend is deployed now so it is ready when that work lands.

---

## Step 1: Format the Supabase connection string

Your Supabase direct connection URL is:
```
postgresql://postgres:[YOUR-PASSWORD]@db.coknqhohxzvnemzwolpe.supabase.co:5432/postgres
```

The app uses **psycopg3** (not psycopg2), and Supabase enforces SSL on all connections. You must adapt the URL in two ways:

1. Change the scheme from `postgresql://` to `postgresql+psycopg://`
2. Append `?sslmode=require`

**Your final connection string (substitute your real password):**
```
postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.coknqhohxzvnemzwolpe.supabase.co:5432/postgres?sslmode=require
```

Keep this string handy — you will paste it into both your local `.env` (step 2) and Render's environment variable dashboard (step 5).

> **Why port 5432 (direct) and not 6543 (pooler)?**
> Port 5432 is Supabase's direct connection. Port 6543 goes through PgBouncer (connection pooler), which does not support the DDL statements Alembic uses to create schemas and triggers. Always use 5432 for migration work. For high-concurrency production, you would switch to 6543 with a pooling-aware connection factory — outside the scope of this free-tier setup.

---

## Step 2: Run Alembic migrations against Supabase

Migrations must be applied from your local machine before you deploy. The Render web service does not run migrations automatically.

### 2a. Point your local `.env` at Supabase

Open `src\.env` and replace the local URL with your Supabase URL:

```
MERIDIAN_DATABASE_URL=postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.coknqhohxzvnemzwolpe.supabase.co:5432/postgres?sslmode=require
MERIDIAN_TEST_DATABASE_URL=postgresql+psycopg://meridian_dev:localpassword@localhost:5432/meridian_test
```

The test URL stays local — tests always run against your local PostgreSQL, never against the cloud database.

### 2b. Verify connectivity

```powershell
.\.venv\Scripts\python.exe -c "from platform_core.db import make_engine; e = make_engine(); print(e.connect())"
```

Expected: a SQLAlchemy `Connection` object printed, no error. If you see `SSL connection has been closed unexpectedly`, check that `sslmode=require` is in the URL.

### 2c. Apply all 17 migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

This creates 16 custom schemas (`platform`, `core`, `time_labor`, `payroll`, `benefits`, `workflow`, `integration`, `ai`, `service_delivery`, `analytics`, `comp`, `recruiting`, `performance`, `learning`, `succession`, `migration`) plus all tables and immutability triggers inside the Supabase `postgres` database.

Expected last line:
```
INFO  [alembic.runtime.migration] Running upgrade 0016 -> 0017, Add monotonic seq column to ninebox_placement
```

Verify:
```powershell
.\.venv\Scripts\python.exe -m alembic current
```
Should show `0017 (head)`.

### 2d. (Optional) Load the demo seed dataset

```powershell
$env:PGPASSWORD = "[YOUR-PASSWORD]"
psql -h db.coknqhohxzvnemzwolpe.supabase.co -U postgres -d postgres -v ON_ERROR_STOP=1 -f SQL\run_all.sql
```

### 2e. Restore your local `.env`

After migrations are confirmed, restore `src\.env` to your local PostgreSQL URL so local development and tests continue to work:

```
MERIDIAN_DATABASE_URL=postgresql+psycopg://meridian_dev:your_local_password@localhost:5432/meridian
MERIDIAN_TEST_DATABASE_URL=postgresql+psycopg://meridian_dev:your_local_password@localhost:5432/meridian_test
```

---

## Step 3: Prepare the repository

Two files were already created for you; make sure they are committed.

### 3a. Verify the new files exist

```powershell
Test-Path ".python-version"          # should print True
Test-Path "UI\public\_redirects"     # should print True
```

- **`.python-version`** — tells Render to use Python 3.11.9 (matches the local toolchain)
- **`UI/public/_redirects`** — tells Render's CDN to route all URL paths to `index.html` so React Router's client-side routing works correctly

### 3b. Commit and push to GitHub

```powershell
git add .python-version UI/public/_redirects
git commit -m "chore: add Render deployment config files"
git push origin main
```

Your repository must be on GitHub (or GitLab/Bitbucket) for Render to pull from it. If it is not yet on GitHub:

```powershell
# Create a new repo on github.com first, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

---

## Step 4: Supabase — verify schema is ready

1. Open [supabase.com](https://supabase.com) → your project → **Table Editor** (left sidebar).
2. You should see schemas `platform`, `core`, `payroll`, etc. in the schema dropdown. If the list only shows `public`, migrations did not apply — re-run step 2c.
3. Check **Project Settings → Database → Database pausing** is set to your preference. On free tier, enable "Pause after inactivity" but be aware you'll need to unpause before testing.

---

## Step 5: Render — deploy the backend API

### 5a. Create a new Web Service

1. Log in to [render.com](https://render.com) → **New +** → **Web Service**
2. Click **Connect a repository** → authorize GitHub → select your `HR_Module` repo
3. Fill in the service settings:

| Field | Value |
|---|---|
| **Name** | `meridian-api` |
| **Region** | Oregon (US West) — or closest to you |
| **Branch** | `main` |
| **Root Directory** | *(leave blank — repo root)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn platform_core.api:app --app-dir src --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

> **Why `--app-dir src`?** This flag adds `src/` to `sys.path`, which is how all package imports (`from platform_core...`, `from core_hr...`, etc.) resolve correctly — the same mechanism that `pyproject.toml`'s `pythonpath = ["src"]` provides locally.

### 5b. Set the environment variable

Scroll down to **Environment Variables** on the same page (or go to the service → **Environment** tab after creation):

| Key | Value |
|---|---|
| `MERIDIAN_DATABASE_URL` | `postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.coknqhohxzvnemzwolpe.supabase.co:5432/postgres?sslmode=require` |

Click **Save Changes** — Render will trigger a deploy automatically.

> Do **not** set `MERIDIAN_TEST_DATABASE_URL` on Render. It is only used by the local pytest suite.

### 5c. Watch the deploy log

In the Render dashboard → `meridian-api` → **Logs** tab. A successful deploy ends with:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXXX
```

If you see `RuntimeError: MERIDIAN_DATABASE_URL is not set`, the environment variable was not saved — go back to the **Environment** tab and confirm the key is there.

### 5d. Note your API URL

Render assigns a URL like `https://meridian-api.onrender.com`. You will see it at the top of the service page. Copy it.

### 5e. Smoke-test the API

Open these URLs in your browser (substitute your actual Render URL):

```
https://meridian-api.onrender.com/docs
https://meridian-api.onrender.com/v1/catalog/records-of-processing
https://meridian-api.onrender.com/v1/audit/verify
```

The `/docs` page should show the Swagger UI. The other two should return JSON. If the browser shows "Service Unavailable", wait 60 seconds — the free tier service may be cold-starting.

---

## Step 6: Render — deploy the UI

### 6a. Create a new Static Site

1. In Render → **New +** → **Static Site**
2. Select the same GitHub repository

| Field | Value |
|---|---|
| **Name** | `meridian-ui` |
| **Branch** | `main` |
| **Root Directory** | `UI` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |

> Setting **Root Directory** to `UI` means Render runs `npm install` inside `UI/`, which is where `package.json` lives. The publish directory `dist` is relative to that root, so it resolves to `UI/dist/`.

### 6b. No environment variables needed

The UI currently uses in-memory mock data (`UI/src/data.ts`). No `VITE_API_URL` or similar is needed yet. When the REST client is wired in a future phase, you will add `VITE_API_URL=https://meridian-api.onrender.com` here.

### 6c. Watch the deploy log

A successful build ends with:

```
✓ built in Xs
dist/index.html  X.XX kB │ gzip: X.XX kB
...
==> Uploading build...
==> Deployed to https://meridian-ui.onrender.com
```

### 6d. Verify SPA routing

Visit your Render static site URL (e.g., `https://meridian-ui.onrender.com`) and confirm:
- The Meridian home screen loads.
- Clicking **Payslips** in the left nav (which changes the URL to `/pay`) and then refreshing the browser still shows the Payslips page rather than a 404. This confirms the `_redirects` file is working.

---

## Step 7: End-to-end verification checklist

| Check | How |
|---|---|
| Supabase schemas exist | Supabase dashboard → Table Editor → check schema list |
| Alembic at head | `alembic current` locally with Supabase URL in `.env` |
| API `/docs` loads | `https://meridian-api.onrender.com/docs` |
| API returns clean audit chain | `https://meridian-api.onrender.com/v1/audit/verify` → `{"intact": true}` |
| UI home loads | `https://meridian-ui.onrender.com` |
| UI deep-link after refresh | Navigate to any page, refresh — should not 404 |

---

## Redeployment workflow (after code changes)

Render auto-deploys on every push to `main`. The workflow is:

```powershell
# Make your changes, then:
git add <files>
git commit -m "feat: ..."
git push origin main
# Render picks up the push and redeploys automatically within ~1-2 minutes
```

**For schema changes (new Alembic migration):**
Run the migration against Supabase from your local machine first, then push:

```powershell
# 1. Point src\.env at Supabase temporarily
# 2. Apply migration
.\.venv\Scripts\python.exe -m alembic upgrade head
# 3. Restore src\.env to local
# 4. Commit and push the new migration file
git add migrations/versions/XXXX_new_migration.py
git push origin main
```

---

## Troubleshooting

### `SSL connection has been closed unexpectedly` or `SSL error`
The `?sslmode=require` is missing from the URL. Update the `MERIDIAN_DATABASE_URL` env var on Render (Environment tab → Save Changes).

### `could not translate host name "db.coknqhohxzvnemzwolpe.supabase.co" to address`
The Render service cannot resolve the Supabase hostname — intermittent DNS issue. Trigger a manual redeploy from the Render dashboard (Manual Deploy → Deploy latest commit).

### `FATAL: password authentication failed for user "postgres"`
The password in the `MERIDIAN_DATABASE_URL` env var is wrong. Retrieve your Supabase database password from **Supabase → Project Settings → Database → Connection string** and update the Render env var.

### `permission denied to create schema`
Supabase's `postgres` user is a superuser and can create schemas. If you see this, the URL is pointing at the wrong database user. Confirm the user in the connection string is `postgres`, not `postgres.xxxxx` (the pooler format).

### Supabase database is paused
If your Supabase free project is paused (inactive for 7+ days), you will see connection refused errors. Go to [supabase.com](https://supabase.com) → your project → click **Restore project**. It takes ~1 minute to come back online.

### Render service shows 502 / `Application failed to respond`
The free-tier service is cold-starting. Wait 60 seconds and refresh. If it persists, check the **Logs** tab — look for import errors (missing package) or `RuntimeError: MERIDIAN_DATABASE_URL is not set`.

### UI shows 404 on direct URL / page refresh
The `UI/public/_redirects` file is missing from the repo. Verify it was committed:
```powershell
git show HEAD:UI/public/_redirects
```
Should print `/*    /index.html   200`. If not, commit and push it.

### `npm: command not found` during Render build
The **Root Directory** field in the static site settings must be set to `UI`, not left blank. Update it in the Render dashboard → Settings → Build & Deploy.

---

## Quick reference card

| Resource | URL |
|---|---|
| Backend API | `https://meridian-api.onrender.com` |
| API docs (Swagger) | `https://meridian-api.onrender.com/docs` |
| Frontend UI | `https://meridian-ui.onrender.com` |
| Supabase dashboard | `https://supabase.com/dashboard/project/coknqhohxzvnemzwolpe` |
| Render dashboard | `https://dashboard.render.com` |
