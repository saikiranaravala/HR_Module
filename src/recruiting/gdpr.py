"""Candidate privacy (REC-2): retention clocks and erasure mid-pipeline."""
import uuid
from datetime import date
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.audit import record_audit
from recruiting.models import Application, CandidateProfile, Offer

CONFIG_DIR = Path(__file__).resolve().parent / "config"


class ErasureRefusedError(PermissionError):
    pass


def load_retention(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "retention.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["retention_months"]


def retention_expired(candidate: CandidateProfile, *, on: date,
                      retention: dict | None = None) -> bool:
    from platform_core.dates import add_months
    retention = retention or load_retention()
    months = retention.get(candidate.country, retention["default"])
    if candidate.consent_captured_on is None:
        return True
    return on > add_months(candidate.consent_captured_on, months)


def erase_candidate(session: Session, candidate: CandidateProfile, *, actor: str) -> dict:
    """Register row: GDPR erasure mid-pipeline. PII is anonymized in place;
    stage/disposition history stays identity-free (OFCCP applicant-flow
    statistics, documented lawful retention). Candidates with an ACCEPTED
    offer are refused — processing basis is now contract, stated in the error."""
    apps = session.scalars(select(Application).where(
        Application.candidate_id == candidate.candidate_id)).all()
    app_ids = [a.application_id for a in apps]
    if app_ids:
        accepted = session.scalars(select(Offer).where(
            Offer.application_id.in_(app_ids), Offer.status == "accepted")).first()
        if accepted is not None:
            raise ErasureRefusedError(
                "erasure refused: an accepted offer exists — processing basis is "
                "contract (GDPR art. 6(1)(b)), not consent"
            )

    candidate.full_name = None
    candidate.email = None
    candidate.erased = True
    for app in apps:
        if app.status == "active":
            app.status = "withdrawn"
            app.disposition_code = "withdrew"
        app.ai_explanation = None  # may quote resume text
    session.flush()
    record_audit(
        session, actor=actor, action="update",
        entity_ref=f"recruiting.candidate_profile:{candidate.candidate_id}",
        after={"detail": "erasure executed; flow statistics retained identity-free"},
        sensitivity_tier="T1", source_channel="recruiting",
        correlation_id=uuid.uuid4(),
    )
    return {"erased": True, "applications_closed": len(apps)}
