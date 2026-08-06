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
        self.assertFalse(result.needs_human_review)

    def test_unknown_text_returns_warning(self):
        result = extract_fields("random unrelated text")
        self.assertEqual(result.document_type, "unknown")
        self.assertIn("document type could not be classified", result.warnings)
        self.assertTrue(result.needs_human_review)

    def test_low_document_confidence_requires_review(self):
        result = extract_fields("Invoice\nTotal: 100.00")
        self.assertLess(result.confidence, 0.8)
        self.assertTrue(result.needs_human_review)

    def test_invoice_prefers_statement_number_and_total_payable(self):
        result = extract_fields(
            "Jio Bill\nStatement Number : 436512522823\n"
            "Total Payable : 1,060.82\nTotal 899.00"
        )
        self.assertEqual(result.fields["document_id"], "436512522823")
        self.assertEqual(result.fields["total_amount"], "1060.82")

    def test_blank_template_is_reviewed_without_false_document_id(self):
        result = extract_fields("COMMERCIAL INVOICE\nCompany Name\nInvoice Number\nPage X of X")
        self.assertNotIn("document_id", result.fields)
        self.assertIn("document contains template placeholders", result.warnings)
        self.assertTrue(result.needs_human_review)

    def test_packing_list_wins_tie_against_po_terms(self):
        result = extract_fields("PACKING LIST\nPO No: PO-1")
        self.assertEqual(result.document_type, "packing_list")

    def test_synthetic_supplychain_fields(self):
        result = extract_fields(
            "COMMERCIAL INVOICE\nInvoice Number: INV-100\nPO Number: PO-100\n"
            "SKU: SKU-1\nQuantity: 10\nTotal Payable: 1000.00"
        )
        self.assertEqual(result.document_type, "invoice")
        self.assertEqual(result.fields["po_number"], "PO-100")
        self.assertEqual(result.fields["sku"], "SKU-1")
        self.assertEqual(result.fields["quantity"], "10")
        self.assertFalse(result.needs_human_review)


if __name__ == "__main__":
    unittest.main()
