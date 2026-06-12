"""Report runner with inherited security (ANLT-1).

A report can never reveal data its runner couldn't see in the UI: every row
goes through the SAME central policy decision (`person.read` against the row's
country/org scope) and the SAME tier filter (`serialize_filtered`) the API
uses. There is no report-side re-implementation of access logic (Invariant #3).
"""
import uuid

from sqlalchemy.orm import Session

from analytics.models import DimWorker
from platform_core.policy.engine import (
    PolicyEngine,
    Resource,
    Subject,
    read_with_audit,
)


def run_report(
    session: Session, policy: PolicyEngine, *, subject: Subject,
    rows: list[DimWorker], columns: list[str],
    correlation_id: uuid.UUID | None = None,
) -> list[dict]:
    correlation_id = correlation_id or uuid.uuid4()
    output = []
    for row in rows:
        decision = policy.decide(
            subject, "person.read",
            Resource(country=row.country, org_path=row.org_path, owner_id=row.worker_key),
        )
        if not decision.allow:
            continue  # denied rows simply don't exist for this runner
        data = {c: getattr(row, c) for c in columns}
        filtered = read_with_audit(
            session, DimWorker, data, decision, subject=subject,
            entity_ref=f"analytics.dim_worker:{row.row_id}",
            source_channel="report", correlation_id=correlation_id,
        )
        if filtered:
            output.append(filtered)
    return output
