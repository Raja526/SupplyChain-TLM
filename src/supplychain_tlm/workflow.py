"""Local orchestration of ingest, validation, planning, approval, and tools."""

from __future__ import annotations

from dataclasses import dataclass

from .ingest import ShipmentBundle
from .planner import Plan, propose_shipment_release
from .tools import Approval, ApprovalGate, EnterpriseTool, ToolCall


@dataclass(frozen=True)
class WorkflowResult:
    plan: Plan
    approval: Approval | None = None
    tool_result: str | None = None


class ReleaseWorkflow:
    """Coordinates one shipment release without hiding side effects."""

    def __init__(self, gate: ApprovalGate, tool: EnterpriseTool) -> None:
        self.gate = gate
        self.tool = tool

    def prepare(self, bundle: ShipmentBundle) -> WorkflowResult:
        return WorkflowResult(propose_shipment_release(bundle))

    def approve_and_execute(self, bundle: ShipmentBundle, approver: str, comment: str = "") -> WorkflowResult:
        prepared = self.prepare(bundle)
        if not prepared.plan.validation_passed:
            return prepared
        shipment_id = bundle.packing_list.shipment_id
        proposal_id = f"release:{shipment_id}"
        approval = self.gate.approve(proposal_id, approver, comment)
        call = ToolCall(
            tool_name=self.tool.name,
            operation="release_shipment",
            inputs={"shipment_id": shipment_id, "po_number": bundle.purchase_order.po_number},
            idempotency_key=proposal_id,
        )
        result = self.gate.execute(self.tool, call, approval)
        return WorkflowResult(prepared.plan, approval, result)
