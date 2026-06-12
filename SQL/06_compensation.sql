-- 06_compensation.sql — temporal ranges (incl. a refresh), comp records
-- written with the REAL uuid5 comp keys the services compute
-- (uuid5(NAMESPACE_URL, 'meridian:comp:<worker_id>:<role>')), FY26 cycle with
-- locked FX and a worksheet showing out-of-guideline + skip-level routing.
BEGIN;

INSERT INTO comp.grade_range
  (range_key, effective_date, effective_sequence, action_code, action_reason,
   created_by, source_channel, correlation_id,
   grade, country, currency, range_min, range_mid, range_max) VALUES
  ('G7:US', '2025-01-01', 0, 'insert', 'annual-structure', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000301', 'G7', 'US', 'USD', 80000, 100000, 120000),
  -- RANGE REFRESH eff 2026-07-01: raises min — Jordan (90k? no: below-min demo uses 88k)
  ('G7:US', '2026-07-01', 0, 'insert', 'range-refresh',    'seed', 'seed', 'cccc0000-0000-4000-8000-000000000302', 'G7', 'US', 'USD', 90000, 110000, 130000),
  ('G8:US', '2025-01-01', 0, 'insert', 'annual-structure', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000303', 'G8', 'US', 'USD', 100000, 125000, 150000),
  ('G7:DE', '2025-01-01', 0, 'insert', 'annual-structure', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000304', 'G7', 'DE', 'EUR', 62000, 78000, 94000),
  ('F3:FR', '2025-01-01', 0, 'insert', 'annual-structure', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000305', 'F3', 'FR', 'EUR', 85000, 105000, 125000)
ON CONFLICT DO NOTHING;

-- Comp records (temporal). comp_key values are deterministic uuid5 results:
--   Avery  home        89501b44-bf1d-5a3f-b836-7b9ba8332d67
--   Jordan home        26c284a6-b266-541c-b3c1-3076ddd98bd1
--   Riley  home        3fca9c90-ddde-55ee-8838-29d4c06c0180
--   Lena   home        d81ef967-ab8c-538e-87a5-bf4d2a23bd8d
--   Lena   host-shadow 72a4eadf-333e-53b8-b2d7-11408cf408f9
INSERT INTO comp.comp_record
  (comp_key, effective_date, effective_sequence, action_code, action_reason,
   created_by, source_channel, correlation_id,
   worker_id, record_role, base_annual, currency, grade, country, fte) VALUES
  -- Avery: hire → promotion → SAME-DAY correction (seq 1 wins) → current 100k
  ('89501b44-bf1d-5a3f-b836-7b9ba8332d67', '2021-03-15', 0, 'insert', 'hire',      'seed', 'seed', 'cccc0000-0000-4000-8000-000000000311', '22222222-2222-4222-8222-222222222101', 'home',  82000.00, 'USD', 'G7', 'US', 1.00),
  ('89501b44-bf1d-5a3f-b836-7b9ba8332d67', '2024-04-01', 0, 'insert', 'promotion', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000312', '22222222-2222-4222-8222-222222222101', 'home',  95000.00, 'USD', 'G7', 'US', 1.00),
  ('89501b44-bf1d-5a3f-b836-7b9ba8332d67', '2024-04-01', 1, 'update-correction', 'merit', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000313', '22222222-2222-4222-8222-222222222101', 'home',  96500.00, 'USD', 'G7', 'US', 1.00),
  ('89501b44-bf1d-5a3f-b836-7b9ba8332d67', '2025-04-01', 0, 'insert', 'merit',     'seed', 'seed', 'cccc0000-0000-4000-8000-000000000314', '22222222-2222-4222-8222-222222222101', 'home', 100000.00, 'USD', 'G7', 'US', 1.00),
  -- Jordan: below the refreshed 2026-07-01 min ⇒ remediation-list candidate
  ('26c284a6-b266-541c-b3c1-3076ddd98bd1', '2022-02-14', 0, 'insert', 'rehire',    'seed', 'seed', 'cccc0000-0000-4000-8000-000000000315', '22222222-2222-4222-8222-222222222103', 'home',  84000.00, 'USD', 'G7', 'US', 1.00),
  ('26c284a6-b266-541c-b3c1-3076ddd98bd1', '2025-09-01', 0, 'insert', 'merit',     'seed', 'seed', 'cccc0000-0000-4000-8000-000000000316', '22222222-2222-4222-8222-222222222103', 'home',  88000.00, 'USD', 'G7', 'US', 1.00),
  ('3fca9c90-ddde-55ee-8838-29d4c06c0180', '2022-09-06', 0, 'insert', 'hire',      'seed', 'seed', 'cccc0000-0000-4000-8000-000000000317', '22222222-2222-4222-8222-222222222104', 'home', 102000.00, 'USD', 'G7', 'US', 1.00),
  -- Lena: DUAL-CURRENCY EXPAT — home record of record (FR/EUR) + DE host shadow
  ('d81ef967-ab8c-538e-87a5-bf4d2a23bd8d', '2026-01-01', 0, 'insert', 'expat-assignment', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000318', '22222222-2222-4222-8222-222222222107', 'home',       105000.00, 'EUR', 'F3', 'FR', 1.00),
  ('72a4eadf-333e-53b8-b2d7-11408cf408f9', '2026-01-01', 0, 'insert', 'expat-assignment', 'seed', 'seed', 'cccc0000-0000-4000-8000-000000000319', '22222222-2222-4222-8222-222222222107', 'host-shadow', 98000.00, 'EUR', 'F3', 'DE', 1.00)
ON CONFLICT DO NOTHING;

INSERT INTO comp.comp_cycle (cycle_id, name, status, corporate_currency, fx_rates, budget_pool, opened_at) VALUES
  ('ffff0001-0000-4000-8000-000000000001', 'FY26 Merit', 'open', 'USD',
   '{"EUR": 1.10, "GBP": 1.27}', 18000.00, '2026-04-01 08:00+00')
ON CONFLICT DO NOTHING;

INSERT INTO comp.cycle_line
  (line_id, cycle_id, worker_id, manager_id, snapshot, merit_pct, justification, out_of_guideline, status) VALUES
  -- Jordan: OUT-OF-GUIDELINE 9% with mandatory justification, flagged for approval
  ('ffff0002-0000-4000-8000-000000000001', 'ffff0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222103', '22222222-2222-4222-8222-222222222102',
   '{"salary": 88000, "currency": "USD", "rating": "exceeds", "compa_quartile": 1}', 9.00, 'retention risk; critical event-layer skill set', true, 'draft'),
  ('ffff0002-0000-4000-8000-000000000002', 'ffff0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222104', '22222222-2222-4222-8222-222222222102',
   '{"salary": 102000, "currency": "USD", "rating": "meets", "compa_quartile": 3}', 2.50, NULL, false, 'draft'),
  ('ffff0002-0000-4000-8000-000000000003', 'ffff0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222105', '22222222-2222-4222-8222-222222222102',
   '{"salary": 70000, "currency": "EUR", "rating": "meets", "compa_quartile": 2}', NULL, NULL, false, 'draft'),
  -- Morgan's own record: SELF-RECOMMENDATION BLOCKED → routed to skip-level
  ('ffff0002-0000-4000-8000-000000000004', 'ffff0001-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222102', '22222222-2222-4222-8222-222222222102',
   '{"salary": 150000, "currency": "USD", "rating": "meets", "compa_quartile": 3}', NULL, NULL, false, 'routed-skip-level')
ON CONFLICT DO NOTHING;

COMMIT;
