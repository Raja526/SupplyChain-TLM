import sys
import unittest

from src.supplychain_tlm.context import build_decision_context
from src.supplychain_tlm.ingest import load_bundle
from src.supplychain_tlm.process_backend import ProcessTLMBackend


class ProcessBackendTests(unittest.TestCase):
    def test_sends_prompt_to_local_process_and_returns_text(self):
        command = (sys.executable, "-c", "import sys; print('local cpu response')")
        context = build_decision_context("Can this shipment be released?", load_bundle("examples/shipment_bundle.json"))
        response = ProcessTLMBackend(command).answer(context)
        self.assertEqual(response.answer, "local cpu response")
        self.assertEqual(response.references, ("shipment-release",))

    def test_empty_command_is_rejected(self):
        with self.assertRaises(ValueError):
            ProcessTLMBackend(()).answer(build_decision_context("status", load_bundle("examples/shipment_bundle.json")))


if __name__ == "__main__":
    unittest.main()
