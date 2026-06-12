-- run_all.sql — load the full Meridian demo dataset.
--   psql -h localhost -U meridian_dev -d meridian -v ON_ERROR_STOP=1 -f SQL/run_all.sql
-- Prereq: alembic upgrade head (schema 0016). Each file is its own transaction.
\ir 00_reset.sql
\ir 01_core_org.sql
\ir 02_workflow_integration_ai.sql
\ir 03_time_labor.sql
\ir 04_payroll.sql
\ir 05_benefits.sql
\ir 06_compensation.sql
\ir 07_recruiting.sql
\ir 08_performance.sql
\ir 09_learning.sql
\ir 10_service_delivery.sql
\ir 11_analytics.sql
\ir 12_succession.sql
\ir 13_migration.sql
\echo '--- demo dataset loaded ---'
