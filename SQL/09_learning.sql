-- 09_learning.sql — content versions (supersede policy), compliance
-- assignments (paused leave clock, vendor-outage extension note, corrupt
-- suspend-data demo, contractor lightweight), version-pinned completions
-- (native / import / equivalency), certifications (expiry pipeline, lapsed).
BEGIN;

INSERT INTO learning.content_item (content_id, content_key, title, version, supersede_policy, active) VALUES
  ('adad0001-0000-4000-8000-000000000001', 'harassment-prevention-ca-supervisor', 'CA Harassment Prevention (Supervisor, 2h)', 1, 'finish-old', false),
  ('adad0001-0000-4000-8000-000000000002', 'harassment-prevention-ca-supervisor', 'CA Harassment Prevention (Supervisor, 2h)', 2, 'finish-old', true),
  ('adad0001-0000-4000-8000-000000000003', 'harassment-prevention-ny', 'NY Harassment Prevention (Annual)', 1, 'restart', true),
  ('adad0001-0000-4000-8000-000000000004', 'loto-authorized', 'Lockout/Tagout — Authorized Worker', 1, 'restart', true),
  ('adad0001-0000-4000-8000-000000000005', 'code-of-conduct', 'Code of Conduct', 3, 'finish-old', true)
ON CONFLICT DO NOTHING;

INSERT INTO learning.assignment
  (assignment_id, worker_id, requirement_key, content_key, content_version, status,
   due_on, paused_on, pause_log, extension_note, attempts, suspend_data, suspend_checksum, lightweight) VALUES
  -- Morgan (CA supervisor): in progress on the OLD pinned version (finish-old),
  -- valid suspend data (sha256 matches → clean resume)
  ('adad0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222102', 'us-ca-harassment-supervisor', 'harassment-prevention-ca-supervisor', 1, 'in-progress',
   '2026-06-30', NULL, NULL, NULL, 1, 'lesson=3;score=80', 'e7735e3e5b6d522a9ed62f2944ec589d1c2eab817eb20f1bcad94c2127d08adb', false),
  -- Jordan: clock PAUSED during leave, resumed with credited days in the log
  ('adad0002-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222103', 'us-ny-harassment', 'harassment-prevention-ny', 1, 'assigned',
   '2026-08-12', NULL, '[{"paused_on":"2025-03-10","resumed_on":"2025-05-12","days_credited":63}]', NULL, 0, NULL, NULL, false),
  -- Riley: OVERDUE safety training (consequence: assignment-block flag candidate)
  ('adad0002-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222104', 'osha-lockout-tagout', 'loto-authorized', 1, 'in-progress',
   '2026-06-05', NULL, NULL, NULL, 1, NULL, NULL, false),
  -- Avery: vendor-outage batch extension with the mandatory evidence note
  ('adad0002-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222101', 'us-ny-harassment', 'harassment-prevention-ny', 1, 'assigned',
   '2026-07-07', NULL, NULL, 'vendor outage 2026-06-28..30, ticket VND-112', 0, NULL, NULL, false),
  -- CORRUPT suspend-data demo: checksum deliberately mismatched → resume
  -- falls back to last good checkpoint, attempt counter protected
  ('adad0002-0000-4000-8000-000000000005', '22222222-2222-4222-8222-222222222105', 'code-of-conduct-policy', 'code-of-conduct', 3, 'in-progress',
   '2026-08-06', NULL, NULL, NULL, 1, 'lesson=2;sc', 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', false),
  -- Chris (contingent): LIGHTWEIGHT record, only contingent-applicable pack rows
  ('adad0002-0000-4000-8000-000000000006', '22222222-2222-4222-8222-222222222108', 'us-ca-harassment-nonsupervisor', 'harassment-prevention-ca-1hr', 1, 'assigned',
   '2026-07-31', NULL, NULL, NULL, 0, NULL, NULL, true)
ON CONFLICT DO NOTHING;

INSERT INTO learning.completion_record
  (completion_id, worker_id, requirement_key, content_key, content_version, score,
   completed_at, source, evidence_ref, approved_by) VALUES
  -- native completion PINNING content v1 (audit answer for "which version")
  ('adad0003-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', 'us-ny-harassment', 'harassment-prevention-ny', 1, 95,
   '2025-11-12 16:20+00', 'native', NULL, NULL),
  -- acquired-population IMPORT (compliance-relevant minimum)
  ('adad0003-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222107', 'us-ny-harassment', 'imported', 0, NULL,
   '2025-09-30 12:00+00', 'import', 'legacy://northwind/transcripts/lm-1042', NULL),
  -- EQUIVALENCY: external cert satisfies LOTO, evidence + named approver
  ('adad0003-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222102', 'osha-lockout-tagout', 'external-osha-cert', 0, NULL,
   '2026-02-14 09:00+00', 'equivalency', 'doc://certs/osha-card-demo-7741', 'compliance-officer-1')
ON CONFLICT DO NOTHING;

INSERT INTO learning.certification
  (certification_id, worker_id, cert_type, issuer, issued_on, expires_on, evidence_ref, job_required) VALUES
  -- inside the 90-day alert window
  ('adad0004-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', 'aws-solutions-architect', 'AWS', '2023-09-14', '2026-09-14', 'doc://certs/aws-demo-1', false),
  -- job-required and LAPSED → required-cert-lapsed flag, assignment-block candidate
  ('adad0004-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', 'forklift-license', 'State of TX', '2024-06-01', '2026-06-01', 'doc://certs/forklift-demo-2', true),
  ('adad0004-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222102', 'osha-authorized-loto', 'OSHA trainer', '2026-02-14', '2027-02-14', 'doc://certs/osha-card-demo-7741', true)
ON CONFLICT DO NOTHING;

COMMIT;
