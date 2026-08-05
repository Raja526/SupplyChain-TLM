"""Side-effect boundaries for future ERP, messaging, and database tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
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


@dataclass(frozen=True)
class ToolPolicy:
    allowed_tools: frozenset[str]
    allowed_operations: frozenset[str]
    required_approver: str

    def check(self, tool: EnterpriseTool, call: ToolCall, approval: Approval) -> str | None:
        if tool.name not in self.allowed_tools:
            return f"tool is not allowed by policy: {tool.name}"
        if call.operation not in self.allowed_operations:
            return f"operation is not allowed by policy: {call.operation}"
        if approval.approver != self.required_approver:
            return f"approval requires {self.required_approver}"
        return None


class AuditLog:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event_type: str, reference: str, details: str) -> None:
        self.events.append(AuditEvent(event_type, datetime.now(timezone.utc).isoformat(), reference, details))


class JsonlAuditLog(AuditLog):
    """Append-only audit log that remains readable after process restart."""

    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.path = Path(path)

    def record(self, event_type: str, reference: str, details: str) -> None:
        super().record(event_type, reference, details)
        event = self.events[-1]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event.__dict__, sort_keys=True) + "\n")

    def persisted_events(self) -> tuple[AuditEvent, ...]:
        if not self.path.exists():
            return ()
        events = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(AuditEvent(**json.loads(line)))
        return tuple(events)


@dataclass
class ApprovalGate:
    audit: AuditLog = field(default_factory=AuditLog)
    policy: ToolPolicy | None = None
    _completed_keys: set[str] = field(default_factory=set, init=False)

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
        if self.policy is not None:
            policy_error = self.policy.check(tool, call, approval)
            if policy_error:
                self.audit.record("blocked_tool_call", call_id, policy_error)
                raise PermissionError(policy_error)
        if call_id in self._completed_keys:
            self.audit.record("duplicate_tool_call", call_id, f"tool={tool.name} operation={call.operation}")
            raise RuntimeError(f"idempotency key already completed: {call_id}")
        self.audit.record("tool_call_started", call_id, f"tool={tool.name} operation={call.operation}")
        result = tool.execute(call)
        self._completed_keys.add(call_id)
        self.audit.record("tool_call_completed", call_id, f"result={result}")
        return result


class FakeERPTool:
    """Test double; production connectors must implement EnterpriseTool."""

    name = "fake_erp"

    def execute(self, call: ToolCall) -> str:
        if call.operation != "release_shipment":
            raise ValueError(f"unsupported fake ERP operation: {call.operation}")
        return f"released:{call.inputs['shipment_id']}"
