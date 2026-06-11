---
name: edge-case-tests
description: Convert a domain PRD's Edge Cases Register into named, mandatory test scenarios. Use when writing the test plan or test suite for any module — the register is the module's exit gate.
---

# Edge-Case Register → Test Suite

Every domain PRD in `Specs/` carries an **Edge Cases Register** (penultimate section). Per `CLAUDE.md`, these are mandatory test scenarios — a module cannot reach `Done` in `Progress.md` until every register row is a passing named test.

## Steps

1. **Read the register** in `Specs/NN-<module>.md` (e.g., `## 8. Edge Cases Register`). Also read `## Open Questions` — an edge case that depends on an open decision gets a test marked as blocked-by-gate, not silently skipped.
2. **Name each test** after its domain and scenario: `test_<DOMAIN>_<scenario_snake_case>` — e.g., `test_PAY_negative_net_arrears`, `test_CORE_multi_job_cross_entity`, `test_TIME_dst_transition_overnight_shift`. The name must let a reader find the register row without a lookup table.
3. **For each test, derive from the register row:** setup (synthetic data only — reserved/invalid ranges for national IDs and bank numbers), action, expected outcome, and the requirement ID it exercises.
4. **Standard cross-cutting cases to add even if the register omits them** (they apply to every module):
   - Same-day double change (effective-sequence ordering).
   - Retroactive change → retro event emitted, downstream recompute correct.
   - As-of query straddling the change boundary.
   - Policy denial consistency: the same record denied in UI is denied via API, report, and AI tool path.
   - Idempotent event redelivery (consumer processes a duplicate without side effects).
5. **Payroll-path modules** (02, 03) additionally require reconciliation identity tests (original + retro delta = recalculated) and snapshot immutability tests.
6. **Produce a coverage table** (register row → test name → status) in the module's design doc or test README, and update `Progress.md` with the count: `edge-cases: 14/17 passing, 2 blocked-by-gate, 1 failing`.

## Rule

A register row may only be excluded with an explicit, written reason reviewed by the user — never dropped because it's hard to set up.
