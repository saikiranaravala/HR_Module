"""Integration hub tests (Specs/13): chassis runs/heartbeat, credential expiry,
JML idempotency + outage queueing, consumer contract pinning."""
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from integration_hub.chassis import (
    Connector,
    ConnectorCredential,
    TransportResult,
    expiring_credentials,
    last_success,
)
from integration_hub.consumers import (
    ConsumerContract,
    ConsumerRegistry,
    ContractVersionError,
    serve_payload,
)
from integration_hub.jml import prestage_due, process_action, replay_queued
from platform_core.catalog import Tier
from sample_entity_int import IntWorkerRow

NOW = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)


class OkConnector(Connector):
    key = "test-ok"

    def transform(self, records):
        return {"lines": [f"{r['id']}|{r['value']}" for r in records]}  # vendor format stays here

    def transport(self, payload):
        return TransportResult(accepted=True, ack_reference="ACK-1")


class RejectingConnector(OkConnector):
    key = "test-reject"

    def transport(self, payload):
        return TransportResult(accepted=False, error="provider closed the window")


class ExplodingConnector(OkConnector):
    key = "test-explode"

    def transform(self, records):
        raise RuntimeError("bad mapping")


def test_connector_run_success_and_heartbeat(session):
    outcome = OkConnector().run(session, [{"id": 1, "value": "a"}])
    session.commit()
    assert outcome.status == "success" and outcome.ack_reference == "ACK-1"
    assert last_success(session, "test-ok") is not None


def test_connector_failures_are_loud_and_normalized(session):
    rejected = RejectingConnector().run(session, [{"id": 1, "value": "a"}])
    exploded = ExplodingConnector().run(session, [{"id": 1, "value": "a"}])
    session.commit()
    assert rejected.status == "failed" and "test-reject" in rejected.error_normalized
    assert exploded.status == "failed" and "bad mapping" in exploded.error_normalized
    assert last_success(session, "test-reject") is None  # no false heartbeat


def test_INT_credential_expiry_alerting(session):
    session.add_all([
        ConnectorCredential(connector_key="carrier-x", credential_kind="cert",
                            reference="vault://carrier-x/cert", expires_on=date(2026, 6, 20)),
        ConnectorCredential(connector_key="provider-y", credential_kind="pgp-key",
                            reference="vault://provider-y/pgp", expires_on=date(2027, 6, 20)),
    ])
    session.commit()
    expiring = expiring_credentials(session, today=date(2026, 6, 10), within_days=30)
    assert [c.connector_key for c in expiring] == ["carrier-x"]


def test_INT_duplicate_delivery_idempotent(session, scim):
    """Register row: the same lifecycle event delivered twice has one effect."""
    ts = NOW
    first = process_action(session, scim, worker_id="w9", action_type="disable", effective_ts=ts)
    second = process_action(session, scim, worker_id="w9", action_type="disable", effective_ts=ts)
    session.commit()
    assert first.applied and not first.duplicate
    assert second.duplicate and not second.applied
    assert scim.calls.count(("disable", "w9")) == 1


def test_INT_idp_outage_termination_queued_with_alert(session, scim):
    """Register row: IdP outage during a termination window — the disable is
    queued with an alert, then replays successfully, disables first."""
    scim.outage = True
    result = process_action(session, scim, worker_id="leaver-1", action_type="disable", effective_ts=NOW)
    process_action(session, scim, worker_id="joiner-1", action_type="prestage",
                   effective_ts=NOW - timedelta(hours=1))
    session.commit()
    assert result.queued and not result.applied

    from sqlalchemy import select
    from integration_hub.jml import ProvisioningAction
    queued_disable = session.scalars(select(ProvisioningAction).where(
        ProvisioningAction.action_type == "disable")).one()
    assert queued_disable.alert_raised  # someone got paged

    scim.outage = False
    applied = replay_queued(session, scim)
    session.commit()
    assert applied == 2
    assert scim.calls[0] == ("disable", "leaver-1")  # SLA path leads the replay


def test_prestage_window():
    start = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)
    assert not prestage_due(start, datetime(2026, 6, 27, 9, 0, tzinfo=timezone.utc))
    assert prestage_due(start, datetime(2026, 6, 28, 9, 0, tzinfo=timezone.utc))


def _registry():
    registry = ConsumerRegistry()
    registry.register(ConsumerContract(
        consumer_key="erp-finance", pinned_version=2,
        approved_categories={"personal", "record-keeping"}, tier_ceiling=Tier.T1,
    ))
    return registry


def test_INT_laggard_consumer_pinned_version():
    """Register row: schema evolution with laggard consumers — a consumer never
    receives a payload version newer than its pinned contract."""
    registry = _registry()
    data = {"display_name": "Synthetic", "base_salary": 1}
    with pytest.raises(ContractVersionError, match="pinned to v2"):
        serve_payload(registry, "erp-finance", IntWorkerRow, data, payload_version=3)
    # pinned or older versions serve fine
    assert serve_payload(registry, "erp-finance", IntWorkerRow, data, payload_version=2)


def test_consumer_tier_ceiling_and_category_contract():
    """A comp-blind token: T2 fields and unapproved categories never leave."""
    registry = _registry()
    data = {"display_name": "Synthetic", "email": "x@example.invalid", "base_salary": 99}
    served = serve_payload(registry, "erp-finance", IntWorkerRow, data, payload_version=1)
    assert served == {"display_name": "Synthetic"}  # salary=T2 gone; email category 'contact' unapproved
