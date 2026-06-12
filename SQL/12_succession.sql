-- 12_succession.sql — T3 domain: key positions (one slate GAP), slates with
-- mandatory rationale + emergency designee + a STALE entry, talent profiles
-- (aspirations consent wall, acquisition interim), append-only 9-box lineage,
-- privileged discovery hold. Retirement eligibility is a BAND, never a date.
BEGIN;

INSERT INTO succession.key_position
  (position_id, title, incumbent_id, division_path, criticality, retirement_band) VALUES
  ('a1a10001-0000-4000-8000-000000000001', 'VP Finance EMEA', '22222222-2222-4222-8222-222222222107', '/corp/emea/finance/',
   '{"impact": 5, "scarcity": 4, "ramp": 3, "total": 26}', '3-5y'),
  -- GAP: no ready-now successor (slate-coverage metric driver)
  ('a1a10001-0000-4000-8000-000000000002', 'Director, Payroll Ops', '22222222-2222-4222-8222-222222222106', '/corp/ops/payroll/',
   '{"impact": 5, "scarcity": 3, "ramp": 2, "total": 23}', '>5y'),
  ('a1a10001-0000-4000-8000-000000000003', 'Director, Platform Eng', '22222222-2222-4222-8222-222222222102', '/corp/eng/platform/',
   '{"impact": 4, "scarcity": 3, "ramp": 2, "total": 20}', '>5y')
ON CONFLICT DO NOTHING;

INSERT INTO succession.slate_entry
  (entry_id, position_id, successor_id, readiness, rationale, emergency,
   development_plan_ref, last_validated, status) VALUES
  ('a1a10002-0000-4000-8000-000000000001', 'a1a10001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222101', 'now',
   'ran the org during Q1 parental-leave gap; calibrated exceeds', false, 'devplan://avery-2026', '2026-05-15', 'active'),
  -- EMERGENCY designee (distinct from development successors)
  ('a1a10002-0000-4000-8000-000000000002', 'a1a10001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222106', 'now',
   'interim cover only — VP scope, not a development successor', true, NULL, '2026-05-15', 'active'),
  -- STALE entry (last validated > 12 months → staleness alert)
  ('a1a10002-0000-4000-8000-000000000003', 'a1a10001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222102', '1-2y',
   'finance-adjacent platform leadership; needs EMEA rotation', false, NULL, '2025-04-01', 'active'),
  -- terminated successor → GAP status (slate-gap alert + review task)
  ('a1a10002-0000-4000-8000-000000000004', 'a1a10001-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222109', '1-2y',
   'payroll parallel-run lead experience', false, NULL, '2026-02-01', 'gap')
ON CONFLICT DO NOTHING;

INSERT INTO succession.talent_profile
  (profile_id, worker_id, aspirations, aspirations_consent, mobility_prefs,
   experiences, interim, history_note) VALUES
  -- consent OFF: aspirations never reach the current manager
  ('a1a10003-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101',
   'International assignment; platform VP track', false,
   '{"geo": ["DE", "SG"], "timeline": "12-18mo"}', '["event-layer launch", "migration parallel-run"]', false, NULL),
  ('a1a10003-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222103',
   'Staff engineer IC track', true, '{"geo": ["remote-US"]}', '["oncall-lead"]', false, NULL),
  -- acquisition cohort: INTERIM profile, limited history explicitly noted
  ('a1a10003-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222107', NULL, false, NULL,
   '["P&L €40M", "turnaround", "international"]', true,
   'acquired via Northwind close 2026-01; pre-close history not migrated')
ON CONFLICT DO NOTHING;

-- 9-box lineage: re-placement is a NEW row (append-only, DB-immutable).
INSERT INTO succession.ninebox_placement
  (placement_id, worker_id, session_id, performance, potential, rationale, actor, placed_at) VALUES
  ('a1a10004-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', 'tr-FY26-platform', 'exceeds', 'high',
   'scaled team through reorg; succession-ready per slate review', 'facilitator-hrbp-1', '2026-06-05 14:00+00'),
  ('a1a10004-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', 'tr-FY26-platform', 'meets', 'medium',
   'solid delivery; potential pending on-call leadership evidence', 'facilitator-hrbp-1', '2026-06-05 14:10+00'),
  ('a1a10004-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222104', 'tr-FY26-platform', 'meets', 'high',
   'calibrated against peer cohort: compiler initiative changed the slope', 'facilitator-hrbp-1', '2026-06-05 15:05+00')
ON CONFLICT DO NOTHING;

-- Legal discovery: artifacts under privilege; release requires named counsel.
INSERT INTO succession.discovery_hold
  (hold_id, scope, requested_by, counsel, privileged, counsel_approved, released, artifact_refs) VALUES
  ('a1a10005-0000-4000-8000-000000000001', 'worker:22222222-2222-4222-8222-222222222104', 'legal-ops', 'counsel-jane',
   true, false, false, '["ninebox:tr-FY26-platform", "slate:a1a10001-0000-4000-8000-000000000003"]')
ON CONFLICT DO NOTHING;

COMMIT;
