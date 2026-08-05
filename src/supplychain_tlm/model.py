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

    def answer(self, context: DecisionContext) -> TLMResponse:
        if not context.validation_passed:
            codes = ", ".join(context.validation_issue_codes)
            return TLMResponse(
                answer=f"Shipment release should be blocked because validation failed: {codes}.",
                confidence=0.99,
                references=context.references,
                suggested_action="request_document_review",
            )
        return TLMResponse(
            answer="The available document checks passed. Shipment release may be proposed for authorized review.",
            confidence=0.90,
            references=context.references,
            suggested_action="request_approval",
        )
