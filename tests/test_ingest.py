import unittest

from src.supplychain_tlm.ingest import bundle_from_dict
from src.supplychain_tlm.validation import validate_shipment_bundle


class IngestTests(unittest.TestCase):
    def test_extracted_dict_becomes_valid_bundle(self):
        bundle = bundle_from_dict({
            "invoice": {"document_id": "INV-1", "po_number": "PO-1", "currency": "USD", "total_amount": 10, "lines": [{"sku": "A", "quantity": 1}]},
            "purchase_order": {"document_id": "PO-1", "po_number": "PO-1", "currency": "USD", "total_amount": 10, "lines": [{"sku": "A", "quantity": 1}]},
            "packing_list": {"document_id": "PK-1", "shipment_id": "S-1", "lines": [{"sku": "A", "quantity": 1}]},
            "bill_of_lading": {"document_id": "B-1", "shipment_id": "S-1", "container_numbers": ["CONT-1"]},
        })
        report = validate_shipment_bundle(bundle.invoice, bundle.purchase_order, bundle.packing_list, bundle.bill_of_lading)
        self.assertTrue(report.passed)
        self.assertEqual(bundle.invoice.lines[0].sku, "A")

    def test_missing_document_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "bundle is missing: bill_of_lading"):
            bundle_from_dict({"invoice": {}, "purchase_order": {}, "packing_list": {}})


if __name__ == "__main__":
    unittest.main()
