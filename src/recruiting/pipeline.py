"""Pipeline & selection (REC-3): stage flows, deterministic knockouts,
OFCCP dispositions, AI rank-and-explain (advisory only — never auto-reject),
data walls, and the do-not-rehire policy gate."""
import uuid
from datetime import date
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_layer.gateway import AiGateway
from platform_core.policy.engine import PolicyEngine, Resource, Subject
from recruiting.models import Application, CandidateProfile, Requisition

CONFIG_DIR = Path(__file__).resolve().parent / "config"

# OFCCP-compliant disposition taxonomy — mandatory at rejection.
DISPOSITION_CODES = {
    "not-qualified-min", "less-qualified-than-selected", "withdrew",
    "did-not-respond", "knockout-failed", "req-cancelled", "salary-mismatch",
}


class DispositionRequiredError(ValueError):
    pass


class AiCannotRejectError(PermissionError):
    pass


class StageFlowError(ValueError):
    pass


def load_stage_flow(template: str, path: Path | None = None) -> list[str]:
    path = path or CONFIG_DIR / "stage_flows.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["templates"][template]


def load_knockouts(path: Path | None = None) -> list[dict]:
    path = path or CONFIG_DIR / "knockout.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["rules"]


def apply_to_requisition(
    session: Session, *, candidate: CandidateProfile, req: Requisition,
    applied_on: date, internal: bool = False, confidential: bool = False,
) -> Application:
    app = Application(candidate_id=candidate.candidate_id,
                      requisition_id=req.requisition_id,
                      internal=internal, confidential=confidential,
                      applied_on=applied_on)
    session.add(app)
    session.flush()
    return app


def knockout_check(answers: dict, rules: list[dict] | None = None) -> tuple[bool, str | None]:
    """Knockouts are OBJECTIVE deterministic rules (work auth, license) —
    explicitly not AI (§4)."""
    rules = rules if rules is not None else load_knockouts()
    for rule in rules:
        value = answers.get(rule["question"])
        if value != rule["required"]:
            return False, rule["question"]
    return True, None


def advance_stage(session: Session, app: Application, *, flow: list[str]) -> Application:
    try:
        index = flow.index(app.stage)
    except ValueError:
        raise StageFlowError(f"stage '{app.stage}' not in flow {flow}")
    if index == len(flow) - 1:
        raise StageFlowError("already at final stage")
    app.stage = flow[index + 1]
    session.flush()
    return app


def reject(session: Session, app: Application, *, actor: str,
           disposition_code: str | None) -> Application:
    """Rejection is a HUMAN action with a mandatory OFCCP code. There is no
    code path from AI ranking to this function (Invariant #6)."""
    if actor == "ai" or actor.startswith("ai:"):
        raise AiCannotRejectError("AI never rejects candidates")
    if disposition_code not in DISPOSITION_CODES:
        raise DispositionRequiredError(
            f"disposition code required at rejection; got {disposition_code!r}"
        )
    app.status = "rejected"
    app.disposition_code = disposition_code
    session.flush()
    return app


def ai_rank(
    session: Session, gateway: AiGateway, *, req: Requisition,
    applications: list[tuple[Application, str]], recruiter_id: str,
) -> list[Application]:
    """Rank-and-explain (REC-3): writes advisory ai_rank/ai_explanation only.
    Recruiter sees and may ignore; statuses and stages are untouched."""
    for position, (app, resume_summary) in enumerate(applications, start=1):
        completion = gateway.complete(
            session, use_case="resume-rank-explain", subject_id=recruiter_id,
            user_text=resume_summary, prompt_key="classify",
            prompt_vars={"labels": f"fit-rank for {req.title}"},
        )
        app.ai_rank = position
        app.ai_explanation = completion.text if completion.status == "ok" else None
    session.flush()
    return [a for a, _ in applications]


def visible_do_not_rehire(policy: PolicyEngine, subject: Subject,
                          candidate: CandidateProfile) -> bool | None:
    """Register row: the do-not-rehire flag is policy-gated (capability
    `candidate.read-dnr`) — recruiters without it see nothing, not False."""
    decision = policy.decide(subject, "candidate.read-dnr",
                             Resource(country=candidate.country))
    if not decision.allow:
        return None
    return candidate.do_not_rehire


def visible_to_manager(app: Application, *, manager_of_candidate: bool) -> bool:
    """Register row: internal-candidate data wall — a confidential internal
    application is invisible to the candidate's current manager."""
    if app.internal and app.confidential and manager_of_candidate:
        return False
    return True


def rejection_notification(app: Application) -> dict:
    """Internal rejections use sensitive handling: personal channel, no
    manager copy (register row)."""
    if app.internal:
        return {"channel": "personal-private", "copy_manager": False,
                "template": "internal-candidate-rejection"}
    return {"channel": "candidate-portal", "copy_manager": False,
            "template": "standard-rejection"}
