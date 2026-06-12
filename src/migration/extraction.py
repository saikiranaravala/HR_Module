"""PeopleSoft extraction adapter (MIG-1). PS table shapes and action codes
exist ONLY in this module (Invariant #4) — everything downstream speaks
canonical temporal rows (full EFFDT/EFFSEQ history, never current-state-only).
"""
from datetime import date, timedelta
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent / "config"


class UnmappedActionError(ValueError):
    pass


def load_action_mapping(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "action_mapping.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["actions"]


def transform_ps_job_history(rows: list[dict], *, mapping: dict | None = None) -> list[dict]:
    """PS_JOB rows (EFFDT/EFFSEQ/ACTION/...) → canonical temporal rows.

    The FULL history chain is preserved row-for-row; unmapped PS actions halt
    loudly (semantic review required — never a silent default)."""
    mapping = mapping or load_action_mapping()
    canonical = []
    for row in sorted(rows, key=lambda r: (r["EMPLID"], r["EFFDT"], r["EFFSEQ"])):
        ps_action = row["ACTION"]
        if ps_action not in mapping:
            raise UnmappedActionError(
                f"PS action '{ps_action}' has no taxonomy mapping — add it to "
                "action_mapping.yaml after semantic review"
            )
        canonical.append({
            "worker_ref": row["EMPLID"],
            "effective_date": row["EFFDT"],
            "effective_sequence": row["EFFSEQ"],
            "action_code": mapping[ps_action]["action"],
            "action_reason": mapping[ps_action].get("reason"),
            "job_code": row.get("JOBCODE"),
            "department": row.get("DEPTID"),
            "fte": row.get("FTE", 1.0),
            "worker_status": mapping[ps_action].get("status", "active"),
        })
    return canonical


def recompute_rehire_bridging(canonical: list[dict], *, bridge_gap_days: int = 365) -> list[dict]:
    """Rehire-bridging recomputation with a diff report vs PS values (§3):
    original hire date bridges across gaps shorter than the policy window."""
    by_worker: dict[str, list[dict]] = {}
    for row in canonical:
        by_worker.setdefault(row["worker_ref"], []).append(row)
    diffs = []
    for worker, rows in by_worker.items():
        hires = [r for r in rows if r["action_code"] in ("hire", "rehire")]
        terms = [r for r in rows if r["action_code"] == "termination"]
        if len(hires) < 2 or not terms:
            continue
        gap = (hires[1]["effective_date"] - terms[0]["effective_date"]).days
        bridged = gap <= bridge_gap_days
        diffs.append({
            "worker_ref": worker,
            "computed_service_date": hires[0]["effective_date"] if bridged else hires[1]["effective_date"],
            "gap_days": gap,
            "bridged": bridged,
        })
    return diffs


def discover_orphan_feeds(*, documented_feeds: set[str],
                          observed_connections: list[dict]) -> list[dict]:
    """Risk register: orphan integrations nobody documented — diff observed
    PS host traffic against the integration inventory (month-1 workstream)."""
    orphans = []
    for connection in observed_connections:
        if connection["feed"] not in documented_feeds:
            orphans.append({**connection, "flag": "orphan-feed",
                            "action": "identify consumer before cutover"})
    return orphans
