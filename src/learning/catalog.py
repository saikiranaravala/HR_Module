"""Catalog & completions (LEARN-1): content versioning with supersede policy,
version-pinned completion evidence, equivalencies, transcript import."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from learning.models import Assignment, CompletionRecord, ContentItem


def publish_version(session: Session, *, content_key: str, title: str,
                    supersede_policy: str) -> ContentItem:
    """New content version. Policy decides in-progress learners' fate:
    finish-old keeps them on their pinned version; restart re-baselines them."""
    current = session.scalars(select(ContentItem).where(
        ContentItem.content_key == content_key, ContentItem.active.is_(True),
    )).first()
    version = 1
    if current is not None:
        current.active = False
        version = current.version + 1
    item = ContentItem(content_key=content_key, title=title, version=version,
                       supersede_policy=supersede_policy)
    session.add(item)
    session.flush()

    if current is not None and supersede_policy == "restart":
        in_progress = session.scalars(select(Assignment).where(
            Assignment.content_key == content_key,
            Assignment.status == "in-progress",
        )).all()
        for assignment in in_progress:
            assignment.status = "assigned"
            assignment.content_version = version
            assignment.suspend_data = None
            assignment.suspend_checksum = None
    session.flush()
    return item


def record_completion(
    session: Session, assignment: Assignment, *, score: int | None,
    completed_at: datetime | None = None,
) -> CompletionRecord:
    """Evidence record pins the content version taken — immutable thereafter."""
    record = CompletionRecord(
        worker_id=assignment.worker_id, requirement_key=assignment.requirement_key,
        content_key=assignment.content_key, content_version=assignment.content_version,
        score=score, completed_at=completed_at or datetime.now(timezone.utc),
        source="native",
    )
    assignment.status = "completed"
    session.add(record)
    session.flush()
    return record


def record_equivalency(
    session: Session, *, worker_id: str, requirement_key: str, content_key: str,
    evidence_ref: str, approved_by: str,
) -> CompletionRecord:
    """External cert / prior completion satisfies a requirement — with evidence
    and a named approver (§2 equivalencies)."""
    record = CompletionRecord(
        worker_id=worker_id, requirement_key=requirement_key,
        content_key=content_key, content_version=0,  # external: no native version
        score=None, completed_at=datetime.now(timezone.utc),
        source="equivalency", evidence_ref=evidence_ref, approved_by=approved_by,
    )
    session.add(record)
    session.flush()
    return record


def import_transcripts(session: Session, *, rows: list[dict],
                       compliance_keys: set[str]) -> dict:
    """Register row: acquired-population import — the guaranteed minimum is
    compliance-relevant history; everything else is best-effort and reported."""
    imported, skipped = 0, []
    for row in rows:
        if row.get("requirement_key") in compliance_keys:
            session.add(CompletionRecord(
                worker_id=row["worker_id"], requirement_key=row["requirement_key"],
                content_key=row.get("content_key", "imported"),
                content_version=row.get("content_version", 0),
                score=row.get("score"),
                completed_at=row["completed_at"],
                source="import", evidence_ref=row.get("evidence_ref"),
            ))
            imported += 1
        else:
            skipped.append(row.get("requirement_key") or "untagged")
    session.flush()
    return {"imported_compliance_records": imported,
            "skipped_non_compliance": skipped}


def transcript(session: Session, worker_id: str) -> list[CompletionRecord]:
    return session.scalars(select(CompletionRecord).where(
        CompletionRecord.worker_id == worker_id,
    ).order_by(CompletionRecord.completed_at)).all()
