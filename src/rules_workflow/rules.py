"""Decision-table rules engine (Specs/12 §3).

Rule sets are versioned, effective-dated YAML. Evaluation is a pure function:
no I/O, guaranteed termination. The version applied to a transaction is chosen
by the TRANSACTION's effective date — rules are temporal data too.

Save-time validation rejects overlapping rules and (for declared numeric
domains without a default) coverage gaps.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent / "config" / "rulesets"

_NUMERIC_OPS = {"gt", "gte", "lt", "lte"}


class RulesetValidationError(ValueError):
    pass


class NoRuleVersionError(LookupError):
    pass


@dataclass(frozen=True)
class Evaluation:
    output: object
    version: int
    matched_rule_index: int | None  # None ⇒ default applied
    explanation: str


def load_ruleset(name: str, base_dir: Path = CONFIG_DIR) -> dict:
    path = base_dir / f"{name}.yaml"
    ruleset = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_ruleset(ruleset)
    return ruleset


def validate_ruleset(ruleset: dict) -> None:
    if "ruleset" not in ruleset or not ruleset.get("versions"):
        raise RulesetValidationError("ruleset requires 'ruleset' name and 'versions'")
    for version in ruleset["versions"]:
        for key in ("version", "effective_date", "inputs", "output"):
            if key not in version:
                raise RulesetValidationError(f"version missing '{key}'")
        _detect_overlap(version)
        _detect_gaps(version)


def _conditions_overlap(cond_a: dict, cond_b: dict, inputs: list[str]) -> bool:
    """Two rules overlap when some input assignment satisfies both."""
    for field in inputs:
        spec_a, spec_b = cond_a.get(field), cond_b.get(field)
        if spec_a is None or spec_b is None:
            continue  # unconstrained on this field ⇒ compatible
        if not _specs_intersect(spec_a, spec_b):
            return False
    return True


def _specs_intersect(spec_a, spec_b) -> bool:
    def as_interval(spec):
        low, high = float("-inf"), float("inf")
        low_closed = high_closed = True
        if isinstance(spec, dict):
            if "gt" in spec:
                low, low_closed = spec["gt"], False
            if "gte" in spec:
                low = spec["gte"]
            if "lt" in spec:
                high, high_closed = spec["lt"], False
            if "lte" in spec:
                high = spec["lte"]
            return low, high, low_closed, high_closed
        return None

    scalar_a = not isinstance(spec_a, dict) or "in" in spec_a
    scalar_b = not isinstance(spec_b, dict) or "in" in spec_b
    if scalar_a and scalar_b:
        set_a = set(spec_a["in"]) if isinstance(spec_a, dict) else {spec_a}
        set_b = set(spec_b["in"]) if isinstance(spec_b, dict) else {spec_b}
        return bool(set_a & set_b)
    if scalar_a or scalar_b:
        # enum vs numeric range: check each enum value against the interval
        enum_spec, range_spec = (spec_a, spec_b) if scalar_a else (spec_b, spec_a)
        values = set(enum_spec["in"]) if isinstance(enum_spec, dict) else {enum_spec}
        return any(
            isinstance(v, (int, float)) and _value_in_interval(v, as_interval(range_spec))
            for v in values
        )
    a, b = as_interval(spec_a), as_interval(spec_b)
    low = max(a[0], b[0])
    high = min(a[1], b[1])
    return low < high or (low == high and _closed_at(a, b, low))


def _closed_at(a, b, point) -> bool:
    a_ok = (point > a[0] or (point == a[0] and a[2])) and (point < a[1] or (point == a[1] and a[3]))
    b_ok = (point > b[0] or (point == b[0] and b[2])) and (point < b[1] or (point == b[1] and b[3]))
    return a_ok and b_ok


def _value_in_interval(value, interval) -> bool:
    low, high, low_closed, high_closed = interval
    if value < low or (value == low and not low_closed):
        return False
    if value > high or (value == high and not high_closed):
        return False
    return True


def _detect_overlap(version: dict) -> None:
    rules = version.get("rules", [])
    inputs = version["inputs"]
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            if _conditions_overlap(rules[i]["when"], rules[j]["when"], inputs):
                raise RulesetValidationError(
                    f"version {version['version']}: rules {i} and {j} overlap"
                )


def _detect_gaps(version: dict) -> None:
    """For a single numeric input with a declared domain and no default,
    contiguous range coverage is required."""
    if version.get("default") is not None:
        return
    domains = version.get("domains", {})
    for field, domain in domains.items():
        if not isinstance(domain, dict) or "min" not in domain:
            continue
        intervals = []
        for rule in version.get("rules", []):
            spec = rule["when"].get(field)
            if spec is None:
                return  # an unconstrained rule covers everything
            if isinstance(spec, dict) and (_NUMERIC_OPS & set(spec)):
                low = spec.get("gte", spec.get("gt", float("-inf")))
                high = spec.get("lte", spec.get("lt", float("inf")))
                intervals.append((low, high))
        intervals.sort()
        cursor = domain["min"]
        for low, high in intervals:
            if low > cursor:
                raise RulesetValidationError(
                    f"version {version['version']}: gap in '{field}' coverage near {cursor}"
                )
            cursor = max(cursor, high)
        if cursor < domain["max"]:
            raise RulesetValidationError(
                f"version {version['version']}: '{field}' uncovered above {cursor}"
            )


def select_version(ruleset: dict, transaction_date: date) -> dict:
    """Latest version effective on the transaction's effective date."""
    candidates = [
        v for v in ruleset["versions"]
        if _as_date(v["effective_date"]) <= transaction_date
    ]
    if not candidates:
        raise NoRuleVersionError(
            f"{ruleset['ruleset']}: no version effective on {transaction_date}"
        )
    return max(candidates, key=lambda v: (_as_date(v["effective_date"]), v["version"]))


