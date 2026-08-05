"""Vendor-neutral capability interfaces for SAP, Oracle, and WMS systems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class SAPConnector(Protocol):
    def release_shipment(self, shipment_id: str, po_number: str) -> str: ...
    def purchase_order_status(self, po_number: str) -> str: ...


class OracleConnector(Protocol):
    def release_shipment(self, shipment_id: str, po_number: str) -> str: ...
    def purchase_order_status(self, po_number: str) -> str: ...


class WMSConnector(Protocol):
    def reserve_inventory(self, shipment_id: str, sku: str, quantity: float) -> str: ...
    def record_goods_receipt(self, shipment_id: str) -> str: ...


@dataclass
class DryRunEnterpriseConnectors:
    """Safe test implementation shared by vendor-specific integration tests."""

    calls: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)

    def _record(self, operation: str, *args: object) -> str:
        self.calls.append((operation, args))
        return "dry-run:" + operation + ":" + ":".join(str(arg) for arg in args)

    def release_shipment(self, shipment_id: str, po_number: str) -> str:
        return self._record("release_shipment", shipment_id, po_number)

    def purchase_order_status(self, po_number: str) -> str:
        return self._record("purchase_order_status", po_number)

    def reserve_inventory(self, shipment_id: str, sku: str, quantity: float) -> str:
        return self._record("reserve_inventory", shipment_id, sku, quantity)

    def record_goods_receipt(self, shipment_id: str) -> str:
        return self._record("record_goods_receipt", shipment_id)
