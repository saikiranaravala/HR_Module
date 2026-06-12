-- 02_workflow_integration_ai.sql — workflow approvals in flight, integration
-- hub runs/credentials, JML provisioning queue, AI governance ledger.
BEGIN;

-- Workflow: pending approvals matching the unified inbox demo. One step is
-- fallback-routed to role:hr-admin (role-queue inbox feature).
INSERT INTO workflow.workflow_instance
  (instance_id, definition_key, definition_version, subject_ref, initiator,
   status, current_step_index, payload, created_at, correlation_id) VALUES
  ('aaaa0001-0000-4000-8000-000000000001', 'job-change-approval', 2, '22222222-2222-4222-8222-222222222104', 'hr-sam', 'running', 0,
   '{"change":"transfer to Data Platform","effective":"2026-07-01"}', '2026-06-07 09:15+00', 'cccc0000-0000-4000-8000-000000000201'),
  ('aaaa0001-0000-4000-8000-000000000002', 'comp-change-approval', 1, '22222222-2222-4222-8222-222222222103', 'mgr-morgan', 'running', 0,
   '{"merit_pct":9,"new_salary":98100,"out_of_guideline":true}', '2026-06-08 14:02+00', 'cccc0000-0000-4000-8000-000000000202'),
  ('aaaa0001-0000-4000-8000-000000000003', 'job-change-approval', 2, '22222222-2222-4222-8222-222222222105', '22222222-2222-4222-8222-222222222105', 'running', 0,
   '{"change":"FTE 0.8 -> 1.0"}', '2026-06-09 08:40+00', 'cccc0000-0000-4000-8000-000000000203'),
  ('aaaa0001-0000-4000-8000-000000000004', 'job-change-approval', 1, '22222222-2222-4222-8222-222222222109', 'hr-sam', 'completed', 2,
   '{"change":"termination close-out"}', '2026-04-28 10:00+00', 'cccc0000-0000-4000-8000-000000000204')
ON CONFLICT DO NOTHING;

INSERT INTO workflow.step_execution
  (execution_id, instance_id, step_id, step_type, resolved_assignee,
   resolution_reason, status, acted_by, acted_at) VALUES
  ('aaaa0002-0000-4000-8000-000000000001', 'aaaa0001-0000-4000-8000-000000000001', 'manager-approval', 'approval', '22222222-2222-4222-8222-222222222102',
   'levels-up:1 from 22222222-2222-4222-8222-222222222104 → manager', 'pending', NULL, NULL),
  ('aaaa0002-0000-4000-8000-000000000002', 'aaaa0001-0000-4000-8000-000000000002', 'manager-approval', 'approval', '22222222-2222-4222-8222-222222222106',
   'levels-up:1; skipped initiator (self-approval blocked) → skip-level', 'pending', NULL, NULL),
  -- chain exhausted -> fallback role queue (visible via inbox roles=("hr-admin",))
  ('aaaa0002-0000-4000-8000-000000000003', 'aaaa0001-0000-4000-8000-000000000003', 'manager-approval', 'approval', 'role:hr-admin',
   'levels-up:1 exhausted → fallback-role:hr-admin', 'pending', NULL, NULL),
  ('aaaa0002-0000-4000-8000-000000000004', 'aaaa0001-0000-4000-8000-000000000004', 'manager-approval', 'approval', '22222222-2222-4222-8222-222222222102',
   'levels-up:1', 'approved', '22222222-2222-4222-8222-222222222102', '2026-04-28 16:21+00'),
  ('aaaa0002-0000-4000-8000-000000000005', 'aaaa0001-0000-4000-8000-000000000004', 'notify-worker', 'notification', NULL,
   'auto-completed (non-approval step)', 'done', 'engine', '2026-04-28 16:21+00')
ON CONFLICT DO NOTHING;

