-- 05_benefits.sql — plans (EOI threshold, defaulting), age-banded rates,
-- enrollments across every lifecycle state.
BEGIN;

INSERT INTO benefits.benefit_plan (plan_id, plan_type, name, country, requires_eoi_above_multiple, default_option) VALUES
  ('eeee0001-0000-4000-8000-000000000001', 'medical', 'PPO Standard',        'US', NULL, 'EE'),
  ('eeee0001-0000-4000-8000-000000000002', 'dental',  'Dental Base',         'US', NULL, 'EE'),
  ('eeee0001-0000-4000-8000-000000000003', 'life',    'Group Term Life',     'US', 3,    '1x'),   -- EOI above 3× salary
  ('eeee0001-0000-4000-8000-000000000004', 'medical', 'GKV Supplement',      'DE', NULL, NULL)    -- waive default (statutory-first)
ON CONFLICT DO NOTHING;

INSERT INTO benefits.benefit_rate
  (rate_id, plan_id, option, age_min, age_max, effective_date, annual_premium, employer_pct) VALUES
  ('eeee0002-0000-4000-8000-000000000001', 'eeee0001-0000-4000-8000-000000000001', 'EE',     0, 120, '2026-01-01',  6000.00, 75.00),
  ('eeee0002-0000-4000-8000-000000000002', 'eeee0001-0000-4000-8000-000000000001', 'EE+FAM', 0, 120, '2026-01-01', 18000.00, 70.00),
  ('eeee0002-0000-4000-8000-000000000003', 'eeee0001-0000-4000-8000-000000000002', 'EE',     0, 120, '2026-01-01',   444.00, 50.00),
  -- age-banded life rates
  ('eeee0002-0000-4000-8000-000000000004', 'eeee0001-0000-4000-8000-000000000003', '1x',     0,  49, '2026-01-01',   120.00, 100.00),
  ('eeee0002-0000-4000-8000-000000000005', 'eeee0001-0000-4000-8000-000000000003', '1x',    50, 120, '2026-01-01',   290.00, 100.00),
  ('eeee0002-0000-4000-8000-000000000006', 'eeee0001-0000-4000-8000-000000000003', '5x',     0,  49, '2026-01-01',   980.00, 0.00)
ON CONFLICT DO NOTHING;

INSERT INTO benefits.enrollment
  (enrollment_id, worker_id, plan_id, option, status, coverage_start, coverage_end, dependents, source) VALUES
  -- Avery: active OE election with dependents (drives the payslip delta story)
  ('eeee0003-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', 'eeee0001-0000-4000-8000-000000000001', 'EE+FAM', 'active', '2026-05-01', NULL,
   '[{"dependent_key":"dep-q-1","relation":"spouse"},{"dependent_key":"dep-q-2","relation":"child"}]', 'oe'),
  ('eeee0003-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222101', 'eeee0001-0000-4000-8000-000000000002', 'EE', 'active', '2026-05-01', NULL, NULL, 'oe'),
  -- Avery elected 5× life above the EOI threshold: pending evidence of insurability
  ('eeee0003-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222101', 'eeee0001-0000-4000-8000-000000000003', '5x', 'pending-eoi', '2026-05-01', NULL, NULL, 'oe'),
  -- Sasha (new hire DE 2026-05-08): waiting period ⇒ coverage first of month
  -- STRICTLY AFTER hire+30 (2026-06-07 → 2026-07-01), defaulted on window expiry
  ('eeee0003-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222105', 'eeee0001-0000-4000-8000-000000000004', 'EE', 'defaulted', '2026-07-01', NULL, NULL, 'default'),
  -- Riley waived dental
  ('eeee0003-0000-4000-8000-000000000005', '22222222-2222-4222-8222-222222222104', 'eeee0001-0000-4000-8000-000000000002', 'EE', 'waived', '2026-01-01', NULL, NULL, 'oe'),
  -- Pat (terminated 2026-04-30): active coverage ended at month end; future OE election cancelled at term date
  ('eeee0003-0000-4000-8000-000000000006', '22222222-2222-4222-8222-222222222109', 'eeee0001-0000-4000-8000-000000000001', 'EE', 'terminated', '2026-01-01', '2026-04-30', NULL, 'oe'),
  ('eeee0003-0000-4000-8000-000000000007', '22222222-2222-4222-8222-222222222109', 'eeee0001-0000-4000-8000-000000000001', 'EE+FAM', 'terminated', '2027-01-01', '2026-04-30', NULL, 'oe')
ON CONFLICT DO NOTHING;

COMMIT;
