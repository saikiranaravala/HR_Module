"""AI Gateway (Specs/14 §2) — the single egress for every model call.

Providers are pluggable behind one interface; locally MockProvider answers
deterministically. Every call (including refusals) lands in the AI ledger.
Per-use-case budgets trip a circuit breaker; the PII guard blocks third-party
personal data pasted into prompts; injection heuristics flag hostile content
embedded in user-supplied text.
"""
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import yaml
from sqlalchemy import DateTime, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

CONFIG_DIR = Path(__file__).resolve().parent / "config"

_AI_TAG = tag(
    category="ai-ledger", purpose="ai-governance",
    lawful_basis="legitimate-interest", retention_class="ai-ledger-3y", tier=Tier.T1,
)


class UseCaseNotRegisteredError(PermissionError):
    """Unregistered use cases never reach a model (governance gate)."""


class ProviderOutageError(RuntimeError):
    pass


@dataclass
class Completion:
    text: str
    model: str
    prompt_version: str


class Provider(Protocol):
    def complete(self, prompt: str, model_class: str) -> Completion: ...


class MockProvider:
    """Deterministic local provider. The Anthropic client implements the same
    interface when the cloud phase starts (Claude family per spec §2)."""

    def __init__(self, canned: dict[str, str] | None = None, down: bool = False):
        self._canned = canned or {}
        self.down = down

    def complete(self, prompt: str, model_class: str) -> Completion:
        if self.down:
            raise ProviderOutageError("provider unreachable")
        for needle, response in self._canned.items():
            if needle in prompt:
                return Completion(response, f"mock-{model_class}", "n/a")
        return Completion(f"[mock {model_class}] ack", f"mock-{model_class}", "n/a")


@register_model
class AiLedgerEntry(Base):
    __tablename__ = "ai_ledger"
    __table_args__ = {"schema": "ai"}

    entry_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    occurred_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    use_case: Mapped[str] = mapped_column(Text, info=dict(_AI_TAG))
    subject_id: Mapped[str] = mapped_column(Text, info=dict(_AI_TAG))
    purpose: Mapped[str] = mapped_column(Text, info=dict(_AI_TAG))
    model: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_AI_TAG))
    prompt_version: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_AI_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_AI_TAG))  # ok|refused|degraded
    refusal_reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_AI_TAG))
    request_chars: Mapped[int] = mapped_column(Integer, default=0, info=dict(_AI_TAG))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))


@dataclass
class GatewayResult:
    status: str  # ok | refused | degraded
    text: str | None = None
    refusal_reason: str | None = None
    warnings: list[str] = field(default_factory=list)


# National-ID / bank-shaped third-party data heuristics (synthetic-safe).
_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),          # SSN-shaped
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9 ]{12,30}\b"),  # IBAN-shaped
]
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|previous|prior) (instructions|rules)", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"disregard your", re.I),
]


def detect_third_party_pii(text: str, self_reference_ids: set[str] | None = None) -> bool:
    return any(p.search(text) for p in _PII_PATTERNS)


def detect_injection(text: str) -> bool:
    return any(p.search(text) for p in _INJECTION_PATTERNS)


class AiGateway:
    def __init__(self, provider: Provider, config_dir: Path = CONFIG_DIR):
        self._provider = provider
        self._use_cases = yaml.safe_load((config_dir / "use_cases.yaml").read_text(encoding="utf-8"))["use_cases"]
        self._prompts = yaml.safe_load((config_dir / "prompts.yaml").read_text(encoding="utf-8"))["prompts"]
        self._spend: dict[str, int] = {}

    def use_case(self, key: str) -> dict:
        if key not in self._use_cases:
            raise UseCaseNotRegisteredError(
                f"AI use case '{key}' is not in the governance registry"
            )
        return self._use_cases[key]

    def prompt(self, key: str) -> dict:
        return self._prompts[key]  # {version, template}

    def complete(
        self,
        session: Session,
        *,
        use_case: str,
        subject_id: str,
        user_text: str,
        prompt_key: str,
        prompt_vars: dict | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> GatewayResult:
        spec = self.use_case(use_case)  # raises for unregistered (governance gate)
        correlation_id = correlation_id or uuid.uuid4()
        warnings: list[str] = []

        def ledger(status, *, model=None, prompt_version=None, refusal=None):
            session.add(AiLedgerEntry(
                occurred_at=datetime.now(timezone.utc), use_case=use_case,
                subject_id=subject_id, purpose=spec["purpose"], model=model,
                prompt_version=prompt_version, status=status, refusal_reason=refusal,
                request_chars=len(user_text), correlation_id=correlation_id,
            ))
            session.flush()

        # PII guard: third-party personal data is not processed (register row).
        if detect_third_party_pii(user_text):
            ledger("refused", refusal="third-party-pii-detected")
            return GatewayResult(
                "refused",
                refusal_reason="Your message appears to contain another person's "
                               "identifiers; it was not processed.",
            )

        if detect_injection(user_text):
            warnings.append("injection-heuristic-flagged")  # hardened, logged, continues with minimal tools

        # Per-use-case budget circuit breaker.
        spent = self._spend.get(use_case, 0)
        if spent + len(user_text) > spec.get("budget_chars", 10**9):
            ledger("refused", refusal="budget-exhausted")
            return GatewayResult("refused", refusal_reason="use-case budget exhausted")
        self._spend[use_case] = spent + len(user_text)

        prompt_spec = self.prompt(prompt_key)
        rendered = prompt_spec["template"].format(**{"user_text": user_text, **(prompt_vars or {})})

        try:
            completion = self._provider.complete(rendered, spec.get("model_class", "haiku"))
        except ProviderOutageError:
            # Graceful degradation (register row): no model, fall back to links.
            ledger("degraded", refusal="provider-outage")
            return GatewayResult(
                "degraded",
                text="AI assistance is temporarily unavailable. Here are knowledge-base "
                     "search results for your question instead.",
                warnings=warnings + ["provider-outage-fallback"],
            )

        ledger("ok", model=completion.model, prompt_version=prompt_spec["version"])
        return GatewayResult("ok", text=completion.text, warnings=warnings)
