import unittest

from src.supplychain_tlm.domains import CustomsAdapter, FinancialAdapter, ShippingAdapter
from src.supplychain_tlm.ingest import load_bundle


class DomainAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle("examples/shipment_bundle.json")

    def test_financial_adapter_exposes_shared_totals(self):
        facts = dict(FinancialAdapter().build_context(self.bundle).facts)
        self.assertEqual(facts["currency"], "USD")
        self.assertEqual(facts["invoice_total"], "1000.0")

    def test_shipping_adapter_exposes_container(self):
        facts = dict(ShippingAdapter().build_context(self.bundle).facts)
        self.assertEqual(facts["shipment_id"], "SHIP-100")
        self.assertEqual(facts["containers"], "MSCU1234567")

    def test_customs_adapter_does_not_claim_clearance(self):
        facts = dict(CustomsAdapter().build_context(self.bundle).facts)
        self.assertEqual(facts["customs_status"], "requires_external_check")


if __name__ == "__main__":
    unittest.main()
