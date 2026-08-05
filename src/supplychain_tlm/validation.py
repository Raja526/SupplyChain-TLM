"""Deterministic checks for a basic shipment document bundle."""

from __future__ import annotations

from collections import defaultdict
import sys

from .schemas import BillOfLading, Invoice, PackingList, PurchaseOrder, ValidationIssue, ValidationReport


def _issue(code: str, message: str, *evidence: str, severity: str = "error") -> ValidationIssue:
    return ValidationIssue(code, severity, message, tuple(evidence))


def validate_invoice_against_po(invoice: Invoice, purchase_order: PurchaseOrder, *, amount_tolerance: float = 0.01) -> ValidationReport:
    """Compare invoice identity, currency, amount, and line quantities with its PO."""
    issues: list[ValidationIssue] = []
    if invoice.po_number != purchase_order.po_number:
        issues.append(_issue("PO_NUMBER_MISMATCH", "Invoice references a different purchase order.", invoice.po_number, purchase_order.po_number))
    if invoice.currency.upper() != purchase_order.currency.upper():
        issues.append(_issue("CURRENCY_MISMATCH", "Invoice and purchase order use different currencies.", invoice.currency, purchase_order.currency))
    if abs(invoice.total_amount - purchase_order.total_amount) > amount_tolerance:
        issues.append(_issue("TOTAL_MISMATCH", "Invoice total differs from the purchase-order total.", f"invoice={invoice.total_amount}", f"po={purchase_order.total_amount}"))

    po_quantities = {line.sku: line.quantity for line in purchase_order.lines}
    for line in invoice.lines:
        expected = po_quantities.get(line.sku)
        if expected is None:
            issues.append(_issue("UNKNOWN_SKU", f"Invoice line {line.sku!r} is not present on the purchase order.", line.sku))
        elif line.quantity > expected:
            issues.append(_issue("QUANTITY_OVERAGE", f"Invoice quantity for {line.sku!r} exceeds the purchase order.", f"invoice={line.quantity}", f"po={expected}"))
    return ValidationReport(tuple(issues))


def validate_shipment_bundle(invoice: Invoice, purchase_order: PurchaseOrder, packing_list: PackingList, bill_of_lading: BillOfLading) -> ValidationReport:
    """Run cross-document checks needed before a release decision."""
    issues = list(validate_invoice_against_po(invoice, purchase_order).issues)
    if packing_list.shipment_id != bill_of_lading.shipment_id:
        issues.append(_issue("SHIPMENT_ID_MISMATCH", "Packing list and bill of lading refer to different shipments.", packing_list.shipment_id, bill_of_lading.shipment_id))

    po_quantities = defaultdict(float)
    for line in purchase_order.lines:
        po_quantities[line.sku] += line.quantity
    packed_quantities = defaultdict(float)
    for line in packing_list.lines:
        packed_quantities[line.sku] += line.quantity
    for sku, quantity in packed_quantities.items():
        if sku not in po_quantities:
            issues.append(_issue("PACKING_UNKNOWN_SKU", f"Packing list contains SKU {sku!r} absent from the purchase order.", sku))
        elif quantity > po_quantities[sku]:
            issues.append(_issue("PACKING_QUANTITY_OVERAGE", f"Packed quantity for {sku!r} exceeds the purchase order.", f"packed={quantity}", f"po={po_quantities[sku]}"))

    if not bill_of_lading.container_numbers:
        issues.append(_issue("MISSING_CONTAINER", "Bill of lading has no container number."))
    return ValidationReport(tuple(issues))


def _demo() -> int:
    """Run a small example without requiring a model or external service."""
    from .schemas import DocumentHeader, LineItem

    po = PurchaseOrder(DocumentHeader("PO-100", "purchase_order"), "PO-100", "USD", 1000.0, (LineItem("SKU-1", quantity=10),))
    invoice = Invoice(DocumentHeader("INV-9", "invoice"), "PO-100", "USD", 1100.0, (LineItem("SKU-1", quantity=11),))
    packing = PackingList(DocumentHeader("PK-1", "packing_list"), "SHIP-1", (LineItem("SKU-1", quantity=10),))
    bol = BillOfLading(DocumentHeader("BOL-1", "bill_of_lading"), "SHIP-1", ("MSCU1234567",))
    report = validate_shipment_bundle(invoice, po, packing, bol)
    print(f"passed: {report.passed}")
    for issue in report.issues:
        print(f"{issue.severity}: {issue.code}: {issue.message}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(_demo())
