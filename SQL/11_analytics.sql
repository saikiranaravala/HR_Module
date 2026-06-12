-- 11_analytics.sql — SCD2 dimension (closed + open rows, regrettable exit,
-- contingent toggle data), certified snapshots with a RESTATED version
-- (immutable v1 + annotated v2), org bridge for like-for-like trending.
-- worker_key is tokenized (PII-vault pattern): wk-NN, never a name.
BEGIN;

INSERT INTO analytics.dim_worker
  (row_id, worker_key, valid_from, valid_to, org_path, country, worker_type, fte, exited, regrettable_exit) VALUES
  -- Avery: closed row (pre-promotion) + open row
  ('afaf0001-0000-4000-8000-000000000001', 'wk-101', '2021-03-15', '2024-03-31', '/corp/eng/platform/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-000000000002', 'wk-101', '2024-04-01', '9999-12-31', '/corp/eng/platform/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-000000000003', 'wk-102', '2015-06-01', '9999-12-31', '/corp/eng/platform/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-000000000004', 'wk-103', '2022-02-14', '9999-12-31', '/corp/eng/platform/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-000000000005', 'wk-104', '2022-09-06', '9999-12-31', '/corp/eng/platform/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-000000000006', 'wk-105', '2026-05-08', '9999-12-31', '/corp/eng/platform/', 'DE', 'employee', 0.80, false, false),
  ('afaf0001-0000-4000-8000-000000000007', 'wk-106', '2010-01-11', '9999-12-31', '/corp/eng/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-000000000008', 'wk-107', '2026-01-01', '9999-12-31', '/corp/emea/finance/', 'DE', 'employee', 1.00, false, false),
  -- contingent (contractor-inclusion toggle demo)
  ('afaf0001-0000-4000-8000-000000000009', 'wk-108', '2026-02-02', '9999-12-31', '/corp/eng/platform/', 'US', 'contingent', 1.00, false, false),
  -- Pat: REGRETTABLE EXIT — closed active row + exited row (restated facts)
  ('afaf0001-0000-4000-8000-00000000000a', 'wk-109', '2017-10-09', '2026-04-29', '/corp/eng/platform/', 'US', 'employee', 1.00, false, false),
  ('afaf0001-0000-4000-8000-00000000000b', 'wk-109', '2026-04-30', '9999-12-31', '/corp/eng/platform/', 'US', 'employee', 1.00, true, true)
ON CONFLICT DO NOTHING;

-- Certified snapshots: v1 immutable; the retro exit produced an ANNOTATED v2
-- pointing at the original (restatement-by-version, never an UPDATE).
INSERT INTO analytics.certified_snapshot
  (snapshot_id, as_of, metric, value, version, restatement_of, annotation) VALUES
  ('afaf0002-0000-4000-8000-000000000001', '2026-05-01', 'headcount', 12691, 1, NULL, NULL),
  ('afaf0002-0000-4000-8000-000000000002', '2026-06-01', 'headcount', 12803, 1, NULL, NULL),
  ('afaf0002-0000-4000-8000-000000000003', '2026-06-01', 'headcount', 12802, 2, 'afaf0002-0000-4000-8000-000000000002',
   'retro exit wk-109 effective 2026-04-30 (regrettable)'),
  ('afaf0002-0000-4000-8000-000000000004', '2026-06-01', 'turnover', 0.094, 1, NULL, NULL)
ON CONFLICT DO NOTHING;

-- Reorg bridge: pre-reorg history trends like-for-like under the new org.
INSERT INTO analytics.org_bridge (bridge_id, old_org_path, new_org_path, effective_date) VALUES
  ('afaf0003-0000-4000-8000-000000000001', '/corp/eng/platform/', '/corp/product/platform/', '2026-09-01')
ON CONFLICT DO NOTHING;

COMMIT;
