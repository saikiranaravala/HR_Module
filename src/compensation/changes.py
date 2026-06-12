"""Comp change transactions (COMP-1 §2) and the promo+merit / retro / expat
register behaviors. All comp writes go through insert_temporal (Invariant #1)."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from compensation import structures
from compensation.models import CompRecord, comp_key
from platform_core import temporal

REASONS = {"merit", "promotion", "market", "equity-adjustment", "demotion"}
COMP_TEAM_APPROVAL_PCT = Decimal("12")  # > this ⇒ comp-team approval


class InvalidReasonError(ValueError):
    pass


@dataclass
class ChangeResult:
    record: CompRecord
    requires_comp_team_approval: bool = False
    approval_reasons: list[str] = field(default_factory=list)
    payroll_elements: list[dict] = field(default_factory=list)


def apply_change(
    session: Session, *, worker_id: str, new_salary: Decimal, reason: str,
    effective_date: date, actor: str, worker_terminated_on: date | None = None,
    record_role: str = "home",
) -> ChangeResult:
    if reason not in REASONS:
        raise InvalidReasonError(f"'{reason}' is not in the reason taxonomy {sorted(REASONS)}")

    previous = structures.current_comp(session, worker_id, as_of=effective_date,
                                       record_role=record_role)
    if previous is None:
        raise LookupError(f"no comp record for {worker_id} as of {effective_date}")

    approval_reasons = []
    pct = ((new_salary - previous.base_annual) / previous.base_annual * 100).quantize(Decimal("0.01"))
    if pct > COMP_TEAM_APPROVAL_PCT:
        approval_reasons.append(f"increase {pct}% exceeds {COMP_TEAM_APPROVAL_PCT}% cap")
    rng = structures.range_as_of(session, grade=previous.grade,
                                 country=previous.country, as_of=effective_date)
    if rng is not None and not (rng.range_min <= new_salary <= rng.range_max):
        approval_reasons.append("out of range for grade")

    row = CompRecord(
        comp_key=comp_key(worker_id, record_role), worker_id=worker_id,
        record_role=record_role, base_annual=new_salary, currency=previous.currency,
        grade=previous.grade, country=previous.country, fte=previous.fte,
        effective_date=effective_date, action_code="insert", action_reason=reason,
    )
    temporal.insert_temporal(session, row, actor=actor, source_channel="comp-change")

    elements = []
    if worker_terminated_on is not None and effective_date <= worker_terminated_on:
        # Register row: retro merit after termination → the base change is a
        # retro temporal row; pay lands as a FINAL-PAY SUPPLEMENT element, not
        # a regular ongoing earnings change.
        owed_delta = new_salary - previous.base_annual
        elements.append({
            "element": "final-pay-supplement",
            "reason": reason,
            "basis_delta_annual": owed_delta,
            "currency": previous.currency,
            "off_cycle": True,
        })
    else:
        elements.append({
            "element": "base-salary",
            "annual": new_salary,
            "currency": previous.currency,
            "effective_date": effective_date.isoformat(),
        })
    return ChangeResult(record=row, requires_comp_team_approval=bool(approval_reasons),
                        approval_reasons=approval_reasons, payroll_elements=elements)


def promote_with_merit(
    session: Session, *, worker_id: str, new_grade: str, merit_pct: Decimal,
    promotion_pct: Decimal, effective_date: date, actor: str,
) -> ChangeResult:
    """Register row: promotion + merit in one cycle. Pinned sequencing:
    1. merit % applies to the PRE-promotion salary,
    2. promotion % applies on top,
    3. range validation runs against the NEW grade's range."""
    current = structures.current_comp(session, worker_id, as_of=effective_date)
    if current is None:
        raise LookupError(f"no comp record for {worker_id}")
    merited = current.base_annual * (1 + merit_pct / 100)
    promoted = (merited * (1 + promotion_pct / 100)).quantize(Decimal("0.01"))

    new_range = structures.range_as_of(session, grade=new_grade,
                                       country=current.country, as_of=effective_date)
    approval_reasons = []
    if new_range is not None and not (new_range.range_min <= promoted <= new_range.range_max):
        approval_reasons.append("result outside new grade range")

    row = CompRecord(
        comp_key=comp_key(worker_id), worker_id=worker_id, record_role="home",
        base_annual=promoted, currency=current.currency, grade=new_grade,
        country=current.country, fte=current.fte,
        effective_date=effective_date, action_code="insert",
        action_reason="promotion",  # merit folded per sequencing rule
    )
    temporal.insert_temporal(session, row, actor=actor, source_channel="comp-change")
    return ChangeResult(record=row, requires_comp_team_approval=bool(approval_reasons),
                        approval_reasons=approval_reasons,
                        payroll_elements=[{"element": "base-salary", "annual": promoted,
                                           "currency": current.currency,
                                           "effective_date": effective_date.isoformat()}])


def create_expat_split(
    session: Session, *, worker_id: str, effective_date: date, actor: str,
    home: dict, host: dict,
) -> tuple[CompRecord, CompRecord]:
    """Register row: dual-currency expats. The HOME record is the comp record
    of record (drives metrics/payroll basis); the HOST shadow mirrors the
    delivery-currency view and never doubles headcount or pay."""
    rows = []
    for role, spec in (("home", home), ("host-shadow", host)):
        row = CompRecord(
            comp_key=comp_key(worker_id, role), worker_id=worker_id, record_role=role,
            base_annual=spec["base_annual"], currency=spec["currency"],
            grade=spec["grade"], country=spec["country"], fte=spec.get("fte", Decimal("1")),
            effective_date=effective_date, action_code="insert", action_reason="expat-assignment",
        )
        temporal.insert_temporal(session, row, actor=actor, source_channel="comp-change")
        rows.append(row)
    return rows[0], rows[1]
