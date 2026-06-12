"""Regenerate SQL/DDL/*.sql from the live alembic-managed database.
Usage: python SQL/DDL/_generate.py  (requires local PostgreSQL 17 + meridian_dev)"""
import os
import pathlib
import re
import subprocess

PG_DUMP = r"C:\Program Files\PostgreSQL\17\bin\pg_dump"
SCHEMAS = ["platform", "workflow", "integration", "ai", "core", "time_labor",
           "payroll", "benefits", "service_delivery", "analytics", "comp",
           "recruiting", "performance", "learning", "succession", "migration"]
DESC = {
    "platform": "audit_event (hash-chained, immutable), policy_decision_log, forbid_mutation()",
    "workflow": "workflow_instance, step_execution (Specs/12)",
    "integration": "connector_run/credential, provisioning_action (Specs/13)",
    "ai": "ai_ledger - every gateway call (Specs/14)",
    "core": "person, person_name*, national_id, work_eligibility, worker, assignment*, department, position (*temporal+immutable)",
    "time_labor": "time_entry, time_result, accrual_lot (Specs/02)",
    "payroll": "pay_cycle, pay_input_record, pay_result_record (Specs/03)",
    "benefits": "benefit_plan, benefit_rate, enrollment (Specs/04)",
    "service_delivery": "case, case_note, kb_article, delegation, notification_pref, access_grant (Specs/10)",
    "analytics": "dim_worker (SCD2), certified_snapshot (immutable), org_bridge (Specs/11)",
    "comp": "grade_range*, comp_record* (temporal+immutable), comp_cycle, cycle_line (Specs/05)",
    "recruiting": "candidate_profile, requisition, application, offer (Specs/06)",
    "performance": "goal, review_cycle, review_doc, calibration_adjustment (immutable), checkin, feedback (Specs/07)",
    "learning": "content_item, assignment, completion_record (immutable), certification (Specs/08)",
    "succession": "key_position, slate_entry, talent_profile, ninebox_placement (immutable), discovery_hold (Specs/09)",
    "migration": "staged_record (idempotency unique), dq_exception, gate_artifact (immutable), sync_conflict (Specs/16)",
}

OUT = pathlib.Path(__file__).resolve().parent
SKIP_PREFIXES = ("SET ", "SELECT pg_catalog.set_config", "-- Dumped")
SKIP_BACKSLASH = ("restrict", "unrestrict")


def clean(raw: str, schema: str) -> str:
    lines = []
    for line in raw.splitlines():
        if line.startswith(SKIP_PREFIXES):
            continue
        if line.startswith("\\") and line[1:].split(" ")[0] in SKIP_BACKSLASH:
            continue
        if line.strip() in ("-- PostgreSQL database dump", "-- PostgreSQL database dump complete"):
            continue
        lines.append(line)
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return body.replace(f"CREATE SCHEMA {schema};", f"CREATE SCHEMA IF NOT EXISTS {schema};")


def main() -> None:
    for i, schema in enumerate(SCHEMAS, start=1):
        raw = subprocess.run(
            [PG_DUMP, "-h", "localhost", "-U", "meridian_dev", "-d", "meridian",
             "-s", "--no-owner", "--no-privileges", "-n", schema],
            env={**os.environ, "PGPASSWORD": "meridian_dev"},
            capture_output=True, text=True, check=True,
        ).stdout
        header = (
            f"-- SQL/DDL/{i:02d}_{schema}.sql - {DESC[schema]}\n"
            "-- Generated from the live alembic-managed database (rev 0016) via pg_dump.\n"
            "-- Canonical source of truth remains migrations/versions/ (alembic upgrade head);\n"
            "-- use these files only to build a standalone copy, then: alembic stamp head.\n\n"
        )
        path = OUT / f"{i:02d}_{schema}.sql"
        path.write_text(header + clean(raw, schema) + "\n", encoding="utf-8")
        print("wrote", path.name, len(raw.splitlines()), "->", len(path.read_text(encoding='utf-8').splitlines()), "lines")


if __name__ == "__main__":
    main()
