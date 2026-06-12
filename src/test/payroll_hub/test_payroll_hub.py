"""Payroll Hub tests (Specs/03): state machine, PAY-3 gate, snapshot
immutability, adapter transmission, results identity, reconciliation,
and the §10 edge-case register."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from integration_hub.chassis import Connector, TransportResult
from payroll_hub import cycle as pc
from payroll_hub.cpdc import CpdcRecord, PayElement, StateAllocation


class MockProviderAdapter(Connector):
    """CPDC → provider format mapping lives HERE and only here (Invariant #4)."""
    key = "mock-provider-us"
    MAPPING = {"REG": "E001", "OT15": "E002", "401K": "D401", "HEALTH": "D200"}

    def __init__(self, down=False):
        self.down = down
        self.sent_lines: list[str] = []

    def transform(self, records):
        lines = []
        for record in records:
            for element in record["elements"]:
                provider_code = self.MAPPING.get(element["code"], "E999")
                lines.append(f"{record['worker_id']}|{provider_code}|{element['amount']}")
        return lines

    def transport(self, payload):
        if self.down:
            return TransportResult(accepted=False, error="provider endpoint unreachable")
        self.sent_lines = payload
        return TransportResult(accepted=True, ack_reference="PRV-ACK-77")


def _new_cycle(session, country="US"):
    cyc = pc.PayCycle(country=country, pay_group="us-biweekly", period_key="2026-P12")
    session.add(cyc)
    session.flush()
    return cyc


def _run_to_approved(session, cyc, records, actor="compiler", approver="approver"):
    pc.compile_inputs(session, cyc, records, actor=actor)
    pc.validate_cycle(session, cyc)
    pc.approve_cycle(session, cyc, approver=approver)


# ---------- State machine & snapshot ----------

def test_state_machine_enforces_order(session, record_factory):
    cyc = _new_cycle(session)
    with pytest.raises(pc.IllegalTransitionError):
        pc.approve_cycle(session, cyc, approver="x")  # cannot skip states
    pc.compile_inputs(session, cyc, [record_factory()], actor="ops-1")
    with pytest.raises(pc.IllegalTransitionError):
        pc.compile_inputs(session, cyc, [record_factory()], actor="ops-1")  # no recompile


def test_PAY_snapshot_immutable_after_compile(session, record_factory):
    """CLAUDE.md payroll-path requirement: the compiled snapshot is immutable —
    any tampering with input rows is detected by hash verification."""
    cyc = _new_cycle(session)
    pc.compile_inputs(session, cyc, [record_factory(), record_factory(worker="w-2")],
                      actor="ops-1")
    session.commit()
    pc.verify_snapshot(session, cyc)  # intact

    session.execute(text(
        "UPDATE payroll.pay_input_record SET payload = jsonb_set(payload, '{elements,0,amount}', '\"9999\"') "
        "WHERE worker_id = 'w-1'"
    ))
    session.commit()
    with pytest.raises(pc.SnapshotTamperedError):
        pc.verify_snapshot(session, cyc)


def test_four_eyes_above_threshold(session, record_factory):
    cyc = _new_cycle(session)
    big = record_factory(gross=Decimal("2000000"))
    pc.compile_inputs(session, cyc, [big], actor="ops-1")
    pc.validate_cycle(session, cyc)
    with pytest.raises(PermissionError, match="4-eyes"):
        pc.approve_cycle(session, cyc, approver="ops-1")  # same person
    pc.approve_cycle(session, cyc, approver="ops-2")
    assert cyc.state == "approved"


# ---------- PAY-3 validation gate ----------

def test_blocking_error_stops_transmission(session, record_factory):
    """'Nothing transmits with blocking errors' — inactive element for country."""
    cyc = _new_cycle(session, country="DE")
    bad = CpdcRecord(worker_id="w-de", legal_entity="meridian-de", country="DE",
                     pay_group="de-monthly", period_key="2026-P12",
                     elements=[PayElement("REG", "earning", Decimal("4000")),
                               PayElement("401K", "deduction", Decimal("100"))])  # US-only element
    pc.compile_inputs(session, cyc, [bad], actor="ops-1")
    with pytest.raises(pc.BlockingValidationError, match="element-not-active"):
        pc.validate_cycle(session, cyc)
    assert cyc.state == "inputs-compiled"  # gate held the cycle


def test_hold_record_excludes_but_cycle_proceeds(session, record_factory):
    """HOLD-RECORD: suspicious record excluded, the rest transmits."""
    cyc = _new_cycle(session)
    suspicious = record_factory(worker="w-risky",
                                bank_last_changed_days_before_payday=2)
    clean = record_factory(worker="w-clean")
    pc.compile_inputs(session, cyc, [suspicious, clean], actor="ops-1")
    findings = pc.validate_cycle(session, cyc)
    pc.approve_cycle(session, cyc, approver="ops-2")

    adapter = MockProviderAdapter()
    outcome = pc.transmit(session, cyc, adapter)
    session.commit()

    assert any(f.rule == "bank-change-near-payday" for f in findings)
    assert outcome["transmitted"] == 1  # held record excluded
    held = session.scalars(select(pc.PayInputRecord).where(
        pc.PayInputRecord.held == True)).one()  # noqa: E712
    assert held.worker_id == "w-risky" and "retro auto-queued" in held.hold_reason


def test_warn_transmits_and_is_tracked(session, record_factory):
    cyc = _new_cycle(session)
    pc.compile_inputs(session, cyc, [record_factory(gross=Decimal("20000"))], actor="ops-1")
    findings = pc.validate_cycle(
        session, cyc,
        trailing_nets={"w-1": [Decimal("4000"), Decimal("4100"), Decimal("3900")]},
    )
    assert any(f.severity == "WARN" and f.rule == "trailing-variance" for f in findings)
    assert cyc.state == "validated"  # WARN never blocks


# ---------- Register rows ----------

def test_PAY_multi_state_allocation_must_sum_100(session, record_factory):
    cyc = _new_cycle(session)
    split = record_factory(state_allocations=[
        StateAllocation("CA", Decimal("60")), StateAllocation("NY", Decimal("30")),
    ])  # 90 ≠ 100
    pc.compile_inputs(session, cyc, [split], actor="ops-1")
    with pytest.raises(pc.BlockingValidationError, match="multi-state"):
        pc.validate_cycle(session, cyc)


def test_PAY_deceased_worker_beneficiary_payee(session, record_factory):
    cyc = _new_cycle(session)
    deceased = record_factory(deceased=True)  # no payee override
    pc.compile_inputs(session, cyc, [deceased], actor="ops-1")
    with pytest.raises(pc.BlockingValidationError, match="deceased-payee"):
        pc.validate_cycle(session, cyc)

    cyc_ok = _new_cycle(session)
    handled = record_factory(worker="w-9", deceased=True, payee_override="estate-of-w-9")
    pc.compile_inputs(session, cyc_ok, [handled], actor="ops-1")
    pc.validate_cycle(session, cyc_ok)
    assert cyc_ok.state == "validated"


def test_PAY_negative_net_arrears_policy(record_factory):
    """Register row: deduction stack > gross — deductions reduced, shortfall
    carried as arrears, net never below zero."""
    record = record_factory(gross=Decimal("500"), deductions=Decimal("400"))
    record.elements.append(PayElement("GARN", "deduction", Decimal("300")))  # total 700 > 500

    adjusted = pc.apply_arrears_policy(record)

    assert adjusted.gross() - adjusted.deductions() == Decimal("0")  # net floor at 0
    assert adjusted.arrears_carried == Decimal("200")
    garn = next(e for e in adjusted.elements if e.element_code == "GARN")
    assert garn.amount == Decimal("100")  # last-priority deduction reduced first


def test_PAY_mid_cycle_entity_transfer_split(record_factory):
    """Register row: mid-cycle legal-entity transfer → two records, amounts
    split, YTD handover marked on the receiving entity's record."""
    record = record_factory(gross=Decimal("5000"), deductions=Decimal("750"))
    before, after = pc.split_for_entity_transfer(
        record, new_entity="meridian-us-west", split_fraction=Decimal("0.4"),
    )
    assert before.legal_entity == "meridian-us" and after.legal_entity == "meridian-us-west"
    assert before.gross() + after.gross() == Decimal("5000.00")
    assert after.ytd_handover_from_entity == "meridian-us"


def test_PAY_provider_outage_pay_as_last_cycle(session, record_factory):
    """Register row: provider outage at cut-off — transmission fails loudly;
    the pay-as-last-cycle contingency needs explicit authorization and queues
    a true-up. The pipeline never degrades silently."""
    cyc = _new_cycle(session)
    _run_to_approved(session, cyc, [record_factory()])

    with pytest.raises(RuntimeError, match="explicit authorization"):
        pc.transmit(session, cyc, MockProviderAdapter(down=True))

    outcome = pc.transmit(session, cyc, MockProviderAdapter(down=True),
                          last_cycle_authorized_by="payroll-director")
    session.commit()
    assert outcome["contingency"] and outcome["true_up_queued"]
    assert cyc.state == "transmitted"


# ---------- Results & reconciliation ----------

def test_PAY_results_identity_net_gross(session, record_factory):
    cyc = _new_cycle(session)
    _run_to_approved(session, cyc, [record_factory()])
    pc.transmit(session, cyc, MockProviderAdapter())

    with pytest.raises(RuntimeError, match="identity violated"):
        pc.ingest_results(session, cyc, [
            {"worker_id": "w-1", "gross": "5000", "total_deductions": "750", "net": "4000"},
        ])

    pc.ingest_results(session, cyc, [
        {"worker_id": "w-1", "gross": "5000", "total_deductions": "750", "net": "4250"},
    ])
    session.commit()
    assert cyc.state == "results-received"


def test_headcount_mismatch_is_critical(session, record_factory):
    cyc = _new_cycle(session)
    _run_to_approved(session, cyc, [record_factory()])
    pc.transmit(session, cyc, MockProviderAdapter())
    with pytest.raises(RuntimeError, match="ADDED"):
        pc.ingest_results(session, cyc, [
            {"worker_id": "w-1", "gross": "5000", "total_deductions": "750", "net": "4250"},
            {"worker_id": "w-ghost", "gross": "100", "total_deductions": "0", "net": "100"},
        ])


def test_adapter_maps_canonical_to_provider_codes(session, record_factory):
    """Invariant #4 demonstrated: canonical REG becomes provider E001 inside
    the adapter; no provider code exists upstream."""
    cyc = _new_cycle(session)
    _run_to_approved(session, cyc, [record_factory()])
    adapter = MockProviderAdapter()
    pc.transmit(session, cyc, adapter)
    assert any("|E001|" in line for line in adapter.sent_lines)
    assert not any("REG" in line for line in adapter.sent_lines)


def test_three_way_reconciliation_classification():
    meridian = {"REG": Decimal("5000"), "OT15": Decimal("450"), "401K": Decimal("-750")}
    provider = {"REG": Decimal("5000"), "OT15": Decimal("450.01"), "401K": Decimal("-750")}
    legacy = {"REG": Decimal("5000"), "OT15": Decimal("450"), "401K": Decimal("-700"),
              "OLDX": Decimal("12")}

    variances = pc.reconcile_three_way(meridian, provider, legacy)
    by_class = {v["element"]: v["class"] for v in variances}
    assert by_class["OT15"] == "rounding"
    assert by_class["401K"] == "legacy-divergence"
    assert by_class["OLDX"] == "population-diff"
    assert "REG" not in by_class  # penny-perfect element produces no variance
