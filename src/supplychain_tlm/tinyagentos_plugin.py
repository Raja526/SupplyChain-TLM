"""TinyAgentOS integration for the deterministic SupplyChain-TLM baseline.

The adapter keeps document reasoning in this package and exposes it through
TinyAgentOS service names. Enterprise actions remain behind TinyAgentOS's
explicit approval and idempotency checks.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .context import build_decision_context
from .ingest import bundle_from_dict
from .model import RuleBasedSupplyChainTLM
from .planner import propose_shipment_release
from .router import route_request
from .validation import validate_shipment_bundle

try:
    from tinyagentos import CallableStage, ExecutionContext, Pipeline, TinyAgent
    from tinyagentos.kernel import Kernel
    from tinyagentos.tools import ToolExecutor
except ImportError as exc:  # pragma: no cover - exercised by optional install checks
    CallableStage = ExecutionContext = Pipeline = TinyAgent = Any  # type: ignore[misc,assignment]
    Kernel = Any  # type: ignore[misc,assignment]
    ToolExecutor = None  # type: ignore[assignment]
    _TINYAGENTOS_IMPORT_ERROR = exc
else:
    _TINYAGENTOS_IMPORT_ERROR = None


class ReleaseShipmentTool:
    """Demo action; replace its body with an ERP connector at deployment time."""

    name = "release_shipment"

    def execute(self, arguments: dict[str, Any]) -> str:
        shipment_id = str(arguments["shipment_id"])
        return f"dry-run:release:{shipment_id}"


def answer_request(request: str, bundle: dict[str, Any], *, approved: bool = True) -> dict[str, Any]:
    """Return a JSON-safe domain answer for use by an agent stage or API."""
    typed_bundle = bundle_from_dict(bundle)
    context = build_decision_context(request, typed_bundle)
    if not approved:
        context = replace(
            context,
            domain_facts=context.domain_facts + (
                ("compliance", "approval_present", "false"),
                ("compliance", "approval_bypass_requested", "true"),
            ),
        )
    response = RuleBasedSupplyChainTLM().answer(context)
    return {
        "answer": response.answer,
        "confidence": response.confidence,
        "references": list(response.references),
        "suggested_action": response.suggested_action,
        "capabilities": list(context.capabilities),
        "validation_passed": context.validation_passed,
        "validation_issue_codes": list(context.validation_issue_codes),
    }


def plan_release(bundle: dict[str, Any]) -> dict[str, Any]:
    """Create a JSON-safe release proposal without executing it."""
    plan = propose_shipment_release(bundle_from_dict(bundle))
    return {
        "goal": plan.goal,
        "validation_passed": plan.validation_passed,
        "references": list(plan.references),
        "proposals": [
            {
                "action": proposal.action,
                "status": proposal.status,
                "reason": proposal.reason,
                "required_approval": proposal.required_approval,
                "inputs": list(proposal.inputs),
            }
            for proposal in plan.proposals
        ],
    }


@dataclass
class SupplyChainTLMPlugin:
    """Register SupplyChain-TLM capabilities in a TinyAgentOS kernel."""

    name: str = "supplychain-tlm"
    required_approver: str = "procurement_manager"

    def activate(self, kernel: Kernel) -> None:
        if _TINYAGENTOS_IMPORT_ERROR is not None or ToolExecutor is None:
            raise RuntimeError("TinyAgentOS is required; add it to PYTHONPATH or install the package") from _TINYAGENTOS_IMPORT_ERROR
        kernel.registry.register("supplychain.router", route_request)
        kernel.registry.register("supplychain.validator", validate_shipment_bundle)
        kernel.registry.register("supplychain.tlm", answer_request)
        kernel.registry.register("supplychain.planner", plan_release)
        tools = ToolExecutor(required_approver=self.required_approver)
        tools.register(ReleaseShipmentTool())
        kernel.registry.register("supplychain.tools", tools)


def build_agent(request: str, bundle: dict[str, Any], *, approved: bool = True, model: Any | None = None) -> Any:
    """Build a pipeline with an optional CPU model explanation.

    The model output is returned as advisory text only. Deterministic answer
    and planner fields are produced independently and remain authoritative.
    """
    pipeline = Pipeline()

    if model is not None:
        def explain(context: Any) -> Any:
            context.variables["model_explanation"] = model.generate(context)
            return context

        pipeline.add_stage(CallableStage(explain))

    def decide(context: Any) -> Any:
        context.variables["output"] = {
            "answer": answer_request(request, bundle, approved=approved),
            "plan": plan_release(bundle),
            "model_explanation": context.variables.get("model_explanation"),
        }
        return context

    pipeline.add_stage(CallableStage(decide))
    return TinyAgent(pipeline=pipeline, plugins=[SupplyChainTLMPlugin()])
