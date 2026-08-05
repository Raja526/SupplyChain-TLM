import unittest

from src.supplychain_tlm.ingest import bundle_from_dict
from src.supplychain_tlm.planner import propose_shipment_release


def bundle(total=10):
    return bundle_from_dict({
        "invoice": {"document_id": "INV-1", "po_number": "PO-1", "currency": "USD", "total_amount": total, "lines": [{"sku": "A", "quantity": 1}]},
        "purchase_order": {"document_id": "PO-1", "po_number": "PO-1", "currency": "USD", "total_amount": 10, "lines": [{"sku": "A", "quantity": 1}]},
        "packing_list": {"document_id": "PK-1", "shipment_id": "S-1", "lines": [{"sku": "A", "quantity": 1}]},
        "bill_of_lading": {"document_id": "B-1", "shipment_id": "S-1", "container_numbers": ["CONT-1"]},
    })


class PlannerTests(unittest.TestCase):
    def test_valid_bundle_creates_approval_gated_proposal(self):
        plan = propose_shipment_release(bundle())
        self.assertTrue(plan.validation_passed)
        self.assertEqual(plan.proposals[0].status, "proposed")
        self.assertEqual(plan.proposals[0].required_approval, "procurement_manager")
        self.assertIn("shipment-release", plan.references)

    def test_invalid_bundle_is_blocked(self):
        plan = propose_shipment_release(bundle(total=11))
        self.assertFalse(plan.validation_passed)
        self.assertEqual(plan.proposals[0].status, "blocked")
        self.assertIn("TOTAL_MISMATCH", plan.proposals[0].reason)


if __name__ == "__main__":
    unittest.main()
