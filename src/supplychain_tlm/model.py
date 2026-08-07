"""Model boundary for a future compact CPU SupplyChain-TLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .context import DecisionContext


@dataclass(frozen=True)
class TLMResponse:
    answer: str
    confidence: float
    references: tuple[str, ...]
    suggested_action: str | None = None


class TLMBackend(Protocol):
    name: str

    def answer(self, context: DecisionContext) -> TLMResponse:
        """Answer from context; do not execute enterprise actions."""


class RuleBasedSupplyChainTLM:
    """Deterministic baseline used until a trained model is connected."""

    name = "rule_based_baseline"

    @staticmethod
    def _requires_approval(request: str) -> bool:
        action_terms = ("release", "clearance", "clear", "post", "approve", "execute", "dispatch", "leave the port", "depart")
        lowered = request.lower()
        return any(term in lowered for term in action_terms)

    @staticmethod
    def _bypasses_approval(request: str) -> bool:
        lowered = request.lower()
        return any(
            phrase in lowered
            for phrase in (
                "without approval",
                "bypass approval",
                "skip approval",
                "ignore approval",
                "without authorization",
                "bypass authorization",
            )
        )

    def answer(self, context: DecisionContext) -> TLMResponse:
        facts = dict((key, value) for _, key, value in context.domain_facts)
        if self._bypasses_approval(context.request):
            return TLMResponse(
                answer="I cannot execute or authorize an action that bypasses the required approval.",
                confidence=0.99,
                references=context.references,
                suggested_action="refuse_action",
            )
        if facts.get("approval_present", "true").lower() == "false":
            return TLMResponse(
                answer="I cannot execute or authorize release without an approved approval record.",
                confidence=0.99,
                references=context.references,
                suggested_action="refuse_action",
            )
        if not context.validation_passed:
            codes = ", ".join(context.validation_issue_codes)
            return TLMResponse(
                answer=f"Shipment release should be blocked because validation failed: {codes}.",
                confidence=0.99,
                references=context.references,
                suggested_action="request_document_review",
            )
        if self._requires_approval(context.request):
            return TLMResponse(
                answer="The available document checks passed. The requested action may be proposed for authorized review.",
                confidence=0.90,
                references=context.references,
                suggested_action="request_approval",
            )
        return TLMResponse(
            answer="The available document checks passed. I can explain the evidence, but I will not execute an enterprise action.",
            confidence=0.90,
            references=context.references,
            suggested_action=None,
        )
