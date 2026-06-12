-- 04_payroll.sql — Payroll Integration Hub: cycle state machine per country,
-- immutable input snapshots (hash sealed), held inputs, provider results
-- (incl. a negative-net arrears case — the PAY register row).
BEGIN;

INSERT INTO payroll.pay_cycle
  (cycle_id, country, pay_group, period_key, state, off_cycle, snapshot_hash,
   compiled_by, approved_by, gross_total, state_changed_at) VALUES
  ('dddd0001-0000-4000-8000-000000000001', 'US', 'US-SEMI', '2026-06B', 'inputs-compiled', false,
   'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'payroll-ops-1', NULL, 1264500.00, '2026-06-11 04:10+00'),
  ('dddd0001-0000-4000-8000-000000000002', 'DE', 'DE-MON',  '2026-06',  'transmitted', false,
   '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae', 'payroll-ops-2', NULL, 812400.00, '2026-06-10 16:00+00'),
  ('dddd0001-0000-4000-8000-000000000003', 'UK', 'UK-MON',  '2026-06',  'results-reconciled', false,
   'fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9', 'payroll-ops-2', 'payroll-lead-1', 498200.00, '2026-06-11 09:30+00'),
  -- off-cycle: final-pay supplement run for the terminated worker
  ('dddd0001-0000-4000-8000-000000000004', 'US', 'US-SEMI', '2026-05-OFF1', 'released', true,
   'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'payroll-ops-1', 'payroll-lead-1', 1890.00, '2026-05-22 12:00+00')
ON CONFLICT DO NOTHING;

INSERT INTO payroll.pay_input_record (input_id, cycle_id, worker_id, payload, held, hold_reason) VALUES
  ('dddd0002-0000-4000-8000-000000000001', 'dddd0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222101',
   '{"elements":[{"code":"REG","hours":86.67,"rate":48.08},{"code":"MED-EEFAM","amount":-225.00},{"code":"401K","pct":6}]}', false, NULL),
  ('dddd0002-0000-4000-8000-000000000002', 'dddd0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222104',
   '{"elements":[{"code":"REG","hours":80.0,"rate":38.33},{"code":"OT15","hours":2.5,"rate":57.50}]}', false, NULL),
  -- HELD input: bank change inside the pre-payday freeze window (fraud interlock)
  ('dddd0002-0000-4000-8000-000000000003', 'dddd0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222103',
   '{"elements":[{"code":"REG","hours":86.67,"rate":43.27}]}', true, 'bank-change within 3-day payday freeze; out-of-band confirmation pending'),
  ('dddd0002-0000-4000-8000-000000000004', 'dddd0001-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222105',
   '{"elements":[{"code":"REG","hours":138.67,"rate":28.85}]}', false, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO payroll.pay_result_record (result_id, cycle_id, worker_id, gross, total_deductions, net, elements) VALUES
  ('dddd0003-0000-4000-8000-000000000001', 'dddd0001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222107',
   7333.33, 2411.18, 4922.15, '[{"code":"REG","amount":7333.33},{"code":"TAX","amount":-2105.40},{"code":"PEN","amount":-305.78}]'),
  -- NEGATIVE NET (arrears) register case: deductions exceed gross on a partial period
  ('dddd0003-0000-4000-8000-000000000002', 'dddd0001-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222109',
   210.00, 268.40, -58.40, '[{"code":"REG","amount":210.00},{"code":"MED-ARREARS","amount":-180.00},{"code":"TAX","amount":-88.40}]'),
  ('dddd0003-0000-4000-8000-000000000003', 'dddd0001-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222109',
   1890.00, 412.30, 1477.70, '[{"code":"FINAL-PAY-SUPPLEMENT","amount":1890.00},{"code":"TAX","amount":-412.30}]')
ON CONFLICT DO NOTHING;

COMMIT;
