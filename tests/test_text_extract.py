import unittest

from src.supplychain_tlm.text_extract import classify_document, extract_fields


class TextExtractionTests(unittest.TestCase):
    def test_classifies_invoice(self):
        self.assertEqual(classify_document("Commercial Invoice\nInvoice Total: USD 100" )[0], "invoice")

    def test_extracts_common_shipping_fields(self):
        result = extract_fields("Bill of Lading\nShipment ID: SHIP-100\nContainer Number: MSCU1234567")
        self.assertEqual(result.document_type, "bill_of_lading")
        self.assertEqual(result.fields["shipment_id"], "SHIP-100")
        self.assertEqual(result.fields["container_number"], "MSCU1234567")

    def test_unknown_text_returns_warning(self):
        result = extract_fields("random unrelated text")
        self.assertEqual(result.document_type, "unknown")
        self.assertIn("document type could not be classified", result.warnings)


if __name__ == "__main__":
    unittest.main()
