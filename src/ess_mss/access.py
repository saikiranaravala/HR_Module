"""Access modes & interlocks (Specs/10 §3 + §7 register).

- Alumni: terminated workers keep limited-scope portal access (payslips and
  tax documents ONLY) for a per-country retention window — country packs in
  config, never code branches.
- Legal hold: self-service data changes are frozen with clear messaging; the
  attempt is audit-logged.
- Bank-change fraud interlock: freeze window before payday + out-of-band
  confirmation; every change alerts all registered channels.
"""
import uuid
from datetime import date
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from ess_mss.models import AccessGrant
from platform_core.audit import record_audit
from platform_core.dates import add_months

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "alumni.yaml"

ALUMNI_SCOPE = ["payslip", "tax-doc"]
BANK_CHANGE_FREEZE_DAYS = 3


class AccessExpiredError(PermissionError):
    pass


class ScopeError(PermissionError):
    pass


class LegalHoldFreezeError(PermissionError):
    pass


class BankChangeFrozenError(PermissionError):
    pass


def load_retention_config(path: Path = CONFIG_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["alumni_retention_months"]


def grant_alumni_access(
    session: Session, *, worker_id: str, country: str, terminated_on: date,
    retention_config: dict | None = None,
) -> AccessGrant:
    config = retention_config or load_retention_config()
    months = config.get(country, config["default"])
    grant = AccessGrant(
        worker_id=worker_id, kind="alumni", scope=ALUMNI_SCOPE,
        starts_on=terminated_on,
        expires_on=add_months(terminated_on, months),
    )
    session.add(grant)
    session.flush()
    return grant


def authorize_alumni(grant: AccessGrant, *, resource_kind: str, on: date) -> bool:
    """Alumni auth is limited-scope: docs only, inside the retention window."""
    if grant.released or (grant.expires_on and on > grant.expires_on):
        raise AccessExpiredError("alumni access window has ended")
    if resource_kind not in (grant.scope or []):
        raise ScopeError(f"alumni access does not include '{resource_kind}'")
    return True


def place_legal_hold(session: Session, *, worker_id: str, reason: str, on: date) -> AccessGrant:
    hold = AccessGrant(worker_id=worker_id, kind="legal-hold", reason=reason,
                       starts_on=on, expires_on=None)
    session.add(hold)
    session.flush()
    return hold


def active_legal_hold(session: Session, worker_id: str) -> AccessGrant | None:
    return session.scalars(select(AccessGrant).where(
        AccessGrant.worker_id == worker_id,
        AccessGrant.kind == "legal-hold",
        AccessGrant.released.is_(False),
    )).first()


def check_change_allowed(session: Session, *, worker_id: str, field: str) -> None:
    """Self-service change gate: legal hold freezes data changes with clear
    messaging, and the attempt is audit-logged (register row)."""
    hold = active_legal_hold(session, worker_id)
    if hold is None:
        return
    record_audit(
        session, actor=worker_id, action="deny",
        entity_ref=f"service_delivery.access_grant:{hold.grant_id}",
        after={"detail": f"self-service change to '{field}' blocked by legal hold"},
        sensitivity_tier="T1", source_channel="ess-mss",
        correlation_id=uuid.uuid4(),
    )
    raise LegalHoldFreezeError(
        "Your records are temporarily locked and cannot be changed right now. "
        "Please contact HR for assistance."  # no mention of the hold's reason
    )


def validate_bank_change(*, change_date: date, next_payday: date,
                         out_of_band_confirmed: bool) -> None:
    """Fraud interlock (ESS-1): no bank changes inside the pre-payday freeze
    window; out-of-band confirmation always required."""
    if not out_of_band_confirmed:
        raise BankChangeFrozenError("bank changes require out-of-band confirmation")
    if date.toordinal(next_payday) - date.toordinal(change_date) < BANK_CHANGE_FREEZE_DAYS:
        raise BankChangeFrozenError(
            f"bank details are frozen within {BANK_CHANGE_FREEZE_DAYS} days of payday; "
            "the change will be accepted after this pay run"
        )
