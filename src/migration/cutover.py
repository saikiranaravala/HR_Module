"""Cutover tooling (MIG-5): evidence-linked role-signed go/no-go checklist and
the 72-hour rollback decision window."""
from datetime import datetime, timedelta, timezone

ROLLBACK_WINDOW = timedelta(hours=72)
ROLLBACK_RETAINED_CLEAN_CYCLES = 2


class RollbackWindowClosedError(RuntimeError):
    pass


def evaluate_go_no_go(items: list[dict]) -> dict:
    """Every checklist item needs evidence AND a role signature — a checkmark
    without either is a no-go, not a formality."""
    blockers = []
    for item in items:
        if not item.get("evidence_ref"):
            blockers.append(f"'{item['item']}' has no linked evidence")
        if not item.get("signed_by_role"):
            blockers.append(f"'{item['item']}' is not role-signed")
        if not item.get("passed", False):
            blockers.append(f"'{item['item']}' did not pass")
    return {"go": not blockers, "blockers": blockers}


def rollback_decision(*, cutover_at: datetime, requested_at: datetime,
                      clean_cycles_since_cutover: int) -> dict:
    """Register row: rollback is allowed inside the 72-hour decision window,
    and the rehearsed capability is RETAINED until wave + 2 clean cycles —
    after that, rollback is closed and forward-fix is the only path."""
    if requested_at <= cutover_at + ROLLBACK_WINDOW:
        return {"allowed": True, "path": "decision-window",
                "runbook": "ps-reactivation + data-delta replay + comms templates"}
    if clean_cycles_since_cutover < ROLLBACK_RETAINED_CLEAN_CYCLES:
        return {"allowed": True, "path": "retained-capability",
                "runbook": "ps-reactivation + data-delta replay + comms templates",
                "note": "window passed; capability retained until 2 clean cycles"}
    raise RollbackWindowClosedError(
        "rollback closed: 2 clean cycles completed — forward-fix only"
    )
