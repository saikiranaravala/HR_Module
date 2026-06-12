"""Migration-program tests (Specs/16): extraction adapter, factory pipeline,
reconciliation workbench, bidirectional sync, cutover — with the §7 program
risks as the register."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from migration import cutover, extraction, pipeline, recon, sync

SPECS = pipeline.load_mapping_specs()
NOW = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)

PS_JOB_ROWS = [
    {"EMPLID": "1001", "EFFDT": date(2015, 3, 1), "EFFSEQ": 0, "ACTION": "HIR",
     "JOBCODE": "ENG1", "DEPTID": "D100", "FTE": 1.0},
    {"EMPLID": "1001", "EFFDT": date(2018, 7, 1), "EFFSEQ": 0, "ACTION": "PRO",
     "JOBCODE": "ENG2", "DEPTID": "D100", "FTE": 1.0},
    {"EMPLID": "1001", "EFFDT": date(2018, 7, 1), "EFFSEQ": 1, "ACTION": "PAY",
     "JOBCODE": "ENG2", "DEPTID": "D100", "FTE": 1.0},
    {"EMPLID": "1001", "EFFDT": date(2020, 1, 15), "EFFSEQ": 0, "ACTION": "TER",
     "JOBCODE": "ENG2", "DEPTID": "D100", "FTE": 1.0},
    {"EMPLID": "1001", "EFFDT": date(2020, 9, 1), "EFFSEQ": 0, "ACTION": "REH",
     "JOBCODE": "ENG2", "DEPTID": "D200", "FTE": 1.0},
]


# --- Extraction adapter (MIG-1) ----------------------------------------------------

def test_MIG_full_effdt_history_preserved():
    """Risk register: history must survive row-for-row — full EFFDT/EFFSEQ
    chain incl. same-day sequences, never current-state-only."""
    canonical = extraction.transform_ps_job_history(PS_JOB_ROWS)
    assert len(canonical) == 5  # every history row kept
    same_day = [r for r in canonical if r["effective_date"] == date(2018, 7, 1)]
    assert [r["effective_sequence"] for r in same_day] == [0, 1]
    assert {r["action_code"] for r in canonical} == {
        "hire", "promotion", "comp-change", "termination", "rehire"}


def test_unmapped_ps_action_halts_loudly():
    rows = [{"EMPLID": "9", "EFFDT": date(2020, 1, 1), "EFFSEQ": 0, "ACTION": "XYZ"}]
    with pytest.raises(extraction.UnmappedActionError, match="semantic review"):
        extraction.transform_ps_job_history(rows)


def test_rehire_bridging_recompute_diff():
    canonical = extraction.transform_ps_job_history(PS_JOB_ROWS)
    diffs = extraction.recompute_rehire_bridging(canonical)
    assert diffs == [{"worker_ref": "1001",
                      "computed_service_date": date(2015, 3, 1),  # bridged (gap 230d)
                      "gap_days": 230, "bridged": True}]


def test_MIG_orphan_feed_discovery():
    """Risk register: feeds nobody documented are found by traffic diff."""
    orphans = extraction.discover_orphan_feeds(
        documented_feeds={"adp-payfile", "carrier-834"},
        observed_connections=[
            {"feed": "adp-payfile", "host": "ps-batch-01"},
            {"feed": "facilities-badge-extract", "host": "ps-batch-02"},
        ],
    )
    assert len(orphans) == 1
    assert orphans[0]["feed"] == "facilities-badge-extract"
    assert orphans[0]["flag"] == "orphan-feed"


# --- Factory pipeline (MIG-2) ---------------------------------------------------------

def test_idempotent_staging(session):
    rows = [{"source_key": "1001", "worker_ref": "1001", "country": "US"},
            {"source_key": "1002", "worker_ref": "1002", "country": "US"}]
    first = pipeline.stage_batch(session, batch_id="b-1", domain="person", rows=rows)
    rerun = pipeline.stage_batch(session, batch_id="b-1", domain="person", rows=rows)
    assert first == {"staged": 2, "skipped_duplicates": 0}
    assert rerun == {"staged": 0, "skipped_duplicates": 2}  # weekly re-runs safe


def test_dq_scorecard_and_threshold_gate(session):
    rows = [
        {"source_key": "1", "worker_ref": "w1", "effective_date": "2026-01-01",
         "action_code": "hire", "job_code": "ENG1"},
        {"source_key": "2", "worker_ref": "w2", "effective_date": "2026-01-01",
         "action_code": "promotion", "job_code": None},          # completeness fail
        {"source_key": "3", "worker_ref": "w3", "effective_date": "2026-01-01",
         "action_code": "PS-XFR", "job_code": "ENG2"},           # validity fail
        {"source_key": "4", "worker_ref": "ghost", "effective_date": "2026-01-01",
         "action_code": "hire", "job_code": "ENG1"},             # referential fail
    ]
    pipeline.stage_batch(session, batch_id="b-2", domain="job-history", rows=rows)
    scorecard = pipeline.dq_scorecard(session, batch_id="b-2", domain="job-history",
                                      spec=SPECS["job-history"],
                                      known_refs={"w1", "w2", "w3"})
    assert scorecard["scores"]["completeness"] == 0.75
    assert scorecard["scores"]["validity"] == 0.75
    assert scorecard["scores"]["referential"] == 0.75
    assert scorecard["exceptions"] == 3

    ok, blockers = pipeline.threshold_gate(scorecard, thresholds={"completeness": 0.99})
    assert not ok and "completeness" in blockers[0]
    # steward guidance points at the SOURCE
    from migration.models import DqException
    from sqlalchemy import select
    guidance = session.scalars(select(DqException)).all()[0].guidance
    assert "PeopleSoft" in guidance


# --- Reconciliation workbench (MIG-3) ----------------------------------------------------

def test_MIG_field_match_gate_9995():
    """Risk register: the 99.95% critical-field gate, computed not asserted."""
    ps = {str(i): {"job_code": "ENG1", "fte": 1.0} for i in range(10000)}
    meridian = {k: dict(v) for k, v in ps.items()}
    result = recon.field_match(ps, meridian, critical_fields=["job_code", "fte"])
    assert result["gate_passed"] and result["overall_critical_rate"] == 1

    meridian["42"]["job_code"] = "ENG9"        # 1/10000 = 99.99% → still passes
    result = recon.field_match(ps, meridian, critical_fields=["job_code", "fte"])
    assert result["gate_passed"]

    for key in ("43", "44", "45", "46", "47"):  # 6/10000 = 99.94% → fails
        meridian[key]["job_code"] = "ENG9"
    result = recon.field_match(ps, meridian, critical_fields=["job_code", "fte"])
    assert not result["gate_passed"]
    assert len(result["mismatches"]) == 6


def test_MIG_recompute_triage_rule_vs_data():
    """Risk register: history corrupting downstream calc — recompute-and-compare
    distinguishes rule differences from data differences."""
    rule_diff = recon.recompute_triage(
        ps_balance=Decimal("120.0"), meridian_balance=Decimal("118.5"),
        meridian_rule_version="accrual-v2", ps_rule_version="accrual-v1")
    assert rule_diff["kind"] == "rule-difference"
    assert rule_diff["needs"] == "rules adjudication"

    data_diff = recon.recompute_triage(
        ps_balance=Decimal("120.0"), meridian_balance=Decimal("100.0"),
        meridian_rule_version="accrual-v1", ps_rule_version="accrual-v1")
    assert data_diff["kind"] == "data-difference"
    assert data_diff["needs"] == "source data correction"


def test_MIG_variance_taxonomy_env_difference():
    """Risk register: provider test-env fidelity gaps never masquerade as
    payroll errors — they classify as env-difference."""
    env = recon.classify_pay_variance(ps_net=Decimal("2500.00"),
                                      provider_net=Decimal("2498.00"),
                                      provider_env="provider-test")
    assert env["kind"] == "env-difference"
    real = recon.classify_pay_variance(ps_net=Decimal("2500.00"),
                                       provider_net=Decimal("2498.00"),
                                       provider_env="production-parallel")
    assert real["kind"] == "data-difference"
    rounding = recon.classify_pay_variance(ps_net=Decimal("2500.00"),
                                           provider_net=Decimal("2500.01"),
                                           provider_env="production-parallel")
    assert rounding["kind"] == "rounding"


def test_MIG_gate_artifact_immutable(session):
    artifact = recon.sign_gate_artifact(
        session, wave="wave-1-NL", gate="entry", passed=True,
        report={"field_match": "0.9997", "cycles": 3}, signed_by="program-director")
    assert artifact.content_hash
    with pytest.raises(ProgrammingError, match="immutable"):
        with session.begin_nested():
            session.execute(text(
                "UPDATE migration.gate_artifact SET passed = false "
                "WHERE artifact_id = :aid"), {"aid": artifact.artifact_id})


# --- Bidirectional sync (MIG-4, highest risk) -----------------------------------------------

def test_MIG_sync_conflict_queue_and_kill_switch(session):
    """Risk register: concurrent edits → ownership decides + conflict queued
    (4h SLA); kill-switch reverts to one-way and parks open conflicts."""
    engine = sync.SyncEngine(phase="pilot-dual-entry")
    assert engine.owner_of("address") == "meridian"
    assert engine.owner_of("base_salary") == "ps"
    assert engine.owner_of("unlisted-field") == "ps"  # default owner

    outcome = engine.apply_change(session, worker_ref="1001", field="address",
                                  ps_value="old st", meridian_value="new st", now=NOW)
    assert outcome["applied"] == "new st" and outcome["winner"] == "meridian"
    assert outcome["conflict_id"] is not None
    assert sync.overdue_conflicts(session, now=NOW + timedelta(hours=5))

    killed = engine.kill_switch(session, reason="sev-1 sync incident")
    assert killed == {"mode": "one-way", "parked_conflicts": 1}
    with pytest.raises(sync.SyncKilledError):
        engine.apply_change(session, worker_ref="1001", field="address",
                            ps_value="a", meridian_value="b", now=NOW)


def test_MIG_sync_lag_alert(session):
    engine = sync.SyncEngine(phase="pilot-dual-entry")
    assert engine.lag_alert(now=NOW)  # never synced yet
    engine.apply_change(session, worker_ref="1001", field="address",
                        ps_value="x", meridian_value=None, now=NOW)
    assert not engine.lag_alert(now=NOW + timedelta(minutes=10))
    assert engine.lag_alert(now=NOW + timedelta(minutes=16))


def test_shadow_phase_is_one_way(session):
    engine = sync.SyncEngine(phase="shadow")
    assert engine.mode == "one-way"
    with pytest.raises(sync.SyncKilledError):
        engine.apply_change(session, worker_ref="1001", field="address",
                            ps_value="a", meridian_value="b", now=NOW)


# --- Cutover (MIG-5) -----------------------------------------------------------------------

def test_go_no_go_requires_evidence_and_signature():
    items = [
        {"item": "data gate ≥99.95%", "evidence_ref": "gate_artifact:1",
         "signed_by_role": "data-steward", "passed": True},
        {"item": "training completion", "evidence_ref": None,
         "signed_by_role": "hr-lead", "passed": True},
    ]
    outcome = cutover.evaluate_go_no_go(items)
    assert not outcome["go"]
    assert outcome["blockers"] == ["'training completion' has no linked evidence"]


def test_MIG_rollback_decision_window():
    """Risk register: rollback inside 72h, retained until 2 clean cycles,
    closed after."""
    cutover_at = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    inside = cutover.rollback_decision(
        cutover_at=cutover_at, requested_at=cutover_at + timedelta(hours=48),
        clean_cycles_since_cutover=0)
    assert inside["allowed"] and inside["path"] == "decision-window"

    retained = cutover.rollback_decision(
        cutover_at=cutover_at, requested_at=cutover_at + timedelta(days=20),
        clean_cycles_since_cutover=1)
    assert retained["allowed"] and retained["path"] == "retained-capability"

    with pytest.raises(cutover.RollbackWindowClosedError, match="forward-fix"):
        cutover.rollback_decision(
            cutover_at=cutover_at, requested_at=cutover_at + timedelta(days=60),
            clean_cycles_since_cutover=2)
