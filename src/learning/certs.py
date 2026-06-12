"""Certification & license tracking (LEARN-3): expiry pipeline, job-requirement
linkage raising compliance flags (policy-gated blocks, never local)."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from learning.models import Certification

ALERT_DAYS = (90, 60, 30)


def register_certification(session: Session, *, worker_id: str, cert_type: str,
                           issuer: str, issued_on: date, expires_on: date | None,
                           evidence_ref: str | None = None,
                           job_required: bool = False) -> Certification:
    cert = Certification(worker_id=worker_id, cert_type=cert_type, issuer=issuer,
                         issued_on=issued_on, expires_on=expires_on,
                         evidence_ref=evidence_ref, job_required=job_required)
    session.add(cert)
    session.flush()
    return cert


def expiry_alerts(session: Session, *, today: date) -> list[dict]:
    """90/60/30 pipeline to worker + manager."""
    alerts = []
    certs = session.scalars(select(Certification).where(
        Certification.expires_on.isnot(None))).all()
    for cert in certs:
        days_left = (cert.expires_on - today).days
        for threshold in ALERT_DAYS:
            if days_left == threshold:
                alerts.append({"worker_id": cert.worker_id, "cert": cert.cert_type,
                               "days_left": threshold,
                               "recipients": ["worker", "manager"]})
    return alerts


def lapsed_required_certs(session: Session, *, today: date) -> list[dict]:
    """Job-required cert lapsed ⇒ compliance flag (+ assignment-block candidate
    for the policy layer to act on — never blocked here)."""
    lapsed = session.scalars(select(Certification).where(
        Certification.job_required.is_(True),
        Certification.expires_on < today,
    )).all()
    return [{"worker_id": c.worker_id, "cert": c.cert_type,
             "flag": "required-cert-lapsed", "assignment_block_candidate": True}
            for c in lapsed]
