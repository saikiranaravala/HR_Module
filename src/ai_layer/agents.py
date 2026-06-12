"""Agent framework (Specs/14 §4) — typed tools, caller's scope, human gates.

Tools are typed contracts onto Meridian capabilities. Two invariant
enforcement points, both structural:
1. Every tool call is policy-checked with the CALLING USER as subject — agents
   have no privileged identity.
2. Tools that mutate money / employment status / access are GATED: executing
   them produces an AgentDraft; a human commits it through a separate call.
Every tool call writes to the AI ledger via the platform audit pipeline.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from platform_core.audit import record_audit
from platform_core.policy.engine import PolicyEngine, Resource, Subject

GATED_DOMAINS = {"money", "employment-status", "access"}


class HumanGateRequired(PermissionError):
    pass


@dataclass(frozen=True)
class ToolContract:
    name: str
    capability: str               # policy capability the CALLER must hold
    mutates: str | None = None    # None | 'money' | 'employment-status' | 'access' | other
    handler: Callable[..., dict] = None


@dataclass
class AgentDraft:
    draft_id: uuid.UUID
    tool: str
    payload: dict
    drafted_by_agent_for: str  # the human subject
    status: str = "draft"      # draft | committed | discarded


@dataclass
class AgentRuntime:
    policy: PolicyEngine
    tools: dict[str, ToolContract] = field(default_factory=dict)
    drafts: dict[uuid.UUID, AgentDraft] = field(default_factory=dict)
    kill_switch: set[str] = field(default_factory=set)  # disabled tool names

    def register(self, tool: ToolContract) -> None:
        self.tools[tool.name] = tool

    def call_tool(
        self,
        session: Session,
        tool_name: str,
        *,
        subject: Subject,
        resource: Resource,
        payload: dict,
        correlation_id: uuid.UUID | None = None,
    ) -> dict | AgentDraft:
        if tool_name in self.kill_switch:
            raise PermissionError(f"tool '{tool_name}' is disabled (kill switch)")
        tool = self.tools[tool_name]
        correlation_id = correlation_id or uuid.uuid4()

        # Agents inherit the calling user's scope — same decision point as the UI.
        decision = self.policy.decide(subject, tool.capability, resource)
        record_audit(
            session,
            actor=subject.subject_id,
            on_behalf_of=None,
            actor_type="agent",
            action="read" if tool.mutates is None else "insert",
            entity_ref=f"ai.tool:{tool_name}",
            after={"allowed": decision.allow, "capability": tool.capability},
            sensitivity_tier="T1",
            source_channel="ai-agent",
            correlation_id=correlation_id,
        )
        if not decision.allow:
            raise PermissionError(
                f"caller lacks '{tool.capability}' — agent denied identically to UI"
            )

        if tool.mutates in GATED_DOMAINS:
            draft = AgentDraft(
                draft_id=uuid.uuid4(), tool=tool_name, payload=payload,
                drafted_by_agent_for=subject.subject_id,
            )
            self.drafts[draft.draft_id] = draft
            return draft  # agent drafts; human commits

        return tool.handler(session=session, subject=subject, payload=payload)

    def commit_draft(
        self,
        session: Session,
        draft_id: uuid.UUID,
        *,
        human_subject: Subject,
        resource: Resource,
    ) -> dict:
        """The human-approval gate: a person, not the agent, commits the change.
        Enforced at capability level — the commit re-runs the policy decision."""
        draft = self.drafts[draft_id]
        if draft.status != "draft":
            raise ValueError(f"draft is {draft.status}")
        tool = self.tools[draft.tool]

        decision = self.policy.decide(human_subject, tool.capability, resource)
        if not decision.allow:
            raise PermissionError("committing human lacks the capability")

        result = tool.handler(session=session, subject=human_subject, payload=draft.payload)
        draft.status = "committed"
        record_audit(
            session,
            actor=human_subject.subject_id,
            on_behalf_of=draft.drafted_by_agent_for,
            actor_type="user",
            action="insert",
            entity_ref=f"ai.draft:{draft_id}",
            after={"tool": draft.tool, "committed_at": datetime.now(timezone.utc).isoformat()},
            sensitivity_tier="T1",
            source_channel="ai-agent-commit",
            correlation_id=uuid.uuid4(),
        )
        return result
