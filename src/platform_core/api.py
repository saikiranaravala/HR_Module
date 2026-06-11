"""Platform API (internal): policy decisions, audit verification, RoP register.

Conventions per CLAUDE.md: /v1 prefix, RFC7807 errors, X-Correlation-Id
propagation. Other services normally call the policy engine in-process; this
HTTP surface exists so every consumer type (UI, reports, AI gateway) hits the
same decision point.
"""
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from platform_core import catalog
from platform_core.audit import verify_chain
from platform_core.db import make_engine, make_session_factory
from platform_core.policy.engine import PolicyEngine, Resource, Subject

app = FastAPI(title="Meridian Platform Core", version="0.1.0")
_engine = None
_policy_engine = PolicyEngine()


def _session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    return make_session_factory(_engine)()


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


def problem(status: int, title: str, detail: str, correlation_id: str | None = None) -> JSONResponse:
    body = {
        "type": f"https://meridian.local/problems/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
    }
    if correlation_id:
        body["correlationId"] = correlation_id
    return JSONResponse(status_code=status, content=body, media_type="application/problem+json")


class DecideRequest(BaseModel):
    subject_id: str
    roles: list[str]
    capability: str
    resource_country: str | None = None
    resource_org_path: str | None = None
    resource_population: str | None = None
    resource_owner_id: str | None = None


@app.post("/v1/policy/decide")
def decide(body: DecideRequest, request: Request):
    decision = _policy_engine.decide(
        Subject(subject_id=body.subject_id, roles=tuple(body.roles)),
        body.capability,
        Resource(
            country=body.resource_country,
            org_path=body.resource_org_path,
            population=body.resource_population,
            owner_id=body.resource_owner_id,
        ),
    )
    return {
        "allow": decision.allow,
        "clearance": decision.clearance.value,
        "policyVersion": decision.policy_version,
        "reasons": decision.reasons,
        "correlationId": request.state.correlation_id,
    }


@app.get("/v1/audit/verify")
def audit_verify(request: Request, start_seq: int = 1):
    try:
        with _session() as session:
            broken = verify_chain(session, start_seq=start_seq)
    except Exception as exc:  # noqa: BLE001
        return problem(503, "Audit verification unavailable", str(exc), request.state.correlation_id)
    return {"intact": broken is None, "firstBrokenSeq": broken,
            "correlationId": request.state.correlation_id}


@app.get("/v1/catalog/records-of-processing")
def records_of_processing():
    return {"register": catalog.records_of_processing()}
