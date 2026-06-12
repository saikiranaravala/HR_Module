-- SQL/DDL/run_all.sql — build the complete Meridian schema on an EMPTY database.
--   createdb -h localhost -U meridian_dev meridian_new
--   psql -h localhost -U meridian_dev -d meridian_new -v ON_ERROR_STOP=1 -f SQL/DDL/run_all.sql
--
-- NOTE: the canonical schema source is Alembic (migrations/versions/, rev 0016).
-- These files are a faithful pg_dump of that schema for standalone builds.
-- After loading, align Alembic so future migrations apply cleanly:
--   alembic stamp head
-- 01_platform MUST run first: it creates platform.forbid_mutation(), which
-- every immutability trigger in later files references.
\ir 01_platform.sql
\ir 02_workflow.sql
\ir 03_integration.sql
\ir 04_ai.sql
\ir 05_core.sql
\ir 06_time_labor.sql
\ir 07_payroll.sql
\ir 08_benefits.sql
\ir 09_service_delivery.sql
\ir 10_analytics.sql
\ir 11_comp.sql
\ir 12_recruiting.sql
\ir 13_performance.sql
\ir 14_learning.sql
\ir 15_succession.sql
\ir 16_migration.sql
\echo '--- Meridian DDL loaded (16 schemas) ---'
