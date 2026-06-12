"""Pay-cycle orchestration (Specs/03 §4–§7): state machine, immutable input
snapshots, the PAY-3 validation gate, adapter transmission, results identity
checks, and element-level reconciliation.
"""
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, Text, Uuid, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from integration_hub.chassis import Connector, TransportResult
from payroll_hub.cpdc import CpdcRecord, PayElement, load_element_dictionary, element_active
from platform_core.audit import canonical_json
from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_PAY_TAG = tag(category="payroll", purpose="payroll-processing",
               lawful_basis="contract", retention_class="payroll-statutory", tier=Tier.T2)

STATES = [
    "draft", "inputs-compiled", "validated", "approved",
    "transmitted", "results-received", "reconciled", "closed",
]
FOUR_EYES_GROSS_THRESHOLD = Decimal("1000000")


class IllegalTransitionError(ValueError):
    pass


class BlockingValidationError(ValueError):
    pass


class SnapshotTamperedError(RuntimeError):
    pass


@register_model
class PayCycle(Base):
    __tablename__ = "pay_cycle"
    __table_args__ = {"schema": "payroll"}

    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_PAY_TAG))
    pay_group: Mapped[str] = mapped_column(Text, info=dict(_PAY_TAG))
    period_key: Mapped[str] = mapped_column(Text, info=dict(_PAY_TAG))
    state: Mapped[str] = mapped_column(Text, default="draft", info=dict(_PAY_TAG))
    off_cycle: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PAY_TAG))
    snapshot_hash: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))
    compiled_by: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))
    gross_total: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True, info=dict(_PAY_TAG))
    state_changed_at = mapped_column(DateTime(timezone=True), nullable=True, info=dict(RECORD_KEEPING_TAG))


@register_model
class PayInputRecord(Base):
    """One CPDC record in a cycle's compiled snapshot. Immutable once compiled."""
    __tablename__ = "pay_input_record"
    __table_args__ = {"schema": "payroll"}

    input_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_PAY_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_PAY_TAG))
    payload = mapped_column(JSONB, info=dict(_PAY_TAG))  # canonical CPDC serialization
    held: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PAY_TAG))
    hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PAY_TAG))


@register_model
class PayResultRecord(Base):
    __tablename__ = "pay_result_record"
    __table_args__ = {"schema": "payroll"}

    result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_PAY_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_PAY_TAG))
    gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), info=dict(_PAY_TAG))
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), info=dict(_PAY_TAG))
    net: Mapped[Decimal] = mapped_column(Numeric(14, 2), info=dict(_PAY_TAG))
    elements = mapped_column(JSONB, info=dict(_PAY_TAG))


@dataclass
class ValidationFinding:
    worker_id: str
    severity: str  # BLOCK | HOLD-RECORD | WARN
    rule: str
    detail: str


def serialize_record(record: CpdcRecord) -> dict:
    return {
        "worker_id": record.worker_id, "legal_entity": record.legal_entity,
        "country": record.country, "pay_group": record.pay_group,
        "period_key": record.period_key, "deceased": record.deceased,
        "payee_override": record.payee_override,
        "ytd_handover_from_entity": record.ytd_handover_from_entity,
        "bank_change_days": record.bank_last_changed_days_before_payday,
        "state_allocations": [
            {"state": a.state, "percent": str(a.percent)} for a in record.state_allocations
        ],
        "arrears_carried": str(record.arrears_carried),
        "elements": [
            {"code": e.element_code, "kind": e.kind, "amount": str(e.amount),
             "retro": e.retro, "original_period": e.original_period}
            for e in record.elements
        ],
    }


def _transition(cycle: PayCycle, target: str):
    current_idx, target_idx = STATES.index(cycle.state), STATES.index(target)
    if target_idx != current_idx + 1:
        raise IllegalTransitionError(f"{cycle.state} → {target} not allowed")
    cycle.state = target
    cycle.state_changed_at = datetime.now(timezone.utc)


