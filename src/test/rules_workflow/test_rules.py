"""Rules engine tests (Specs/12 §3) including register rows:
overlap/gap detection and rule-vs-transaction effective dating."""
from datetime import date

import pytest

from rules_workflow.rules import (
    RulesetValidationError,
    evaluate,
    load_ruleset,
    run_golden,
    validate_ruleset,
)

RULESET = load_ruleset("overtime-eligibility")


def test_basic_match_and_default():
    hit = evaluate(RULESET, {"country": "US", "weekly_hours": 45}, date(2026, 2, 1))
    miss = evaluate(RULESET, {"country": "US", "weekly_hours": 38}, date(2026, 2, 1))
    assert hit.output == "overtime-1.5x"
    assert miss.output == "not-eligible" and miss.matched_rule_index is None


def test_PLAT_rule_version_selected_by_txn_effective_date():
    """Register row: the rule version is chosen by the TRANSACTION's effective
    date, not the evaluation date. A DE 50-hour week is a WTD breach only under
    v2 (effective 2026-07-01)."""
    inputs = {"country": "DE", "weekly_hours": 50}
    before = evaluate(RULESET, inputs, date(2026, 6, 30))
    after = evaluate(RULESET, inputs, date(2026, 7, 1))
    assert before.version == 1 and before.output == "not-eligible"
    assert after.version == 2 and after.output == "overtime-de-wtd-breach"


def test_PLAT_decision_table_overlap_detected():
    bad = {
        "ruleset": "x",
        "versions": [{
            "version": 1, "effective_date": "2026-01-01",
            "inputs": ["country", "hours"], "output": "d", "default": "n",
            "rules": [
                {"when": {"country": "US", "hours": {"gt": 40}}, "then": "a"},
                {"when": {"country": "US", "hours": {"gte": 50}}, "then": "b"},  # overlaps > 50
            ],
        }],
    }
    with pytest.raises(RulesetValidationError, match="overlap"):
        validate_ruleset(bad)


def test_PLAT_decision_table_gap_detected():
    gappy = {
        "ruleset": "x",
        "versions": [{
            "version": 1, "effective_date": "2026-01-01",
            "inputs": ["hours"], "output": "d",  # no default ⇒ coverage required
            "domains": {"hours": {"min": 0, "max": 80}},
            "rules": [
                {"when": {"hours": {"gte": 0, "lt": 20}}, "then": "a"},
                {"when": {"hours": {"gte": 30, "lte": 80}}, "then": "b"},  # 20–30 uncovered
            ],
        }],
    }
    with pytest.raises(RulesetValidationError, match="gap"):
        validate_ruleset(gappy)


def test_no_version_effective_before_first():
    from rules_workflow.rules import NoRuleVersionError
    with pytest.raises(NoRuleVersionError):
        evaluate(RULESET, {"country": "US", "weekly_hours": 45}, date(2025, 1, 1))


def test_golden_dataset_runner():
    cases = [
        {"inputs": {"country": "US", "weekly_hours": 41}, "transaction_date": "2026-02-01", "expected": "overtime-1.5x"},
        {"inputs": {"country": "FR", "weekly_hours": 36}, "transaction_date": "2026-02-01", "expected": "overtime-fr-statutory"},
        {"inputs": {"country": "DE", "weekly_hours": 50}, "transaction_date": "2026-08-01", "expected": "overtime-de-wtd-breach"},
        {"inputs": {"country": "JP", "weekly_hours": 60}, "transaction_date": "2026-08-01", "expected": "not-eligible"},
    ]
    assert run_golden(RULESET, cases) == []  # 100% pass gates promotion
