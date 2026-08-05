"""ERP connector boundary used behind the approval gate.

The client protocol is intentionally small. Real SAP, Oracle, or warehouse
connectors can implement it without exposing credentials or transport details
to the planner or language model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .tools import ToolCall


class ERPClient(Protocol):
    def release_shipment(self, shipment_id: str, po_number: str) -> str:
        """Release one shipment in the external ERP."""


@dataclass
class DryRunERPClient:
    """Safe local connector for integration tests and demonstrations."""

    released: list[tuple[str, str]] = field(default_factory=list)

    def release_shipment(self, shipment_id: str, po_number: str) -> str:
        record = (shipment_id, po_number)
        if record not in self.released:
            self.released.append(record)
        return f"dry-run:release:{shipment_id}:{po_number}"


@dataclass(frozen=True)
class ERPToolAdapter:
    """Translate an approval-gated ToolCall into an ERP client operation."""

    client: ERPClient
    name: str = "erp"

    def execute(self, call: ToolCall) -> str:
        if call.operation != "release_shipment":
            raise ValueError(f"unsupported ERP operation: {call.operation}")
        shipment_id = call.inputs.get("shipment_id")
        po_number = call.inputs.get("po_number")
        if not shipment_id or not po_number:
            raise ValueError("release_shipment requires shipment_id and po_number")
        return self.client.release_shipment(str(shipment_id), str(po_number))
