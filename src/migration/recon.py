"""Reconciliation workbench (MIG-3): field-match gates, recompute-and-compare
with rule-vs-data triage, variance taxonomy, immutable signed gate artifacts."""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from migration.models import GateArtifact

CRITICAL_FIELD_MATCH_GATE = Decimal("0.9995")  # the 99.95% wave-entry gate

# Variance taxonomy (§4): real differences vs explainable environment ones.
VARIANCE_KINDS = ("data-difference", "rule-difference", "env-difference", "rounding")


def field_match(ps_rows: dict[str, dict], meridian_rows: dict[str, dict],
                *, critical_fields: list[str]) -> dict:
    """Count + field-match per domain run: per-field rates over shared keys."""
    shared = sorted(set(ps_rows) & set(meridian_rows))
    missing = sorted(set(ps_rows) - set(meridian_rows))
    rates = {}
    mismatches = []
    for field in critical_fields:
        matched = sum(
            1 for key in shared
            if ps_rows[key].get(field) == meridian_rows[key].get(field)
        )
        rates[field] = Decimal(matched) / Decimal(len(shared)) if shared else Decimal(0)
        for key in shared:
            if ps_rows[key].get(field) != meridian_rows[key].get(field):
                mismatches.append({"key": key, "field": field,
                                   "ps": ps_rows[key].get(field),
                                   "meridian": meridian_rows[key].get(field)})
    overall = min(rates.values()) if rates else Decimal(0)
    return {"count_ps": len(ps_rows), "count_meridian": len(meridian_rows),
            "missing_in_meridian": missing, "rates": rates,
            "overall_critical_rate": overall, "mismatches": mismatches,
            "gate_passed": overall >= CRITICAL_FIELD_MATCH_GATE and not missing}


def recompute_triage(*, ps_balance: Decimal, meridian_balance: Decimal,
                     meridian_rule_version: str, ps_rule_version: str) -> dict:
    """Accrual recompute-and-compare (§4): same rule version + different value
    = data problem; different rule versions = rule difference to adjudicate."""
    if ps_balance == meridian_balance:
        return {"variance": Decimal("0"), "kind": None}
    kind = ("rule-difference" if meridian_rule_version != ps_rule_version
            else "data-difference")
    return {"variance": meridian_balance - ps_balance, "kind": kind,
            "needs": "rules adjudication" if kind == "rule-difference"
                     else "source data correction"}


def classify_pay_variance(*, ps_net: Decimal, provider_net: Decimal,
                          provider_env: str) -> dict:
    """Payroll three-way variance with the env-difference class: provider
    test environments are contractually shadow-run but fidelity gaps exist —
    those must never masquerade as real payroll errors (risk register)."""
    variance = provider_net - ps_net
    if variance == 0:
        return {"variance": variance, "kind": None}
    if abs(variance) <= Decimal("0.01"):
        return {"variance": variance, "kind": "rounding"}
    if provider_env != "production-parallel":
        return {"variance": variance, "kind": "env-difference",
                "note": f"provider env '{provider_env}' lacks production fidelity; "
                        "re-verify against production-parallel before gating"}
    return {"variance": variance, "kind": "data-difference"}


def sign_gate_artifact(session: Session, *, wave: str, gate: str, passed: bool,
                       report: dict, signed_by: str) -> GateArtifact:
    """Immutable signed gate report — content-hashed (UTC canonical), DB-guarded."""
    signed_at = datetime.now(timezone.utc)
    content = json.dumps({"wave": wave, "gate": gate, "passed": passed,
                          "report": report, "signed_at": signed_at.isoformat()},
                         sort_keys=True, default=str)
    artifact = GateArtifact(
        wave=wave, gate=gate, passed=passed, report=report,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        signed_by=signed_by, signed_at=signed_at,
    )
    session.add(artifact)
    session.flush()
    return artifact
