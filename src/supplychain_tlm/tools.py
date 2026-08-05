"""Side-effect boundaries for future ERP, messaging, and database tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
import uuid


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    operation: str
    inputs: dict[str, Any]
    idempotency_key: str


@dataclass(frozen=True)
class Approval:
    approver: str
    decision: str
    proposal_id: str
    comment: str = ""


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    timestamp: str
    reference: str
    details: str


class EnterpriseTool(Protocol):
    name: str

    def execute(self, call: ToolCall) -> str:
        """Perform one already-authorized, idempotent operation."""


class AuditLog:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event_type: str, reference: str, details: str) -> None:
        self.events.append(AuditEvent(event_type, datetime.now(timezone.utc).isoformat(), reference, details))


@dataclass
class ApprovalGate:
    audit: AuditLog = field(default_factory=AuditLog)

    def approve(self, proposal_id: str, approver: str, comment: str = "") -> Approval:
        approval = Approval(approver, "approved", proposal_id, comment)
        self.audit.record("approval", proposal_id, f"approved by {approver}")
        return approval

    def execute(self, tool: EnterpriseTool, call: ToolCall, approval: Approval | None = None) -> str:
        """Execute only an approved call and always write audit events."""
        call_id = call.idempotency_key or str(uuid.uuid4())
        if approval is None or approval.decision != "approved":
            self.audit.record("blocked_tool_call", call_id, f"tool={tool.name} operation={call.operation}")
            raise PermissionError("tool call requires an approved approval record")
        self.audit.record("tool_call_started", call_id, f"tool={tool.name} operation={call.operation}")
        result = tool.execute(call)
        self.audit.record("tool_call_completed", call_id, f"result={result}")
        return result


class FakeERPTool:
    """Test double; production connectors must implement EnterpriseTool."""

    name = "fake_erp"

    def execute(self, call: ToolCall) -> str:
        if call.operation != "release_shipment":
            raise ValueError(f"unsupported fake ERP operation: {call.operation}")
        return f"released:{call.inputs['shipment_id']}"
