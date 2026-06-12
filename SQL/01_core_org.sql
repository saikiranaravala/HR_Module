-- 01_core_org.sql — Core HR: persons, names, IDs, workers, org, assignments.
-- Demonstrates the temporal pattern (Invariant #1): EFFDT/EFFSEQ history,
-- same-day correction (seq 1), retro row, future-dated transfer.
--
-- Fixed UUID scheme (referenced by every later file):
--   persons      1111....11NN      workers   2222....22NN
--   departments  3333....33NN      positions 4444....44NN
--   NN: 01 Avery Quinn (US)   02 Morgan Lee (US, manager)
--       03 Jordan Patel (US)  04 Riley Chen (US)
--       05 Sasha Kim (DE)     06 Dana Whitfield (US, VP)
--       07 Lena Moreau (FR→DE expat)  08 Chris Vega (US contingent)
--       09 Pat Novak (US, terminated alumni)
BEGIN;

INSERT INTO core.person (person_id, date_of_birth, primary_nationality) VALUES
  ('11111111-1111-4111-8111-111111111101', '1986-04-12', 'US'),
  ('11111111-1111-4111-8111-111111111102', '1979-09-30', 'US'),
  ('11111111-1111-4111-8111-111111111103', '1991-01-22', 'US'),
  ('11111111-1111-4111-8111-111111111104', '1993-07-08', 'US'),
  ('11111111-1111-4111-8111-111111111105', '1997-11-02', 'DE'),
  ('11111111-1111-4111-8111-111111111106', '1972-03-15', 'US'),
  ('11111111-1111-4111-8111-111111111107', '1983-06-27', 'FR'),
  ('11111111-1111-4111-8111-111111111108', '1989-12-05', 'US'),
  ('11111111-1111-4111-8111-111111111109', '1981-08-19', 'US')
ON CONFLICT DO NOTHING;

-- Temporal names: Avery has a verified legal name change (marriage) in 2024.
INSERT INTO core.person_name
  (person_id, effective_date, effective_sequence, action_code, action_reason,
   created_by, source_channel, correlation_id,
   given_name, family_name, formatted_name, legal_doc_verified) VALUES
  ('11111111-1111-4111-8111-111111111101', '2021-03-15', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000001', 'Avery',  'Sanders',   'Avery Sanders',   true),
  ('11111111-1111-4111-8111-111111111101', '2024-08-01', 0, 'insert', 'name-change',     'seed', 'seed', 'cccc0000-0000-4000-8000-000000000002', 'Avery',  'Quinn',     'Avery Quinn',     true),
  ('11111111-1111-4111-8111-111111111102', '2015-06-01', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000003', 'Morgan', 'Lee',       'Morgan Lee',      true),
  ('11111111-1111-4111-8111-111111111103', '2022-02-14', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000004', 'Jordan', 'Patel',     'Jordan Patel',    true),
  ('11111111-1111-4111-8111-111111111104', '2022-09-06', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000005', 'Riley',  'Chen',      'Riley Chen',      true),
  ('11111111-1111-4111-8111-111111111105', '2026-05-08', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000006', 'Sasha',  'Kim',       'Sasha Kim',       true),
  ('11111111-1111-4111-8111-111111111106', '2010-01-11', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000007', 'Dana',   'Whitfield', 'Dana Whitfield',  true),
  ('11111111-1111-4111-8111-111111111107', '2018-04-03', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-000000000008', 'Lena',   'Moreau',    'Lena Moreau',     true),
  ('11111111-1111-4111-8111-111111111108', '2026-02-02', 0, 'insert', 'contingent-start','seed', 'seed', 'cccc0000-0000-4000-8000-000000000009', 'Chris',  'Vega',      'Chris Vega',      false),
  ('11111111-1111-4111-8111-111111111109', '2017-10-09', 0, 'insert', 'hire',           'seed', 'seed', 'cccc0000-0000-4000-8000-00000000000a', 'Pat',    'Novak',     'Pat Novak',       true)
ON CONFLICT DO NOTHING;

-- Synthetic national IDs only: SSN 900-xx range is reserved/invalid by design.
-- value_encrypted holds an obvious placeholder, never a real ciphertext.
INSERT INTO core.national_id (national_id_pk, person_id, id_type, value_encrypted, last_four) VALUES
  ('55555555-5555-4555-8555-555555555101', '11111111-1111-4111-8111-111111111101', 'US-SSN',     'enc:demo:not-a-real-ciphertext:900-00-0101', '0101'),
  ('55555555-5555-4555-8555-555555555102', '11111111-1111-4111-8111-111111111102', 'US-SSN',     'enc:demo:not-a-real-ciphertext:900-00-0102', '0102'),
  ('55555555-5555-4555-8555-555555555105', '11111111-1111-4111-8111-111111111105', 'DE-SteuerID','enc:demo:not-a-real-ciphertext:00-000-105',  '0105')
ON CONFLICT DO NOTHING;

INSERT INTO core.work_eligibility (eligibility_id, person_id, country, document_type, expiry_date) VALUES
  ('66666666-6666-4666-8666-666666666101', '11111111-1111-4111-8111-111111111101', 'US', 'citizen',     NULL),
  ('66666666-6666-4666-8666-666666666105', '11111111-1111-4111-8111-111111111105', 'DE', 'eu-national', NULL),
  ('66666666-6666-4666-8666-666666666107', '11111111-1111-4111-8111-111111111107', 'DE', 'work-permit', '2027-03-31')  -- expat permit with expiry
ON CONFLICT DO NOTHING;

INSERT INTO core.worker
  (worker_id, person_id, legal_entity, entity_country, worker_type, hire_date, original_hire_date, carried_flags) VALUES
  ('22222222-2222-4222-8222-222222222101', '11111111-1111-4111-8111-111111111101', 'Meridian US Inc',  'US', 'employee',   '2021-03-15', '2021-03-15', NULL),
  ('22222222-2222-4222-8222-222222222102', '11111111-1111-4111-8111-111111111102', 'Meridian US Inc',  'US', 'employee',   '2015-06-01', '2015-06-01', NULL),
  -- Jordan is a REHIRE: bridged original hire date retained (rehire-bridging).
  ('22222222-2222-4222-8222-222222222103', '11111111-1111-4111-8111-111111111103', 'Meridian US Inc',  'US', 'employee',   '2022-02-14', '2019-05-20', NULL),
  ('22222222-2222-4222-8222-222222222104', '11111111-1111-4111-8111-111111111104', 'Meridian US Inc',  'US', 'employee',   '2022-09-06', '2022-09-06', 'negative-pto-balance'),
  ('22222222-2222-4222-8222-222222222105', '11111111-1111-4111-8111-111111111105', 'Meridian DE GmbH', 'DE', 'employee',   '2026-05-08', '2026-05-08', NULL),
  ('22222222-2222-4222-8222-222222222106', '11111111-1111-4111-8111-111111111106', 'Meridian US Inc',  'US', 'employee',   '2010-01-11', '2010-01-11', NULL),
  ('22222222-2222-4222-8222-222222222107', '11111111-1111-4111-8111-111111111107', 'Meridian FR SAS',  'FR', 'employee',   '2018-04-03', '2018-04-03', NULL),
  ('22222222-2222-4222-8222-222222222108', '11111111-1111-4111-8111-111111111108', 'Meridian US Inc',  'US', 'contingent', '2026-02-02', '2026-02-02', NULL),
  ('22222222-2222-4222-8222-222222222109', '11111111-1111-4111-8111-111111111109', 'Meridian US Inc',  'US', 'employee',   '2017-10-09', '2017-10-09', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO core.department (department_id, name, parent_id, status) VALUES
  ('33333333-3333-4333-8333-333333333303', 'Engineering',      NULL,                                   'active'),
  ('33333333-3333-4333-8333-333333333301', 'Platform Eng',     '33333333-3333-4333-8333-333333333303', 'active'),
  ('33333333-3333-4333-8333-333333333302', 'Data Platform',    '33333333-3333-4333-8333-333333333303', 'active'),
  ('33333333-3333-4333-8333-333333333304', 'Finance EMEA',     NULL,                                   'active'),
  ('33333333-3333-4333-8333-333333333305', 'Field Operations', NULL,                                   'inactive')  -- inactivated dept (blocked while staffed rule)
ON CONFLICT DO NOTHING;

INSERT INTO core.position (position_id, job_code, department_id, headcount_budget, status) VALUES
  ('44444444-4444-4444-8444-444444444401', 'ENG2', '33333333-3333-4333-8333-333333333301', 4, 'active'),
  ('44444444-4444-4444-8444-444444444402', 'ENG1', '33333333-3333-4333-8333-333333333301', 6, 'active'),
  ('44444444-4444-4444-8444-444444444403', 'ENG2', '33333333-3333-4333-8333-333333333302', 2, 'active'),
  ('44444444-4444-4444-8444-444444444404', 'FIN3', '33333333-3333-4333-8333-333333333304', 1, 'active')
ON CONFLICT DO NOTHING;

-- Assignments: the temporal job series. Avery shows hire → promotion +
-- SAME-DAY comp-change correction (seq 1) → FUTURE transfer. Jordan shows a
-- RETRO leave row inserted after a later record existed. Pat is terminated.
INSERT INTO core.assignment
  (worker_id, effective_date, effective_sequence, action_code, action_reason,
   created_by, source_channel, correlation_id,
   worker_status, job_code, department_id, position_id, manager_worker_id,
   location_country, fte, pay_group) VALUES
  -- Avery Quinn
  ('22222222-2222-4222-8222-222222222101', '2021-03-15', 0, 'insert',            'hire',        'seed', 'seed', 'cccc0000-0000-4000-8000-000000000101', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222101', '2024-04-01', 0, 'insert',            'promotion',   'seed', 'seed', 'cccc0000-0000-4000-8000-000000000102', 'active', 'ENG2', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444401', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222101', '2024-04-01', 1, 'update-correction', 'merit',       'seed', 'seed', 'cccc0000-0000-4000-8000-000000000103', 'active', 'ENG2', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444401', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222101', '2026-07-01', 0, 'insert',            'org-transfer','seed', 'seed', 'cccc0000-0000-4000-8000-000000000104', 'active', 'ENG2', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444403', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  -- Morgan Lee (manager) / Dana Whitfield (VP)
  ('22222222-2222-4222-8222-222222222102', '2015-06-01', 0, 'insert', 'hire', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000105', 'active', 'MGR3', '33333333-3333-4333-8333-333333333301', NULL, '22222222-2222-4222-8222-222222222106', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222106', '2010-01-11', 0, 'insert', 'hire', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000106', 'active', 'VP1',  '33333333-3333-4333-8333-333333333303', NULL, NULL, 'US', 1.00, 'US-SEMI'),
  -- Jordan Patel: rehire 2022, then a RETRO leave row keyed before an existing later row
  ('22222222-2222-4222-8222-222222222103', '2022-02-14', 0, 'insert',       'rehire',       'seed', 'seed', 'cccc0000-0000-4000-8000-000000000107', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222103', '2025-09-01', 0, 'insert',       'merit',        'seed', 'seed', 'cccc0000-0000-4000-8000-000000000108', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222103', '2025-03-10', 0, 'insert-retro', 'leave-start',  'seed', 'seed', 'cccc0000-0000-4000-8000-000000000109', 'leave',  'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222103', '2025-05-12', 0, 'insert-retro', 'leave-return', 'seed', 'seed', 'cccc0000-0000-4000-8000-00000000010a', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  -- Riley, Sasha (DE), Lena (expat: FR home entity, DE host assignment), Chris (contingent)
  ('22222222-2222-4222-8222-222222222104', '2022-09-06', 0, 'insert', 'hire',             'seed', 'seed', 'cccc0000-0000-4000-8000-00000000010b', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222105', '2026-05-08', 0, 'insert', 'hire',             'seed', 'seed', 'cccc0000-0000-4000-8000-00000000010c', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444402', '22222222-2222-4222-8222-222222222102', 'DE', 0.80, 'DE-MON'),
  ('22222222-2222-4222-8222-222222222107', '2026-01-01', 0, 'insert', 'expat-assignment', 'seed', 'seed', 'cccc0000-0000-4000-8000-00000000010d', 'active', 'FIN3', '33333333-3333-4333-8333-333333333304', '44444444-4444-4444-8444-444444444404', '22222222-2222-4222-8222-222222222106', 'DE', 1.00, 'DE-MON'),
  ('22222222-2222-4222-8222-222222222108', '2026-02-02', 0, 'insert', 'contingent-start', 'seed', 'seed', 'cccc0000-0000-4000-8000-00000000010e', 'active', 'ENG1', '33333333-3333-4333-8333-333333333301', NULL, '22222222-2222-4222-8222-222222222102', 'US', 1.00, NULL),
  -- Pat Novak: terminated 2026-04-30 (feeds alumni access + analytics exit)
  ('22222222-2222-4222-8222-222222222109', '2017-10-09', 0, 'insert', 'hire',        'seed', 'seed', 'cccc0000-0000-4000-8000-00000000010f', 'active',     'ENG2', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444401', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI'),
  ('22222222-2222-4222-8222-222222222109', '2026-04-30', 0, 'insert', 'termination', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000110', 'terminated', 'ENG2', '33333333-3333-4333-8333-333333333301', '44444444-4444-4444-8444-444444444401', '22222222-2222-4222-8222-222222222102', 'US', 1.00, 'US-SEMI')
ON CONFLICT DO NOTHING;

COMMIT;
