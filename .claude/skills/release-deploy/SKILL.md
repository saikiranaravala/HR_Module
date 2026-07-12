---
name: release-deploy
description: Ship code and schema changes to the deployed environments — local stack and the Render (API/UI) + Supabase (DB) cloud stack. Use when asked to "deploy", "release", "push to Render/Supabase", or after merging changes that include a migration.
---

# Release / Deploy

The canonical runbooks are **Deploy-local.md** (local Windows stack) and **Deploy-Render.md** (cloud) at the repo root — this skill is the operational ordering around them, because the ordering is what goes wrong.

## The one rule: schema before code

Render auto-deploys `main` on push, but **never runs migrations**. A push whose code expects a column that Supabase doesn't have yet = broken deploy. Always in this order:

1. **Migrate the cloud DB from the workstation:**
   - Point `src/.env` `MERIDIAN_DATABASE_URL` at Supabase — direct port **5432** (the 6543 pooler breaks Alembic DDL), driver prefix `postgresql+psycopg://`, suffix `?sslmode=require`.
   - `.\.venv\Scripts\python.exe -m alembic upgrade head`, confirm with `alembic current`.
   - **Restore `src/.env` to the local URLs immediately** — leaving it pointed at Supabase makes the next local test run hit the cloud DB.
2. **Push to `main`** — Render redeploys API and UI automatically (~1–2 min).
3. **Verify:** `https://<api>.onrender.com/docs` loads; `/v1/audit/verify` returns `{"intact": true}` (proves API→DB end to end); UI deep-link survives a refresh (the `_redirects` rule).

## Pre-push checklist (any release)

- [ ] Full pytest green locally; `npm run build` green in `UI/`.
- [ ] New migrations verified **up/down/up** on the local dev DB before touching Supabase.
- [ ] `SQL/DDL/` regenerated if a migration was added (`SQL/DDL/_generate.py`).
- [ ] No secrets in the diff — `src/.env` is git-ignored; cloud secrets live only in Render env vars.
- [ ] `Progress.md` updated (`update-progress` skill).

## Free-tier operational notes

- Render free services sleep after 15 min idle → first hit takes 30–60 s; pre-warm before demos.
- Supabase free projects pause after 7 idle days → unpause in the dashboard before migrating or demoing; a "connection refused" from a known-good URL usually means paused, not broken.
- Rollback = revert the commit and push (Render redeploys); a schema rollback additionally needs `alembic downgrade` run against Supabase from the workstation **before** the revert push, mirroring the forward ordering.

Troubleshooting beyond this (SSL errors, auth failures, 502s, SPA 404s): the Troubleshooting section of **Deploy-Render.md** covers each with its fix — don't re-diagnose from scratch.
