-- 13_migration.sql — migration factory: idempotent staging, DQ steward queue
-- (fix-at-source guidance), signed immutable gate artifact, sync conflicts
-- (open within SLA + parked by the kill-switch).
BEGIN;

INSERT INTO migration.staged_record (staged_id, batch_id, source_key, domain, payload, loaded) VALUES
  ('a2a20001-0000-4000-8000-000000000001', 'b-2026-06-w2', 'PS-1001', 'job-history',
   '{"worker_ref": "PS-1001", "effective_date": "2015-03-01", "action_code": "hire", "job_code": "ENG1"}', true),
  ('a2a20001-0000-4000-8000-000000000002', 'b-2026-06-w2', 'PS-1001:2018-07-01:1', 'job-history',
   '{"worker_ref": "PS-1001", "effective_date": "2018-07-01", "effective_sequence": 1, "action_code": "comp-change", "job_code": "ENG2"}', true),
  ('a2a20001-0000-4000-8000-000000000003', 'b-2026-06-w2', 'PS-1002', 'person',
   '{"worker_ref": "PS-1002", "country": "US"}', false),
  ('a2a20001-0000-4000-8000-000000000004', 'b-2026-06-w2', 'PS-1003', 'job-history',
   '{"worker_ref": "PS-1003", "effective_date": "2020-01-15", "action_code": "hire", "job_code": null}', false)
ON CONFLICT DO NOTHING;

INSERT INTO migration.dq_exception (exception_id, batch_id, domain, rule, source_ref, guidance, status) VALUES
  ('a2a20002-0000-4000-8000-000000000001', 'b-2026-06-w2', 'job-history', 'completeness', 'PS-1003',
   'populate ''job_code'' in PeopleSoft (source-correct, not in-flight)', 'open'),
  ('a2a20002-0000-4000-8000-000000000002', 'b-2026-06-w1', 'person', 'referential', 'PS-0988',
   '''worker_ref''=''PS-0988'' unknown in target — verify rehire bridging', 'fixed-at-source'),
  ('a2a20002-0000-4000-8000-000000000003', 'b-2026-06-w1', 'job-history', 'validity', 'PS-0712',
   '''action_code''=''XYZ'' has no taxonomy mapping — semantic review queued', 'waived')
ON CONFLICT DO NOTHING;

-- Signed wave gate artifact: immutable (DB trigger), content-hashed.
INSERT INTO migration.gate_artifact
  (artifact_id, wave, gate, passed, report, content_hash, signed_by, signed_at) VALUES
  ('a2a20003-0000-4000-8000-000000000001', 'wave-1-NL', 'entry', true,
   '{"field_match": "0.9997", "missing_in_meridian": 0, "penny_perfect_cycles": 3, "dq": {"completeness": 0.999, "validity": 0.998}}',
   '7d9f1f2b6a3c4e5d8b9a0c1d2e3f40516273849500aabbccddeeff0011223344', 'program-director', '2026-06-01 18:00+00'),
  ('a2a20003-0000-4000-8000-000000000002', 'wave-0-pilot-US-BU1', 'exit', true,
   '{"penny_perfect_cycles": 3, "txn_error_rate": 0.003, "csat": 4.4, "sev1_sync_incidents_30d": 0}',
   '11aa22bb33cc44dd55ee66ff7788990011aabb22cc33dd44ee55ff6677889900', 'program-director', '2026-05-15 17:00+00')
ON CONFLICT DO NOTHING;

INSERT INTO migration.sync_conflict
  (conflict_id, worker_ref, field, ps_value, meridian_value, detected_at, sla_due_at, status, resolution) VALUES
  -- open conflict inside the 4-hour SLA (pilot dual-entry phase)
  ('a2a20004-0000-4000-8000-000000000001', 'PS-1001', 'address', '12 Old Rd, Denver CO', '88 New Ave, Denver CO',
   '2026-06-12 08:30+00', '2026-06-12 12:30+00', 'open', NULL),
  -- resolved per ownership matrix (meridian owns address in phase B)
  ('a2a20004-0000-4000-8000-000000000002', 'PS-1042', 'emergency_contact', 'old contact', 'new contact',
   '2026-06-10 10:00+00', '2026-06-10 14:00+00', 'resolved', 'ownership-matrix: meridian wins (pilot-dual-entry)'),
  -- PARKED by the kill-switch during a sev-1 (loud halt, never quiet)
  ('a2a20004-0000-4000-8000-000000000003', 'PS-0907', 'job_code', 'ENG1', 'ENG2',
   '2026-05-28 09:00+00', '2026-05-28 13:00+00', 'parked', 'kill-switch: sev-1 sync incident INC-3321')
ON CONFLICT DO NOTHING;

COMMIT;
