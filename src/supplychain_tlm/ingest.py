"""Convert extracted JSON fields into SupplyChain-TLM schemas."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Any

from .schemas import BillOfLading, DocumentHeader, Invoice, LineItem, PackingList, PurchaseOrder
from .validation import validate_shipment_bundle


@dataclass(frozen=True)
class ShipmentBundle:
    invoice: Invoice
    purchase_order: PurchaseOrder
    packing_list: PackingList
    bill_of_lading: BillOfLading


def _header(data: dict[str, Any], document_type: str) -> DocumentHeader:
    return DocumentHeader(
        document_id=str(data["document_id"]),
        document_type=document_type,
        supplier=str(data.get("supplier", "")),
        buyer=str(data.get("buyer", "")),
    )


def _lines(data: dict[str, Any]) -> tuple[LineItem, ...]:
    return tuple(
        LineItem(
            sku=str(item["sku"]),
            description=str(item.get("description", "")),
            quantity=float(item.get("quantity", 0.0)),
            unit_price=float(item["unit_price"]) if item.get("unit_price") is not None else None,
        )
        for item in data.get("lines", [])
    )


def document_from_dict(document_type: str, data: dict[str, Any]) -> Invoice | PurchaseOrder | PackingList | BillOfLading:
    """Parse one extracted document object and fail clearly on missing fields."""
    if document_type == "invoice":
        return Invoice(_header(data, document_type), str(data["po_number"]), str(data["currency"]), float(data["total_amount"]), _lines(data))
    if document_type == "purchase_order":
        return PurchaseOrder(_header(data, document_type), str(data["po_number"]), str(data["currency"]), float(data["total_amount"]), _lines(data))
    if document_type == "packing_list":
        return PackingList(_header(data, document_type), str(data["shipment_id"]), _lines(data))
    if document_type == "bill_of_lading":
        return BillOfLading(_header(data, document_type), str(data["shipment_id"]), tuple(map(str, data.get("container_numbers", []))))
    raise ValueError(f"unsupported document type: {document_type}")


def bundle_from_dict(data: dict[str, Any]) -> ShipmentBundle:
    required = ("invoice", "purchase_order", "packing_list", "bill_of_lading")
    missing = [name for name in required if name not in data]
    if missing:
        raise ValueError(f"bundle is missing: {', '.join(missing)}")
    return ShipmentBundle(
        invoice=document_from_dict("invoice", data["invoice"]),
        purchase_order=document_from_dict("purchase_order", data["purchase_order"]),
        packing_list=document_from_dict("packing_list", data["packing_list"]),
        bill_of_lading=document_from_dict("bill_of_lading", data["bill_of_lading"]),
    )


def load_bundle(path: str | Path) -> ShipmentBundle:
    with Path(path).open(encoding="utf-8") as stream:
        return bundle_from_dict(json.load(stream))


def _main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 -m src.supplychain_tlm.ingest BUNDLE.json")
        return 2
    bundle = load_bundle(sys.argv[1])
    report = validate_shipment_bundle(bundle.invoice, bundle.purchase_order, bundle.packing_list, bundle.bill_of_lading)
    print(f"invoice={bundle.invoice.header.document_id} po={bundle.purchase_order.po_number} shipment={bundle.packing_list.shipment_id}")
    print(f"passed: {report.passed}")
    for issue in report.issues:
        print(f"{issue.severity}: {issue.code}: {issue.message}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(_main())
