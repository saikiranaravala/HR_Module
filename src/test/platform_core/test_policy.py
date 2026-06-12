"""Policy service tests (TECH-5): RBAC+ABAC decisions, tier filtering,
cross-surface consistency, fail-closed behavior, and T2/T3 read logging."""
import uuid
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from platform_core import temporal
from platform_core.api import app
from platform_core.audit import AuditEvent
from platform_core.catalog import Tier
from platform_core.policy.engine import (
    Decision,
    PolicyEngine,
    Resource,
    Subject,
    read_with_audit,
    serialize_filtered,
)
from sample_entity import WorkerProfile

ENGINE = PolicyEngine()


def test_hr_admin_reads_comp_anywhere():
    decision = ENGINE.decide(
        Subject("u-hr-1", ("hr-admin",)), "comp.read", Resource(country="DE")
    )
    assert decision.allow
    assert decision.clearance == Tier.T2
    assert decision.policy_version == "2026-06-11.1"


def test_country_scope_denies_out_of_scope():
    decision = ENGINE.decide(
        Subject("u-hr-us", ("hr-admin-us",)), "person.read", Resource(country="DE")
    )
    assert not decision.allow


def test_self_capability_requires_ownership():
    own = ENGINE.decide(
        Subject("w-100", ("employee",)), "person.read", Resource(owner_id="w-100")
    )
    other = ENGINE.decide(
        Subject("w-100", ("employee",)), "person.read", Resource(owner_id="w-200")
    )
    assert own.allow and own.clearance == Tier.T1
    assert not other.allow


def test_serialize_strips_fields_above_clearance():
    data = {
        "display_name": "Synthetic Worker",
        "email": "synthetic.worker@example.invalid",
        "base_salary": 50000,
    }
    t1 = serialize_filtered(WorkerProfile, data, Decision(allow=True, clearance=Tier.T1))
    t2 = serialize_filtered(WorkerProfile, data, Decision(allow=True, clearance=Tier.T2))
    deny = serialize_filtered(WorkerProfile, data, Decision(allow=False))

    assert "base_salary" not in t1 and "display_name" in t1
    assert "base_salary" in t2
    assert deny == {}


def test_cross_surface_consistency_api_matches_in_process():
    """The HTTP surface and the in-process call must reach identical decisions
    (the 'can never see via report what UI denies' guarantee, locally)."""
    cases = [
        ("hr-admin", "comp.read", {"resource_country": "JP"}, Resource(country="JP")),
        ("hr-admin-us", "person.read", {"resource_country": "DE"}, Resource(country="DE")),
        ("employee", "person.read", {"resource_owner_id": "someone-else"}, Resource(owner_id="someone-else")),
        ("auditor", "audit.verify", {}, Resource()),
    ]
    client = TestClient(app)
    for role, capability, api_resource, resource in cases:
        in_process = ENGINE.decide(Subject("subject-x", (role,)), capability, resource)
        response = client.post(
            "/v1/policy/decide",
            json={"subject_id": "subject-x", "roles": [role], "capability": capability, **api_resource},
        )
        assert response.status_code == 200
        assert response.json()["allow"] == in_process.allow, (role, capability)


def test_TECH_policy_unavailable_fails_closed(tmp_path: Path):
    """Specs/15 §9 analogue: when the policy engine breaks, everything denies —
    access never silently degrades to allow."""
    missing = PolicyEngine(policy_path=tmp_path / "does-not-exist.yaml")
    decision = missing.decide(Subject("u", ("hr-admin",)), "person.read", Resource())
    assert not decision.allow
    assert any("fail closed" in reason for reason in decision.reasons)

    corrupt_file = tmp_path / "corrupt.yaml"
    corrupt_file.write_text("just-a-string", encoding="utf-8")
    corrupt = PolicyEngine(policy_path=corrupt_file)
    decision = corrupt.decide(Subject("u", ("hr-admin",)), "person.read", Resource())
    assert not decision.allow


def test_t2_read_is_audit_logged(session, make_row):
    worker_id = uuid.uuid4()
    temporal.insert_temporal(
        session, make_row(worker_id, date(2026, 1, 1)),
        actor="setup", source_channel="test", correlation_id=uuid.uuid4(),
    )
    session.commit()

    decision = ENGINE.decide(
        Subject("u-hr-1", ("hr-admin",)), "comp.read", Resource(country="US")
    )
    row = temporal.as_of(session, WorkerProfile, worker_id, date(2026, 1, 1))
    payload = read_with_audit(
        session, WorkerProfile, temporal.snapshot(row), decision,
        subject=Subject("u-hr-1", ("hr-admin",)),
        entity_ref=f"worker_profile:{worker_id}",
        source_channel="test",
        correlation_id=uuid.uuid4(),
    )
    session.commit()

    assert "base_salary" in payload  # T2 clearance sees T2 field
    read_events = session.scalars(
        select(AuditEvent).where(AuditEvent.action == "read")
    ).all()
    assert len(read_events) == 1
    assert read_events[0].sensitivity_tier == "T2"


def test_t1_read_not_logged_when_t2_fields_redacted(session, make_row):
    worker_id = uuid.uuid4()
    temporal.insert_temporal(
        session, make_row(worker_id, date(2026, 1, 1)),
        actor="setup", source_channel="test", correlation_id=uuid.uuid4(),
    )
    session.commit()

    decision = ENGINE.decide(
        Subject(str(worker_id), ("employee",)), "person.read",
        Resource(owner_id=str(worker_id)),
    )
    row = temporal.as_of(session, WorkerProfile, worker_id, date(2026, 1, 1))
    payload = read_with_audit(
        session, WorkerProfile, temporal.snapshot(row), decision,
        subject=Subject(str(worker_id), ("employee",)),
        entity_ref=f"worker_profile:{worker_id}",
        source_channel="test",
        correlation_id=uuid.uuid4(),
    )
    session.commit()

    assert "base_salary" not in payload  # redacted at T1
    read_events = session.scalars(select(AuditEvent).where(AuditEvent.action == "read")).all()
    assert read_events == []  # nothing sensitive returned ⇒ no read log
