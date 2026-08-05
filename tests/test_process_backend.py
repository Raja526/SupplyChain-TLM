import sys
import unittest

from src.supplychain_tlm.context import build_decision_context
from src.supplychain_tlm.ingest import load_bundle
from src.supplychain_tlm.process_backend import ProcessTLMBackend, clean_model_output


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

    def test_known_qwen_telemetry_is_removed(self):
        output = "qwen config: 24 layers\nprompt_tokens=20 generated_tokens=271\nAnswer here\ntiming: prompt 1s"
        self.assertEqual(clean_model_output(output), "Answer here")


if __name__ == "__main__":
    unittest.main()
