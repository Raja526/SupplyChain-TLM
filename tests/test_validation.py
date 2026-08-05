import unittest

from src.supplychain_tlm.schemas import BillOfLading, DocumentHeader, Invoice, LineItem, PackingList, PurchaseOrder
from src.supplychain_tlm.validation import validate_shipment_bundle


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.po = PurchaseOrder(DocumentHeader("PO-100", "purchase_order"), "PO-100", "USD", 1000.0, (LineItem("SKU-1", quantity=10),))
        self.invoice = Invoice(DocumentHeader("INV-9", "invoice"), "PO-100", "USD", 1000.0, (LineItem("SKU-1", quantity=10),))
        self.packing = PackingList(DocumentHeader("PK-1", "packing_list"), "SHIP-1", (LineItem("SKU-1", quantity=10),))
        self.bol = BillOfLading(DocumentHeader("BOL-1", "bill_of_lading"), "SHIP-1", ("MSCU1234567",))

    def test_matching_bundle_passes(self):
        self.assertTrue(validate_shipment_bundle(self.invoice, self.po, self.packing, self.bol).passed)

    def test_mismatched_invoice_is_blocked(self):
        invoice = Invoice(self.invoice.header, "PO-999", "EUR", 1200.0, self.invoice.lines)
        report = validate_shipment_bundle(invoice, self.po, self.packing, self.bol)
        self.assertFalse(report.passed)
        self.assertEqual({issue.code for issue in report.issues}, {"PO_NUMBER_MISMATCH", "CURRENCY_MISMATCH", "TOTAL_MISMATCH"})

    def test_missing_container_is_blocked(self):
        bol = BillOfLading(self.bol.header, self.bol.shipment_id, ())
        report = validate_shipment_bundle(self.invoice, self.po, self.packing, bol)
        self.assertFalse(report.passed)
        self.assertIn("MISSING_CONTAINER", {issue.code for issue in report.issues})


if __name__ == "__main__":
    unittest.main()
