-- 03_time_labor.sql — punches (incl. midnight-spanning + DST), locked compile
-- results with a retro delta pair (reconciliation identity), accrual lots
-- (FIFO with expiring carryover, negative-balance flag carried on worker).
BEGIN;

INSERT INTO time_labor.time_entry
  (entry_id, worker_id, person_id, in_utc, out_utc, timezone_name, work_date, pay_group, country, state) VALUES
  -- regular Austin day
  ('bbbb0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222104', '11111111-1111-4111-8111-111111111104',
   '2026-06-08 13:00+00', '2026-06-08 22:30+00', 'America/Chicago', '2026-06-08', 'US-SEMI', 'US', 'TX'),
  -- MIDNIGHT-SPANNING shift: attributed to the LOCAL shift-start date (register row)
  ('bbbb0001-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', '11111111-1111-4111-8111-111111111104',
   '2026-06-10 23:00+00', '2026-06-11 07:00+00', 'America/Chicago', '2026-06-10', 'US-SEMI', 'US', 'TX'),
  -- DST transition day (US spring-forward 2026-03-08): 23-hour local day, elapsed from UTC
  ('bbbb0001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222101', '11111111-1111-4111-8111-111111111101',
   '2026-03-08 06:00+00', '2026-03-08 14:00+00', 'America/Chicago', '2026-03-08', 'US-SEMI', 'US', 'TX'),
  -- DE worker (monthly group)
  ('bbbb0001-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222105', '11111111-1111-4111-8111-111111111105',
   '2026-06-09 07:00+00', '2026-06-09 13:30+00', 'Europe/Berlin', '2026-06-09', 'DE-MON', 'DE', NULL)
ON CONFLICT DO NOTHING;

-- Locked period compile + retro delta lineage:
-- original + delta = recalculated (the payroll-path reconciliation identity).
INSERT INTO time_labor.time_result
  (result_id, worker_id, period_key, pay_group, earnings_code, hours, rate,
   is_retro_delta, origin_result_id, explanation, locked) VALUES
  ('bbbb0002-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222104', '2026-05B', 'US-SEMI', 'REG', 80.00, 38.3300, false, NULL,
   'regular hours · US-FLSA weekly-40 v3', true),
  ('bbbb0002-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222104', '2026-05B', 'US-SEMI', 'OT15', 2.50, 57.5000, false, NULL,
   '2.5h over weekly-40 @1.5x · US-FLSA weekly-40 v3', true),
  -- retro: rate corrected after lock — delta row references the original
  ('bbbb0002-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222104', '2026-05B', 'US-SEMI', 'OT15', 0.00, 1.2500, true,
   'bbbb0002-0000-4000-8000-000000000002', 'retro rate correction +1.25/h on locked 2026-05B; original immutable', false),
  ('bbbb0002-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222101', '2026-05B', 'US-SEMI', 'REG', 86.67, 48.0800, false, NULL,
   'salaried proration · semi-monthly', true)
ON CONFLICT DO NOTHING;

INSERT INTO time_labor.accrual_lot
  (lot_id, worker_id, absence_type, granted_on, hours_granted, hours_consumed, expires_on) VALUES
  -- Avery: FIFO lots — expiring carryover is consumed first
  ('bbbb0003-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101', 'pto',  '2026-01-01', 24.00, 0.00, '2026-06-30'),  -- carryover, expiring
  ('bbbb0003-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222101', 'pto',  '2026-01-01', 160.00, 28.00, NULL),
  ('bbbb0003-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222101', 'sick', '2026-01-01', 192.00, 0.00, NULL),
  -- Riley: negative balance situation (limit guard demo; worker carries the flag)
  ('bbbb0003-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222104', 'pto',  '2026-01-01', 120.00, 128.00, NULL),
  -- Sasha DE: statutory grant
  ('bbbb0003-0000-4000-8000-000000000005', '22222222-2222-4222-8222-222222222105', 'pto',  '2026-05-08', 160.00, 0.00, NULL)
ON CONFLICT DO NOTHING;

COMMIT;