def _as_date(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _matches(condition: dict, inputs: dict) -> bool:
    for field, spec in condition.items():
        value = inputs.get(field)
        if isinstance(spec, dict):
            if "in" in spec:
                if value not in spec["in"]:
                    return False
            elif _NUMERIC_OPS & set(spec):
                if value is None:
                    return False
                if "gt" in spec and not value > spec["gt"]:
                    return False
                if "gte" in spec and not value >= spec["gte"]:
                    return False
                if "lt" in spec and not value < spec["lt"]:
                    return False
                if "lte" in spec and not value <= spec["lte"]:
                    return False
            else:
                raise RulesetValidationError(f"unknown condition spec for '{field}': {spec}")
        elif value != spec:
            return False
    return True


def evaluate(ruleset: dict, inputs: dict, transaction_date: date) -> Evaluation:
    version = select_version(ruleset, transaction_date)
    for index, rule in enumerate(version.get("rules", [])):
        if _matches(rule["when"], inputs):
            return Evaluation(
                output=rule["then"],
                version=version["version"],
                matched_rule_index=index,
                explanation=f"v{version['version']} rule[{index}] matched {rule['when']}",
            )
    if version.get("default") is not None:
        return Evaluation(
            output=version["default"],
            version=version["version"],
            matched_rule_index=None,
            explanation=f"v{version['version']} default applied",
        )
    raise NoRuleVersionError(
        f"{ruleset['ruleset']} v{version['version']}: no rule matched and no default"
    )


def run_golden(ruleset: dict, cases: list[dict]) -> list[dict]:
    """Golden-dataset regression: returns failures (empty list = 100% pass)."""
    failures = []
    for case in cases:
        result = evaluate(ruleset, case["inputs"], _as_date(case["transaction_date"]))
        if result.output != case["expected"]:
            failures.append({**case, "actual": result.output, "explanation": result.explanation})
    return failures