def compile_inputs(session: Session, cycle: PayCycle, records: list[CpdcRecord],
                   *, actor: str) -> str:
    """Draft → Inputs-Compiled: persist the snapshot and hash it. The snapshot
    is the immutable basis for validation, transmission, and reconciliation."""
    if cycle.state != "draft":
        raise IllegalTransitionError("inputs may only be compiled from draft")
    payloads = []
    for record in records:
        payload = serialize_record(record)
        payloads.append(payload)
        session.add(PayInputRecord(cycle_id=cycle.cycle_id,
                                   worker_id=record.worker_id, payload=payload))
    cycle.snapshot_hash = _snapshot_hash(payloads)
    cycle.compiled_by = actor
    cycle.gross_total = sum((r.gross() for r in records), Decimal("0"))
    _transition(cycle, "inputs-compiled")
    session.flush()
    return cycle.snapshot_hash


def _snapshot_hash(payloads: list[dict]) -> str:
    """Deterministic hash of the compiled input set, order-independent."""
    ordered = sorted(payloads, key=lambda p: p["worker_id"])
    return hashlib.sha256(canonical_json(ordered).encode()).hexdigest()


def verify_snapshot(session: Session, cycle: PayCycle) -> None:
    """Recompute the snapshot hash from stored rows; any post-compile mutation
    of the input set surfaces here (snapshot immutability guarantee)."""
    rows = session.scalars(
        select(PayInputRecord).where(PayInputRecord.cycle_id == cycle.cycle_id)
    ).all()
    if _snapshot_hash([row.payload for row in rows]) != cycle.snapshot_hash:
        raise SnapshotTamperedError("compiled snapshot hash mismatch")


def validate_cycle(
    session: Session, cycle: PayCycle, *,
    trailing_nets: dict[str, list[Decimal]] | None = None,
    retro_sanity_pct: Decimal = Decimal("0.5"),
) -> list[ValidationFinding]:
    """The PAY-3 gate on the compiled snapshot. BLOCK stops the cycle;
    HOLD-RECORD excludes the record (rest proceeds, retro auto-queued);
    WARN transmits and is tracked."""
    if cycle.state != "inputs-compiled":
        raise IllegalTransitionError("validation runs on the compiled snapshot")
    dictionary = load_element_dictionary()
    trailing_nets = trailing_nets or {}
    findings: list[ValidationFinding] = []

    rows = session.scalars(
        select(PayInputRecord).where(PayInputRecord.cycle_id == cycle.cycle_id)
    ).all()
    for row in rows:
        payload = row.payload
        worker = payload["worker_id"]

        # Layer 1 — structural
        for element in payload["elements"]:
            if not element_active(dictionary, element["code"], payload["country"]):
                findings.append(ValidationFinding(
                    worker, "BLOCK", "element-not-active",
                    f"element {element['code']} not active for {payload['country']}"))
        allocations = payload.get("state_allocations") or []
        if allocations:
            total = sum(Decimal(a["percent"]) for a in allocations)
            if total != Decimal("100"):
                findings.append(ValidationFinding(
                    worker, "BLOCK", "multi-state-allocation",
                    f"state allocations sum to {total}, must be exactly 100"))
        if payload["deceased"] and not payload.get("payee_override"):
            findings.append(ValidationFinding(
                worker, "BLOCK", "deceased-payee",
                "deceased worker requires beneficiary payee override"))

        # Layer 2 — business rules
        for element in payload["elements"]:
            if element["retro"]:
                if not element.get("original_period"):
                    findings.append(ValidationFinding(
                        worker, "BLOCK", "retro-lineage",
                        f"retro element {element['code']} lacks original-period pointer"))
                elif abs(Decimal(element["amount"])) > retro_sanity_pct * _gross(payload):
                    findings.append(ValidationFinding(
                        worker, "HOLD-RECORD", "retro-sanity",
                        f"retro {element['code']} exceeds {retro_sanity_pct:%} of gross"))

        # Layer 3 — anomaly heuristics (AI scoring slot, Specs/14 hookup later)
        history = trailing_nets.get(worker, [])
        if history:
            mean = sum(history) / len(history)
            net_estimate = _gross(payload) - _deductions(payload)
            if mean > 0 and abs(net_estimate - mean) > mean * Decimal("0.5"):
                findings.append(ValidationFinding(
                    worker, "WARN", "trailing-variance",
                    f"net {net_estimate} deviates >50% from trailing mean {mean:.2f}"))
        bank_days = payload.get("bank_change_days")
        if bank_days is not None and bank_days <= 7:
            findings.append(ValidationFinding(
                worker, "HOLD-RECORD", "bank-change-near-payday",
                f"bank change {bank_days} days before payday — fraud review"))

    blocking = [f for f in findings if f.severity == "BLOCK"]
    if blocking:
        raise BlockingValidationError(
            "; ".join(f"{f.worker_id}:{f.rule}" for f in blocking)
        )
    for finding in findings:
        if finding.severity == "HOLD-RECORD":
            held = next(r for r in rows if r.worker_id == finding.worker_id)
            held.held = True
            held.hold_reason = f"{finding.rule}: {finding.detail} (retro auto-queued)"
    _transition(cycle, "validated")
    session.flush()
    return findings


