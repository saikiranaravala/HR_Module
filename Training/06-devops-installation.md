# Training 06 — DevOps / Platform Engineer (Installation & Deployment)

**Audience:** engineers who install, deploy, and operate the Meridian runtime. **Duration:** 2 days. **Prerequisites:** PostgreSQL administration basics, Git, one cloud platform.

The two canonical runbooks already exist and are the source of truth — this course teaches you to *own* them:

- **[Deploy-local.md](../Deploy-local.md)** — full local stack on Windows (12 sections + troubleshooting)
- **[Deploy-Render.md](../Deploy-Render.md)** — cloud: Render (API + UI) + Supabase (PostgreSQL)

## Learning Objectives

Install the stack from scratch both locally and in cloud; manage the migration chain safely; own environment configuration and secrets; understand every deployment invariant (what must never differ between environments); operate within free-tier constraints; know the target-state architecture and what is deliberately absent locally.

---

## Day 1 — Installation & Configuration

### 1.1 The pinned toolchain (never "close enough")

| Component | Version | Enforced by |
|---|---|---|
| Python | 3.11.9 | `.python-version` (Render reads it) |
| Node / npm | 24.14.0 / 11.11.0 | UI builds only |
| PostgreSQL | 17 | local service `postgresql-x64-17`; Supabase in cloud |
| Python deps | pinned in `requirements.txt` (+ `-dev`) | mirrors `pyproject.toml`; install both files |

### 1.2 Lab: local install from zero

Execute Deploy-local.md §1–8 on a clean machine/VM. Checkpoints: service running, `meridian`/`meridian_test` DBs created, `src/.env` populated, `alembic current` = head, pytest 237 green, API `/docs` up, UI dev server up.

Key facts you must be able to explain afterwards:
- **`src/.env` is the only config source** (`MERIDIAN_DATABASE_URL`, `MERIDIAN_TEST_DATABASE_URL`) — loaded by `platform_core.db`; git-ignored; no config lives in code.
- **Driver string is `postgresql+psycopg://`** (psycopg3) — `postgresql://` alone or psycopg2 forms fail.
- **Tests don't use Alembic** — each module's conftest rebuilds its schemas from ORM metadata in `meridian_test`. Consequence: model/migration drift shows up as "tests pass, dev DB broken" or vice versa — treat either as a release blocker.
- **Two schema paths, one truth:** Alembic chain (canonical) vs `SQL/DDL/run_all.sql` (pg_dump artifact for scratch builds, requires `alembic stamp head` after). DDL is regenerated (`SQL/DDL/_generate.py`) after each new migration — check it's current before using it.

### 1.3 Lab: cloud install

Execute Deploy-Render.md end to end. The five decisions that matter:

1. **Supabase connection = direct port 5432, `?sslmode=require`** — the 6543 pooler breaks Alembic DDL.
2. **Migrations run from a workstation, not the platform** — Render never migrates automatically; schema changes are a deliberate pre-deploy step.
3. **Start command:** `uvicorn platform_core.api:app --app-dir src --host 0.0.0.0 --port $PORT` — `--app-dir src` is what makes every package import resolve.
4. **UI is a static site** with root directory `UI`, publish `dist`, and `UI/public/_redirects` (`/* /index.html 200`) for SPA routing.
5. **Secrets live in Render env vars** — only `MERIDIAN_DATABASE_URL`; never set the test URL in cloud.

## Day 2 — Operations, Constraints & Target State

### 2.1 Migration operations (the riskiest thing you do)

```powershell
.\.venv\Scripts\python.exe -m alembic current            # where am I
.\.venv\Scripts\python.exe -m alembic upgrade head       # apply
.\.venv\Scripts\python.exe -m alembic downgrade -1       # down-path check
.\.venv\Scripts\python.exe -m alembic history --verbose  # the chain
.\.venv\Scripts\python.exe -m alembic stamp head         # after a DDL bootstrap ONLY
```

Rules: every new migration is verified **up/down/up** before merge; `stamp` is for aligning a DDL-bootstrapped DB, never for "fixing" a failed migration; a migration that mutates history data (not just schema) is forbidden without retro events + reconciliation evidence — escalate, don't run it.

### 2.2 Free-tier constraints you operate around

| Constraint | Operational answer |
|---|---|
| Render free service sleeps after 15 min | First-hit latency 30–60 s; warn demo audiences or pre-warm before sessions |
| Supabase free pauses after 7 days idle | Unpause in dashboard before any demo/training day |
| 512 MB RAM on Render | Watch deploy logs for OOM kills if dependencies grow |
| Auto-deploy on push to `main` | Protect `main`; a bad push is a bad deploy |

### 2.3 CI expectations (gates, not suggestions)

Green before merge: full pytest (all modules), `npm run build` (tsc + vite), lint. Release checklist adds: new migrations verified up/down/up; DDL regenerated; `Progress.md` updated. WCAG 2.2 AA is designed to become a CI gate when the UI hardening phase lands — flag any a11y regression now rather than accumulating debt.

### 2.4 Target-state architecture (so you don't "fix" deliberate gaps)

The spec (PRD 15) targets: services per bounded context on EKS, Aurora per service, Kafka (MSK), Redis (no PII), OpenSearch, Terraform + OPA, ArgoCD GitOps, mTLS mesh, signed images + SBOM. **None of this exists locally, deliberately** — events are deferred (direct service calls), one PostgreSQL stands in for DB-per-service, and cloud-only concerns are marked N/A-local in design docs. Recorded in `.claude/memory.md`. Do not introduce infrastructure ahead of the module that owns it.

### 2.5 Security operations you own

- No PII in logs — application logging is ID-based; if you add log lines, keep them that way (Invariant #8).
- `src/.env`, Render env vars, and Supabase credentials are the secret surface; rotation = update var + redeploy + verify `/v1/audit/verify` still reads the DB.
- The audit chain (`GET /v1/audit/verify`) is also your post-incident integrity check — see Training 07.

---

## Competency Checklist (sign-off)

- [ ] Clean-machine local install unaided; all checkpoints green
- [ ] Cloud deploy unaided including migration pre-step and SPA redirects
- [ ] Explains model-vs-migration drift and both places it manifests
- [ ] Performs up/down/up verification; states the two legitimate uses of `stamp`
- [ ] States all four free-tier constraints and their operational answers
- [ ] Names the deliberately-absent infrastructure and where the deferral is recorded
