"""Transform/validate/load factory (MIG-2): versioned mapping specs, idempotent
re-runs, DQ scorecards with threshold gates, steward exception queue."""
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from migration.models import DqException, StagedRecord

CONFIG_DIR = Path(__file__).resolve().parent / "config"

DQ_RULES = ("completeness", "validity", "referential", "uniqueness")


def load_mapping_specs(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "mapping_specs.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["domains"]


def stage_batch(session: Session, *, batch_id: str, domain: str,
                rows: list[dict]) -> dict:
    """Idempotent staging: (batch_id, source_key) is the natural key — re-runs
    of the same batch never duplicate (the pipeline runs weekly for months)."""
    existing = {
        r.source_key for r in session.scalars(select(StagedRecord).where(
            StagedRecord.batch_id == batch_id, StagedRecord.domain == domain)).all()
    }
    staged, skipped = 0, 0
    for row in rows:
        if row["source_key"] in existing:
            skipped += 1
            continue
        session.add(StagedRecord(batch_id=batch_id, domain=domain,
                                 source_key=row["source_key"], payload=row))
        existing.add(row["source_key"])
        staged += 1
    session.flush()
    return {"staged": staged, "skipped_duplicates": skipped}


def dq_scorecard(session: Session, *, batch_id: str, domain: str,
                 spec: dict, known_refs: set[str]) -> dict:
    """Per-domain scorecard over staged rows: completeness / validity /
    referential / uniqueness rates, with exceptions queued for stewards."""
    records = session.scalars(select(StagedRecord).where(
        StagedRecord.batch_id == batch_id, StagedRecord.domain == domain)).all()
    total = len(records)
    if total == 0:
        return {"total": 0, "scores": {}, "exceptions": 0}

    failures = {rule: 0 for rule in DQ_RULES}
    seen_keys: set[str] = set()
    exceptions = 0
    for record in records:
        payload = record.payload
        for field in spec.get("required_fields", []):
            if payload.get(field) in (None, ""):
                failures["completeness"] += 1
                exceptions += _queue(session, batch_id, domain, "completeness",
                                     record.source_key,
                                     f"populate '{field}' in PeopleSoft (source-correct, not in-flight)")
                break
        for field, allowed in spec.get("valid_values", {}).items():
            if payload.get(field) is not None and payload[field] not in allowed:
                failures["validity"] += 1
                exceptions += _queue(session, batch_id, domain, "validity",
                                     record.source_key,
                                     f"'{field}'='{payload[field]}' not in {allowed}")
                break
        ref_field = spec.get("referential_field")
        if ref_field and payload.get(ref_field) not in known_refs:
            failures["referential"] += 1
            exceptions += _queue(session, batch_id, domain, "referential",
                                 record.source_key,
                                 f"'{ref_field}'='{payload.get(ref_field)}' unknown in target")
        if record.source_key in seen_keys:
            failures["uniqueness"] += 1
        seen_keys.add(record.source_key)

    scores = {rule: round(1 - failures[rule] / total, 4) for rule in DQ_RULES}
    return {"total": total, "scores": scores, "exceptions": exceptions}


def _queue(session: Session, batch_id, domain, rule, source_ref, guidance) -> int:
    session.add(DqException(batch_id=batch_id, domain=domain, rule=rule,
                            source_ref=source_ref, guidance=guidance))
    session.flush()
    return 1


def threshold_gate(scorecard: dict, *, thresholds: dict) -> tuple[bool, list[str]]:
    """Quality gate: every rule must clear its threshold to proceed."""
    blockers = []
    for rule, minimum in thresholds.items():
        score = scorecard["scores"].get(rule, 0)
        if score < minimum:
            blockers.append(f"{rule} {score:.4f} < required {minimum}")
    return (not blockers, blockers)
