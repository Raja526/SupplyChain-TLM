import unittest

from src.supplychain_tlm.erp import DryRunERPClient, ERPToolAdapter
from src.supplychain_tlm.tools import ApprovalGate, ToolCall


class ERPConnectorTests(unittest.TestCase):
    def test_adapter_runs_only_through_approval_gate(self):
        client = DryRunERPClient()
        tool = ERPToolAdapter(client)
        call = ToolCall("erp", "release_shipment", {"shipment_id": "S-1", "po_number": "PO-1"}, "release:S-1")
        gate = ApprovalGate()
        with self.assertRaises(PermissionError):
            gate.execute(tool, call)
        approval = gate.approve("release:S-1", "procurement_manager")
        self.assertEqual(gate.execute(tool, call, approval), "dry-run:release:S-1:PO-1")
        self.assertEqual(client.released, [("S-1", "PO-1")])

    def test_adapter_rejects_incomplete_release(self):
        tool = ERPToolAdapter(DryRunERPClient())
        with self.assertRaises(ValueError):
            tool.execute(ToolCall("erp", "release_shipment", {"shipment_id": "S-1"}, "release:S-1"))


if __name__ == "__main__":
    unittest.main()
