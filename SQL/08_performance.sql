-- 08_performance.sql — goal cascade + version chain + orphan, review docs in
-- every state (AI-drafted+edited, released, AMENDED DUAL RECORD, PIP T3,
-- close-out, manager handoff, leave extension), append-only calibration
-- lineage, check-ins with author-only private notes, 360 with anonymity.
BEGIN;

INSERT INTO performance.goal
  (goal_id, worker_id, title, goal_type, weight, parent_goal_id, visibility, status, version, supersedes) VALUES
  -- cascade: company → org → individual
  ('acac0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222106', 'Platform reliability 99.95%', 'okr', 100, NULL, 'public', 'active', 1, NULL),
  ('acac0001-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222102', 'Org: ship event layer + cut latency', 'okr', 100, 'acac0001-0000-4000-8000-000000000001', 'public', 'active', 1, NULL),
  -- Avery v1 superseded by v2 (mid-cycle revision; original preserved)
  ('acac0001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222101', 'Ship event-layer v1', 'okr', 40, 'acac0001-0000-4000-8000-000000000002', 'manager', 'superseded', 1, NULL),
  ('acac0001-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222101', 'Ship event-layer v1 + hardening', 'okr', 50, 'acac0001-0000-4000-8000-000000000002', 'manager', 'active', 2, 'acac0001-0000-4000-8000-000000000003'),
  -- orphan goal (no alignment) — shows on the leaders' orphan report
  ('acac0001-0000-4000-8000-000000000005', '22222222-2222-4222-8222-222222222104', 'Refactor build scripts', 'okr', 30, NULL, 'manager', 'active', 1, NULL),
  -- development goal (exempt from orphan report)
  ('acac0001-0000-4000-8000-000000000006', '22222222-2222-4222-8222-222222222101', 'Mentor 2 associate engineers', 'development', 25, NULL, 'private', 'active', 1, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO performance.review_cycle (cycle_id, name, template_key, status, launched_on, window_end) VALUES
  ('acac0002-0000-4000-8000-000000000001', 'FY26 Annual', 'annual-standard', 'open', '2026-01-15', '2026-07-15'),
  ('acac0002-0000-4000-8000-000000000002', 'FY25 Annual', 'annual-standard', 'closed', '2025-01-15', '2025-07-15')
ON CONFLICT DO NOTHING;

INSERT INTO performance.review_doc
  (doc_id, cycle_id, worker_id, manager_id, state, rating, narrative, self_assessment,
   ai_drafted, ai_draft_edited, prorated, extension_until, restricted, amends,
   amendment_reason, skip_level_disagreement, acknowledged_comment, closeout_reason, handoff_log) VALUES
  -- Avery: AI-drafted, edited (gate satisfied), calibrated; manager HANDOFF logged
  ('acac0003-0000-4000-8000-000000000001', 'acac0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', '22222222-2222-4222-8222-222222222102',
   'calibrated', 'exceeds', 'Delivered the event-layer milestone ahead of plan; latency down 22%.', 'Strong year; want Data Platform scope.',
   true, true, false, NULL, false, NULL, NULL, NULL, NULL, NULL,
   '[{"outgoing":"mgr-previous","incoming":"22222222-2222-4222-8222-222222222102","at":"2026-03-02T10:00:00+00:00","draft_state_at_handoff":"draft"}]'),
  -- Jordan: LEAVE AUTO-EXTENSION (parental +60d past window end)
  ('acac0003-0000-4000-8000-000000000002', 'acac0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222103', '22222222-2222-4222-8222-222222222102',
   'self-done', NULL, NULL, 'Drafting…', false, false, false, '2026-09-13', false, NULL, NULL, NULL, NULL, NULL, NULL),
  -- Sasha: PRORATED (hired mid-window, >90d at launch is false — she joined 2026-05-08, excluded from FY26; instead prorate Riley)
  ('acac0003-0000-4000-8000-000000000003', 'acac0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222104', '22222222-2222-4222-8222-222222222102',
   'draft', NULL, NULL, NULL, false, false, true, NULL, false, NULL, NULL, 'dir-dana: rating may understate scope growth', NULL, NULL, NULL),
  -- FY25 RELEASED doc later AMENDED: dual record — original preserved as 'amended'
  ('acac0003-0000-4000-8000-000000000004', 'acac0002-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222101', '22222222-2222-4222-8222-222222222102',
   'amended', 'meets', 'FY25: solid delivery (2/3 goals).', NULL, false, false, false, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL),
  ('acac0003-0000-4000-8000-000000000005', 'acac0002-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222101', '22222222-2222-4222-8222-222222222102',
   'released', 'exceeds', 'FY25: goal attainment recounted (3/3, not 2/3).', NULL, false, false, false, NULL, false,
   'acac0003-0000-4000-8000-000000000004', 'goal attainment miscounted (3/3 not 2/3)', NULL, 'Acknowledged — thanks for the correction.', NULL, NULL),
  -- terminated-before-release CLOSE-OUT (Pat, FY26)
  ('acac0003-0000-4000-8000-000000000006', 'acac0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222109', '22222222-2222-4222-8222-222222222102',
   'closed-out', NULL, NULL, NULL, false, false, false, NULL, false, NULL, NULL, NULL, NULL, 'terminated 2026-04-30 before release', NULL),
  -- RESTRICTED PIP doc (T3 tier, read-audited)
  ('acac0003-0000-4000-8000-000000000007', 'acac0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222104', '22222222-2222-4222-8222-222222222102',
   'draft', NULL, 'Milestone 1: on-call readiness by 2026-07-01.', NULL, false, false, false, NULL, true, NULL, NULL, NULL, NULL, NULL, NULL)
ON CONFLICT DO NOTHING;

-- Calibration lineage: append-only, every adjustment has actor + rationale.
INSERT INTO performance.calibration_adjustment
  (adjustment_id, doc_id, session_id, before_rating, after_rating, rationale, actor, adjusted_at) VALUES
  ('acac0004-0000-4000-8000-000000000001', 'acac0003-0000-4000-8000-000000000001', 'cal-FY26-platform', 'meets', 'exceeds',
   'cross-team comparison: top-quartile impact on three dependent teams', 'hrbp-1', '2026-06-05 15:00+00'),
  ('acac0004-0000-4000-8000-000000000002', 'acac0003-0000-4000-8000-000000000001', 'cal-FY26-platform', 'exceeds', 'exceeds',
   'skip-level resolution: panel reviewed; rating stands', 'hrbp-1', '2026-06-05 15:40+00')
ON CONFLICT DO NOTHING;

INSERT INTO performance.checkin
  (checkin_id, worker_id, manager_id, occurred_on, shared_notes, private_notes, private_notes_author) VALUES
  ('acac0005-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', '22222222-2222-4222-8222-222222222102',
   '2026-06-02', 'Growth plan: event-layer ownership; Data Platform rotation discussed.', 'Watch workload — burnout risk after the migration push.', '22222222-2222-4222-8222-222222222102'),
  ('acac0005-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', '22222222-2222-4222-8222-222222222102',
   '2026-05-05', 'Workload review; on-call rotation feedback.', NULL, NULL)
ON CONFLICT DO NOTHING;

-- 360 campaign: communication has 3 raters (theme shown), strategy has 1 (withheld).
INSERT INTO performance.feedback
  (feedback_id, author_id, subject_id, visibility, body, competency, campaign_id, given_on) VALUES
  ('acac0006-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222103', '22222222-2222-4222-8222-222222222101', 'to-manager', 'Communicates incident state clearly under pressure.', 'communication', '360-FY26-avery', '2026-05-20'),
  ('acac0006-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', '22222222-2222-4222-8222-222222222101', 'to-manager', 'Design docs are a model for the org.', 'communication', '360-FY26-avery', '2026-05-21'),
  ('acac0006-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222106', '22222222-2222-4222-8222-222222222101', 'to-manager', 'Clear, candid status reporting.', 'communication', '360-FY26-avery', '2026-05-22'),
  ('acac0006-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222102', '22222222-2222-4222-8222-222222222101', 'to-manager', 'Needs more multi-quarter strategy framing.', 'strategy', '360-FY26-avery', '2026-05-23'),
  -- explicit to-subject praise (never silently manager-visible)
  ('acac0006-0000-4000-8000-000000000005', '22222222-2222-4222-8222-222222222103', '22222222-2222-4222-8222-222222222104', 'to-subject', 'Thanks for the pairing session on the compiler!', NULL, NULL, '2026-06-01')
ON CONFLICT DO NOTHING;

COMMIT;
