import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.supplychain_tlm.service import answer_payload, handle_json, release_payload


class ServiceTests(unittest.TestCase):
    bundle = "examples/shipment_bundle.json"

    def test_answer_payload_is_tool_free(self):
        payload = answer_payload(self.bundle, "Can this shipment be released?")
        self.assertEqual(payload["mode"], "deterministic")
        self.assertEqual(payload["suggested_action"], "request_approval")

    def test_release_requires_approval(self):
        with TemporaryDirectory() as directory:
            result = release_payload(self.bundle, audit_path=str(Path(directory) / "audit.jsonl"))
            self.assertEqual(result["mode"], "review_only")

    def test_json_dispatch(self):
        payload = handle_json(json.dumps({"operation": "answer", "bundle": self.bundle, "request": "status"}))
        self.assertEqual(json.loads(payload)["mode"], "deterministic")

    def test_unknown_operation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "operation must be answer or release"):
            handle_json(json.dumps({"operation": "execute"}))


if __name__ == "__main__":
    unittest.main()
