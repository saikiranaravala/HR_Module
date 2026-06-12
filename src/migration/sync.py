"""Bidirectional sync core (MIG-4) — the program's highest technical risk.

Field-ownership matrix per phase decides who wins; concurrent edits to the
same field raise conflicts (4-hour SLA queue); lag > 15 min alerts; the
kill-switch reverts to one-way PS-authoritative and parks open conflicts —
a loud halt, never quiet degradation."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from migration.models import SyncConflict

CONFIG_DIR = Path(__file__).resolve().parent / "config"

CONFLICT_SLA = timedelta(hours=4)
LAG_ALERT = timedelta(minutes=15)


class SyncKilledError(RuntimeError):
    pass


def load_ownership(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "ownership_matrix.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["phases"]


class SyncEngine:
    def __init__(self, *, phase: str, ownership: dict | None = None):
        self.phase = phase
        self.matrix = (ownership or load_ownership())[phase]
        self.mode = "bidirectional" if self.matrix.get("bidirectional") else "one-way"
        self.last_sync_at: datetime | None = None

    def owner_of(self, field: str) -> str:
        return self.matrix["fields"].get(field, self.matrix["default_owner"])

    def apply_change(self, session: Session, *, worker_ref: str, field: str,
                     ps_value: str | None, meridian_value: str | None,
                     now: datetime | None = None) -> dict:
        """Both sides changed the same field in the window ⇒ ownership decides
        the applied value AND a conflict is queued for human confirmation."""
        if self.mode == "one-way" and meridian_value is not None and ps_value is not None:
            raise SyncKilledError("sync is one-way (PS-authoritative); Meridian "
                                  "writes are queued, not merged")
        now = now or datetime.now(timezone.utc)
        self.last_sync_at = now
        owner = self.owner_of(field)
        if ps_value is not None and meridian_value is not None and ps_value != meridian_value:
            conflict = SyncConflict(
                worker_ref=worker_ref, field=field, ps_value=ps_value,
                meridian_value=meridian_value, detected_at=now,
                sla_due_at=now + CONFLICT_SLA,
            )
            session.add(conflict)
            session.flush()
            return {"applied": ps_value if owner == "ps" else meridian_value,
                    "winner": owner, "conflict_id": conflict.conflict_id}
        return {"applied": ps_value if ps_value is not None else meridian_value,
                "winner": owner, "conflict_id": None}

    def lag_alert(self, *, now: datetime) -> bool:
        if self.last_sync_at is None:
            return True
        return now - self.last_sync_at > LAG_ALERT

    def kill_switch(self, session: Session, *, reason: str) -> dict:
        """Revert to one-way PS-authoritative; park open conflicts loudly."""
        self.mode = "one-way"
        open_conflicts = session.scalars(select(SyncConflict).where(
            SyncConflict.status == "open")).all()
        for conflict in open_conflicts:
            conflict.status = "parked"
            conflict.resolution = f"kill-switch: {reason}"
        session.flush()
        return {"mode": self.mode, "parked_conflicts": len(open_conflicts)}


def overdue_conflicts(session: Session, *, now: datetime) -> list[SyncConflict]:
    return session.scalars(select(SyncConflict).where(
        SyncConflict.status == "open",
        SyncConflict.sla_due_at < now,
    )).all()
