import unittest

from src.supplychain_tlm.knowledge import DEFAULT_KNOWLEDGE, KnowledgeDocument, KnowledgeIndex


class KnowledgeTests(unittest.TestCase):
    def test_retrieves_customs_reference(self):
        results = DEFAULT_KNOWLEDGE.search("Which HS code and tariff checks are needed?")
        self.assertEqual(results[0].document.document_id, "hs-codes")

    def test_results_are_limited_and_ranked(self):
        index = KnowledgeIndex((KnowledgeDocument("a", "Invoice", "invoice currency total"), KnowledgeDocument("b", "Shipping", "shipment container")))
        results = index.search("invoice total", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document.document_id, "a")

    def test_empty_query_has_no_results(self):
        self.assertEqual(DEFAULT_KNOWLEDGE.search(""), ())


if __name__ == "__main__":
    unittest.main()
