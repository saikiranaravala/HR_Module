"""Continuous performance (PERF-3): check-ins with private notes, explicit
feedback visibility, 360 aggregation with anonymity threshold."""
from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from performance.models import Checkin, Feedback

ANONYMITY_THRESHOLD = 3  # §4: no theme shown under 3 raters

VISIBILITIES = {"to-subject", "to-manager"}


def record_checkin(session: Session, *, worker_id: str, manager_id: str,
                   occurred_on: date, shared_notes: str,
                   private_notes: str | None = None,
                   private_author: str | None = None) -> Checkin:
    checkin = Checkin(worker_id=worker_id, manager_id=manager_id,
                      occurred_on=occurred_on, shared_notes=shared_notes,
                      private_notes=private_notes,
                      private_notes_author=private_author)
    session.add(checkin)
    session.flush()
    return checkin


def checkin_view(checkin: Checkin, *, viewer: str) -> dict:
    """Private notes are author-only — they never serialize to the other party."""
    view = {"occurred_on": checkin.occurred_on, "shared_notes": checkin.shared_notes}
    if checkin.private_notes_author == viewer:
        view["private_notes"] = checkin.private_notes
    return view


def give_feedback(session: Session, *, author_id: str, subject_id: str,
                  visibility: str, body: str, competency: str | None = None,
                  campaign_id: str | None = None, on: date) -> Feedback:
    """Visibility is EXPLICIT per item (§4: no silent manager-visible feedback)."""
    if visibility not in VISIBILITIES:
        raise ValueError(f"visibility must be one of {sorted(VISIBILITIES)}")
    item = Feedback(author_id=author_id, subject_id=subject_id,
                    visibility=visibility, body=body, competency=competency,
                    campaign_id=campaign_id, given_on=on)
    session.add(item)
    session.flush()
    return item


def aggregate_360(session: Session, *, campaign_id: str, subject_id: str) -> dict:
    """360 report: competency themes appear only at/above the anonymity
    threshold; below it the competency is withheld entirely."""
    items = session.scalars(select(Feedback).where(
        Feedback.campaign_id == campaign_id,
        Feedback.subject_id == subject_id,
    )).all()
    by_competency: dict[str, list[str]] = defaultdict(list)
    for item in items:
        by_competency[item.competency or "general"].append(item.body)
    themes = {}
    withheld = []
    for competency, bodies in by_competency.items():
        if len(bodies) >= ANONYMITY_THRESHOLD:
            themes[competency] = {"rater_count": len(bodies), "comments": bodies}
        else:
            withheld.append(competency)
    return {"themes": themes, "withheld_below_threshold": sorted(withheld),
            "total_raters": len({i.author_id for i in items})}
