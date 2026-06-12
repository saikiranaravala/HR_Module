-- 07_recruiting.sql — candidates (incl. internal-confidential, do-not-rehire,
-- GDPR-erased), pay-transparency postings, AI rank-and-explain (advisory),
-- OFCCP dispositions, offer negotiation version chain + accepted offer.
BEGIN;

INSERT INTO recruiting.candidate_profile
  (candidate_id, full_name, email, country, internal_worker_id, do_not_rehire, consent_captured_on, erased) VALUES
  ('abab0001-0000-4000-8000-000000000001', 'Taylor Brooks', 'taylor.brooks@example.test', 'US', NULL, false, '2026-05-02', false),
  ('abab0001-0000-4000-8000-000000000002', 'Jamie Fox',     'jamie.fox@example.test',     'US', NULL, false, '2026-05-10', false),
  ('abab0001-0000-4000-8000-000000000003', 'Casey Morgan',  'casey.morgan@example.test',  'US', NULL, false, '2026-05-28', false),
  -- internal candidate (Riley) — confidential application, manager data wall
  ('abab0001-0000-4000-8000-000000000004', 'Riley Chen',    'riley.chen@meridian.example','US', '22222222-2222-4222-8222-222222222104', false, '2026-05-15', false),
  -- former employee with DO-NOT-REHIRE flag (policy-gated visibility, T2)
  ('abab0001-0000-4000-8000-000000000005', 'Drew Hollis',   'drew.hollis@example.test',   'US', '00000000-0000-4000-8000-00000000dead', true, '2026-04-20', false),
  -- GDPR-ERASED candidate: PII nulled in place, flow statistics retained
  ('abab0001-0000-4000-8000-000000000006', NULL, NULL, 'DE', NULL, false, '2025-11-03', true),
  ('abab0001-0000-4000-8000-000000000007', 'Robin Stone',   'robin.stone@example.test',   'DE', NULL, false, '2026-05-20', false)
ON CONFLICT DO NOTHING;

INSERT INTO recruiting.requisition
  (requisition_id, position_id, title, grade, country, jurisdiction, headcount_type,
   status, range_min, range_max, posting_text) VALUES
  ('abab0002-0000-4000-8000-000000000001', '44444444-4444-4444-8444-444444444402', 'Platform Engineer', 'G7', 'US', 'US-CO', 'backfill', 'open',
   80000, 120000, 'Platform Engineer | Salary range: 80000–120000 USD (disclosed per US-CO)'),
  ('abab0002-0000-4000-8000-000000000002', '44444444-4444-4444-8444-444444444403', 'Data Engineer', 'G7', 'DE', 'EU', 'net-new', 'open',
   70000, 95000, 'Data Engineer | Salary range: 70000–95000 EUR (disclosed per EU)'),
  -- cancelled req: its extended offer was rescinded with care (see offers)
  ('abab0002-0000-4000-8000-000000000003', '44444444-4444-4444-8444-444444444402', 'SRE (cancelled)', 'G7', 'US', 'US-TX', 'net-new', 'cancelled',
   85000, 125000, 'SRE')
ON CONFLICT DO NOTHING;

INSERT INTO recruiting.application
  (application_id, candidate_id, requisition_id, stage, status, disposition_code,
   internal, confidential, ai_rank, ai_explanation, applied_on) VALUES
  ('abab0003-0000-4000-8000-000000000001', 'abab0001-0000-4000-8000-000000000001', 'abab0002-0000-4000-8000-000000000001', 'interview', 'active', NULL,
   false, false, 1, '8y K8s + payments scale; matches 9/10 required skills (advisory only)', '2026-05-02'),
  ('abab0003-0000-4000-8000-000000000002', 'abab0001-0000-4000-8000-000000000002', 'abab0002-0000-4000-8000-000000000001', 'screen', 'active', NULL,
   false, false, 2, 'Strong infra background; missing on-call depth', '2026-05-10'),
  -- rejected by a HUMAN with a mandatory OFCCP code
  ('abab0003-0000-4000-8000-000000000003', 'abab0001-0000-4000-8000-000000000003', 'abab0002-0000-4000-8000-000000000001', 'screen', 'rejected', 'not-qualified-min',
   false, false, 3, 'Adjacent experience (SRE)', '2026-05-28'),
  -- internal + confidential: invisible to Riley''s manager (data wall)
  ('abab0003-0000-4000-8000-000000000004', 'abab0001-0000-4000-8000-000000000004', 'abab0002-0000-4000-8000-000000000002', 'screen', 'active', NULL,
   true, true, NULL, NULL, '2026-05-15'),
  -- erased candidate''s application: closed, identity-free flow stats retained
  ('abab0003-0000-4000-8000-000000000005', 'abab0001-0000-4000-8000-000000000006', 'abab0002-0000-4000-8000-000000000002', 'new', 'withdrawn', 'withdrew',
   false, false, NULL, NULL, '2025-11-03'),
  ('abab0003-0000-4000-8000-000000000006', 'abab0001-0000-4000-8000-000000000007', 'abab0002-0000-4000-8000-000000000002', 'offer', 'active', NULL,
   false, false, NULL, NULL, '2026-05-20'),
  -- application on the cancelled req: dispositioned req-cancelled
  ('abab0003-0000-4000-8000-000000000007', 'abab0001-0000-4000-8000-000000000002', 'abab0002-0000-4000-8000-000000000003', 'offer', 'rejected', 'req-cancelled',
   false, false, NULL, NULL, '2026-04-12')
ON CONFLICT DO NOTHING;

INSERT INTO recruiting.offer
  (offer_id, application_id, version, supersedes, base_annual, currency, components,
   status, start_date, requires_comp_approval, rescind_reason, decided_at) VALUES
  -- negotiation chain: v1 superseded by v2; v2 extended (in range)
  ('abab0004-0000-4000-8000-000000000001', 'abab0003-0000-4000-8000-000000000006', 1, NULL, 88000, 'EUR', NULL,
   'rescinded', '2026-08-01', false, 'superseded by negotiation version', '2026-06-05 10:00+00'),
  ('abab0004-0000-4000-8000-000000000002', 'abab0003-0000-4000-8000-000000000006', 2, 'abab0004-0000-4000-8000-000000000001', 92000, 'EUR',
   '{"sign-on": {"amount": 8000, "clawback_months": 12}}', 'extended', '2026-08-01', false, NULL, NULL),
  -- accepted offer (zero re-keying hire payload source) — OUT OF RANGE: comp-approved
  ('abab0004-0000-4000-8000-000000000003', 'abab0003-0000-4000-8000-000000000001', 1, NULL, 121000, 'USD',
   '{"sign-on": {"amount": 10000, "clawback_months": 12}, "relocation": {"amount": 5000}}',
   'accepted', '2026-07-15', true, NULL, '2026-06-09 18:30+00'),
  -- offer rescinded by req cancellation (offers-out register row)
  ('abab0004-0000-4000-8000-000000000004', 'abab0003-0000-4000-8000-000000000007', 1, NULL, 95000, 'USD', NULL,
   'rescinded', '2026-06-01', false, 'requisition cancelled: budget pulled', '2026-04-30 12:00+00')
ON CONFLICT DO NOTHING;

COMMIT;
