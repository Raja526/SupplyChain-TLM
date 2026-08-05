import unittest

from src.supplychain_tlm.connectors import DryRunEnterpriseConnectors


class ConnectorTests(unittest.TestCase):
    def test_dry_run_supports_erp_and_warehouse_capabilities(self):
        connectors = DryRunEnterpriseConnectors()
        self.assertEqual(connectors.release_shipment("S-1", "PO-1"), "dry-run:release_shipment:S-1:PO-1")
        self.assertEqual(connectors.purchase_order_status("PO-1"), "dry-run:purchase_order_status:PO-1")
        self.assertEqual(connectors.reserve_inventory("S-1", "SKU-1", 10), "dry-run:reserve_inventory:S-1:SKU-1:10")
        self.assertEqual(connectors.record_goods_receipt("S-1"), "dry-run:record_goods_receipt:S-1")
        self.assertEqual(len(connectors.calls), 4)


if __name__ == "__main__":
    unittest.main()