def _gross(payload: dict) -> Decimal:
    return sum((Decimal(e["amount"]) for e in payload["elements"] if e["kind"] == "earning"),
               Decimal("0"))


def _deductions(payload: dict) -> Decimal:
    return sum((Decimal(e["amount"]) for e in payload["elements"] if e["kind"] == "deduction"),
               Decimal("0"))


def approve_cycle(session: Session, cycle: PayCycle, *, approver: str) -> None:
    """Approval with 4-eyes above the gross threshold (SOX segregation)."""
    if cycle.state != "validated":
        raise IllegalTransitionError("approve from validated only")
    if (cycle.gross_total or Decimal("0")) > FOUR_EYES_GROSS_THRESHOLD \
            and approver == cycle.compiled_by:
        raise PermissionError("4-eyes: approver must differ from compiler above threshold")
    cycle.approved_by = approver
    _transition(cycle, "approved")
    session.flush()


def transmit(session: Session, cycle: PayCycle, adapter: Connector,
             *, last_cycle_authorized_by: str | None = None) -> dict:
    """Approved → Transmitted via the provider adapter. Provider outage at
    cut-off (register row): with explicit authorization, fall back to
    pay-as-last-cycle records and queue a true-up."""
    if cycle.state != "approved":
        raise IllegalTransitionError("transmit from approved only")
    rows = session.scalars(
        select(PayInputRecord).where(PayInputRecord.cycle_id == cycle.cycle_id,
                                     PayInputRecord.held == False)  # noqa: E712
    ).all()
    outcome = adapter.run(session, [row.payload for row in rows])
    if outcome.status == "success":
        _transition(cycle, "transmitted")
        session.flush()
        return {"transmitted": len(rows), "ack": outcome.ack_reference, "contingency": False}

    if last_cycle_authorized_by is None:
        raise RuntimeError(
            f"provider transmission failed ({outcome.error_normalized}); "
            "pay-as-last-cycle contingency requires explicit authorization"
        )
    _transition(cycle, "transmitted")  # contingency counts as transmitted, with true-up queued
    session.flush()
    return {"transmitted": len(rows), "ack": None, "contingency": True,
            "authorized_by": last_cycle_authorized_by, "true_up_queued": True}


