"""Capability adapters over shared shipment facts.

Adapters provide focused context; they are not separate language models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .ingest import ShipmentBundle


@dataclass(frozen=True)
class DomainContext:
    capability: str
    facts: tuple[tuple[str, str], ...]


class DomainAdapter(Protocol):
    capability: str

    def build_context(self, bundle: ShipmentBundle) -> DomainContext:
        """Return normalized facts relevant to one business capability."""


class FinancialAdapter:
    capability = "financial"

    def build_context(self, bundle: ShipmentBundle) -> DomainContext:
        return DomainContext(self.capability, (
            ("po_number", bundle.purchase_order.po_number),
            ("currency", bundle.invoice.currency),
            ("invoice_total", str(bundle.invoice.total_amount)),
            ("po_total", str(bundle.purchase_order.total_amount)),
        ))


class ShippingAdapter:
    capability = "shipping"

    def build_context(self, bundle: ShipmentBundle) -> DomainContext:
        return DomainContext(self.capability, (("shipment_id", bundle.packing_list.shipment_id), ("containers", ",".join(bundle.bill_of_lading.container_numbers)), ("packed_skus", ",".join(line.sku for line in bundle.packing_list.lines))))


class CustomsAdapter:
    capability = "customs"

    def build_context(self, bundle: ShipmentBundle) -> DomainContext:
        return DomainContext(self.capability, (("shipment_id", bundle.packing_list.shipment_id), ("goods_skus", ",".join(line.sku for line in bundle.purchase_order.lines)), ("customs_status", "requires_external_check")))


class WarehouseAdapter:
    capability = "warehouse"

    def build_context(self, bundle: ShipmentBundle) -> DomainContext:
        quantity = sum(line.quantity for line in bundle.packing_list.lines)
        return DomainContext(self.capability, (("shipment_id", bundle.packing_list.shipment_id), ("packed_quantity", str(quantity))))


class ComplianceAdapter:
    capability = "compliance"

    def build_context(self, bundle: ShipmentBundle) -> DomainContext:
        return DomainContext(self.capability, (("shipment_id", bundle.packing_list.shipment_id), ("review_required", "true")))


DEFAULT_ADAPTERS: tuple[DomainAdapter, ...] = (FinancialAdapter(), ShippingAdapter(), CustomsAdapter(), WarehouseAdapter(), ComplianceAdapter())
