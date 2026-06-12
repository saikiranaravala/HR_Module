-- 10_service_delivery.sql — cases (incl. ER-segregated T3 with transcript),
-- internal vs employee-visible notes, KB lifecycle (published / stale /
-- legal-review), delegations, notification prefs, alumni grant + legal hold.
BEGIN;

INSERT INTO service_delivery."case"
  (case_id, worker_id, topic, queue, priority, status, description, transcript,
   opened_at, sla_due_at, closed_at, satisfaction) VALUES
  ('aeae0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', 'payslip', 'payroll', 'high', 'open',
   'Net pay lower than expected this period.',
   '[{"role":"user","text":"Why is my net pay lower?"},{"role":"assistant","text":"Your OE elections started this cycle…"}]',
   '2026-06-11 08:12+00', '2026-06-11 16:12+00', NULL, NULL),
  ('aeae0001-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222105', 'enrollment', 'benefits', 'medium', 'open',
   'Question about GKV supplement default.', NULL, '2026-06-10 16:40+00', '2026-06-11 16:40+00', NULL, NULL),
  -- ER-SEGREGATED case (T3): restricted queue, investigation workspace
  ('aeae0001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222104', 'investigation', 'er', 'critical', 'open',
   'post-start background adverse finding: license verification failed', NULL,
   '2026-06-09 11:00+00', '2026-06-09 15:00+00', NULL, NULL),
  -- closed case with CSAT
  ('aeae0001-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222103', 'leave', 'benefits', 'medium', 'closed',
   'FMLA eligibility question.', NULL, '2026-05-02 09:00+00', '2026-05-03 09:00+00', '2026-05-02 14:30+00', 5)
ON CONFLICT DO NOTHING;

INSERT INTO service_delivery.case_note (note_id, case_id, author, visibility, body, created_at) VALUES
  ('aeae0002-0000-4000-8000-000000000001', 'aeae0001-0000-4000-8000-000000000001', 'agent-rivera', 'internal',
   'Cross-checked element diff — OE medical EE+FAM started 05-01. Drafting reply.', '2026-06-11 09:00+00'),
  ('aeae0002-0000-4000-8000-000000000002', 'aeae0001-0000-4000-8000-000000000001', 'agent-rivera', 'employee',
   'Your medical election (EE+FAM) began this cycle — that is the difference. Breakdown attached.', '2026-06-11 09:05+00')
ON CONFLICT DO NOTHING;

INSERT INTO service_delivery.kb_article
  (article_id, title, body, country, population, version, status, is_policy, published_on, review_due) VALUES
  ('aeae0003-0000-4000-8000-000000000001', 'US family & medical leave', 'US workers: FMLA provides up to 12 weeks unpaid, job-protected leave.', 'US', 'all', 3, 'published', true, '2026-01-01', '2027-01-01'),
  ('aeae0003-0000-4000-8000-000000000002', 'DE Elternzeit', 'DE workers: Elternzeit per BEEG, up to 3 years parental leave.', 'DE', 'all', 2, 'published', true, '2026-01-01', '2027-01-01'),
  -- STALE article (review_due passed → stale-content alert)
  ('aeae0003-0000-4000-8000-000000000003', 'US commuter benefits', 'Pre-tax transit details…', 'US', 'all', 1, 'published', false, '2025-05-01', '2026-05-01'),
  -- policy article waiting at the LEGAL-REVIEW gate
  ('aeae0003-0000-4000-8000-000000000004', 'US remote-work stipend policy', 'Draft policy text…', 'US', 'salaried', 1, 'in-legal-review', true, NULL, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO service_delivery.delegation
  (delegation_id, delegator, delegate, scope_types, starts_on, ends_on, revoked) VALUES
  -- Morgan delegates time/absence (NOT comp) to Dana for vacation — ≤30 days
  ('aeae0004-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222102', '22222222-2222-4222-8222-222222222106',
   '["time", "absence"]', '2026-06-15', '2026-06-26', false),
  ('aeae0004-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222106', '22222222-2222-4222-8222-222222222102',
   '["time"]', '2026-03-01', '2026-03-10', true)
ON CONFLICT DO NOTHING;

INSERT INTO service_delivery.notification_pref
  (pref_id, worker_id, notif_type, channels, quiet_start, quiet_end, personal_channel_consent) VALUES
  -- account-level prefs with quiet hours
  ('aeae0005-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', NULL, NULL, 22, 7, true),
  -- per-type override (mandatory types like bank-change-alert ignore it)
  ('aeae0005-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222101', 'payslip-published', '["push"]', NULL, NULL, true),
  -- frontline contractor: personal channels NOT consented → SMS/personal dropped
  ('aeae0005-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222108', NULL, NULL, NULL, NULL, false)
ON CONFLICT DO NOTHING;

INSERT INTO service_delivery.access_grant
  (grant_id, worker_id, kind, scope, reason, starts_on, expires_on, released) VALUES
  -- Pat: ALUMNI limited-scope access (payslip/tax-doc only) for US retention window
  ('aeae0006-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222109', 'alumni',
   '["payslip", "tax-doc"]', NULL, '2026-04-30', '2029-04-30', false),
  -- Riley: ACTIVE LEGAL HOLD — self-service changes frozen with neutral messaging
  ('aeae0006-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', 'legal-hold',
   NULL, 'litigation hold LH-2026-014 (reason never shown to worker)', '2026-06-01', NULL, false)
ON CONFLICT DO NOTHING;

COMMIT;