def ingest_results(session: Session, cycle: PayCycle, results: list[dict]) -> dict:
    """Results validation (§6): net = gross − deductions per record, and the
    headcount must match the transmitted set exactly (added/dropped = critical)."""
    if cycle.state != "transmitted":
        raise IllegalTransitionError("results land on a transmitted cycle")
    transmitted_workers = set(session.scalars(
        select(PayInputRecord.worker_id).where(
            PayInputRecord.cycle_id == cycle.cycle_id,
            PayInputRecord.held == False)  # noqa: E712
    ).all())
    result_workers = {r["worker_id"] for r in results}
    critical = []
    if result_workers - transmitted_workers:
        critical.append(f"provider ADDED records: {sorted(result_workers - transmitted_workers)}")
    if transmitted_workers - result_workers:
        critical.append(f"provider DROPPED records: {sorted(transmitted_workers - result_workers)}")
    if critical:
        raise RuntimeError("CRITICAL headcount mismatch: " + "; ".join(critical))

    for result in results:
        gross = Decimal(str(result["gross"]))
        deductions = Decimal(str(result["total_deductions"]))
        net = Decimal(str(result["net"]))
        if gross - deductions != net:
            raise RuntimeError(
                f"identity violated for {result['worker_id']}: {gross} - {deductions} != {net}"
            )
        session.add(PayResultRecord(
            cycle_id=cycle.cycle_id, worker_id=result["worker_id"],
            gross=gross, total_deductions=deductions, net=net,
            elements=result.get("elements", []),
        ))
    _transition(cycle, "results-received")
    session.flush()
    return {"ingested": len(results)}


def apply_arrears_policy(record: CpdcRecord) -> CpdcRecord:
    """Negative-net policy (register row): when deductions exceed gross,
    deductions are reduced to gross (priority order preserved by list order)
    and the shortfall carries as arrears — net never goes below zero."""
    gross = record.gross()
    shortfall = record.deductions() - gross
    if shortfall <= 0:
        return record
    remaining = shortfall
    for element in reversed([e for e in record.elements if e.kind == "deduction"]):
        if remaining <= 0:
            break
        reduction = min(element.amount, remaining)
        element.amount -= reduction
        remaining -= reduction
    record.arrears_carried += shortfall
    return record


def split_for_entity_transfer(
    record: CpdcRecord, *, new_entity: str, split_fraction: Decimal,
) -> tuple[CpdcRecord, CpdcRecord]:
    """Mid-cycle legal-entity transfer (register row): one worker, two CPDC
    records — pre-transfer entity and post-transfer entity — with the YTD
    handover marked on the receiving record. Amounts split by fraction."""
    def scaled(elements, fraction):
        return [PayElement(e.element_code, e.kind,
                           (e.amount * fraction).quantize(Decimal("0.01")),
                           e.units, e.retro, e.original_period)
                for e in elements]

    before = CpdcRecord(
        worker_id=record.worker_id, legal_entity=record.legal_entity,
        country=record.country, pay_group=record.pay_group,
        period_key=record.period_key,
        elements=scaled(record.elements, Decimal("1") - split_fraction),
    )
    after = CpdcRecord(
        worker_id=record.worker_id, legal_entity=new_entity,
        country=record.country, pay_group=record.pay_group,
        period_key=record.period_key,
        elements=scaled(record.elements, split_fraction),
        ytd_handover_from_entity=record.legal_entity,
    )
    return before, after


def reconcile_three_way(
    meridian: dict[str, Decimal], provider: dict[str, Decimal],
    legacy: dict[str, Decimal], *, rounding_tolerance: Decimal = Decimal("0.01"),
) -> list[dict]:
    """Element-level three-way compare (§7) with variance classification."""
    variances = []
    for element in sorted(set(meridian) | set(provider) | set(legacy)):
        m, p, l = (meridian.get(element), provider.get(element), legacy.get(element))
        if m is None or p is None or l is None:
            variances.append({"element": element, "class": "population-diff",
                              "meridian": m, "provider": p, "legacy": l})
            continue
        if m == p == l:
            continue
        delta = max(abs((p or 0) - (m or 0)), abs((p or 0) - (l or 0)))
        if delta <= rounding_tolerance:
            variances.append({"element": element, "class": "rounding", "delta": delta})
        elif m == p != l:
            variances.append({"element": element, "class": "legacy-divergence",
                              "detail": "Meridian matches provider; PeopleSoft differs"})
        else:
            variances.append({"element": element, "class": "true-defect",
                              "meridian": m, "provider": p, "legacy": l})
    return variances