-- Integration hub: connector runs (one normalized failure), a credential
-- expiring inside the 30-day alert window, JML provisioning actions.
INSERT INTO integration.connector_run
  (run_id, connector_key, started_at, finished_at, status, record_count, error_normalized, correlation_id) VALUES
  ('aaaa0003-0000-4000-8000-000000000001', 'adp-payfile-out',    '2026-06-10 02:00+00', '2026-06-10 02:04+00', 'succeeded', 8200, NULL, 'cccc0000-0000-4000-8000-000000000211'),
  ('aaaa0003-0000-4000-8000-000000000002', 'carrier-834-out',    '2026-06-10 03:00+00', '2026-06-10 03:01+00', 'failed', 0, 'AUTH_EXPIRED: partner certificate rejected', 'cccc0000-0000-4000-8000-000000000212'),
  ('aaaa0003-0000-4000-8000-000000000003', 'idp-scim-provision', '2026-06-11 06:00+00', '2026-06-11 06:00+00', 'succeeded', 3, NULL, 'cccc0000-0000-4000-8000-000000000213')
ON CONFLICT DO NOTHING;

INSERT INTO integration.connector_credential
  (credential_id, connector_key, credential_kind, reference, expires_on) VALUES
  ('aaaa0004-0000-4000-8000-000000000001', 'carrier-834-out',    'mtls-cert',  'vault://demo/carrier-834/cert',  '2026-07-05'),  -- inside alert window
  ('aaaa0004-0000-4000-8000-000000000002', 'adp-payfile-out',    'api-key',    'vault://demo/adp/key',           '2027-01-31'),
  ('aaaa0004-0000-4000-8000-000000000003', 'idp-scim-provision', 'oauth-client','vault://demo/idp/client',       '2026-12-31')
ON CONFLICT DO NOTHING;

INSERT INTO integration.provisioning_action
  (action_id, worker_id, action_type, effective_ts, attributes, status, alert_raised, applied_at) VALUES
  ('aaaa0005-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222105', 'joiner-day1', '2026-05-08 06:00+00',
   '{"idp":"activate","badge":"issue","learn":["code-of-conduct"]}', 'applied', false, '2026-05-08 06:02+00'),
  -- leaver access kill: applied within SLA, no alert
  ('aaaa0005-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222109', 'leaver-access-kill', '2026-04-30 22:00+00',
   '{"idp":"deactivate","badge":"revoke"}', 'applied', false, '2026-04-30 22:01+00'),
  -- pending mover re-provisioning for the 2026-07-01 transfer
  ('aaaa0005-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222101', 'mover-reprovision', '2026-07-01 06:00+00',
   '{"groups":["data-platform-eng"],"revoke":["platform-eng-oncall"]}', 'queued', false, NULL)
ON CONFLICT DO NOTHING;

-- AI ledger: every gateway call logged — ok, PII refusal, budget refusal.
INSERT INTO ai.ai_ledger
  (entry_id, occurred_at, use_case, subject_id, purpose, model, prompt_version,
   status, refusal_reason, request_chars, correlation_id) VALUES
  ('aaaa0006-0000-4000-8000-000000000001', '2026-06-11 09:12+00', 'policy-qa-copilot', '22222222-2222-4222-8222-222222222101',
   'Answer policy questions from governed corpus with citations', 'mock-opus', '1.0.0', 'ok', NULL, 64, 'cccc0000-0000-4000-8000-000000000221'),
  ('aaaa0006-0000-4000-8000-000000000002', '2026-06-11 09:14+00', 'policy-qa-copilot', '22222222-2222-4222-8222-222222222104',
   'Answer policy questions from governed corpus with citations', NULL, NULL, 'refused', 'third-party-pii-detected', 118, 'cccc0000-0000-4000-8000-000000000222'),
  ('aaaa0006-0000-4000-8000-000000000003', '2026-06-10 17:40+00', 'resume-rank-explain', 'recruiter-lead-1',
   'Rank-and-explain candidate-requisition fit; never auto-reject', 'mock-opus', '1.0.0', 'ok', NULL, 412, 'cccc0000-0000-4000-8000-000000000223'),
  ('aaaa0006-0000-4000-8000-000000000004', '2026-06-09 11:05+00', 'review-draft-assist', '22222222-2222-4222-8222-222222222102',
   'Draft self/manager review narratives from goals + check-in history; labeled, edit-required; no rating surface', 'mock-opus', '1.0.0', 'ok', NULL, 230, 'cccc0000-0000-4000-8000-000000000224')
ON CONFLICT DO NOTHING;

COMMIT;
