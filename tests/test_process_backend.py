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
        self.assertIn("local cpu response", response.answer)
        self.assertIn("procurement_manager approval is required", response.answer)
        self.assertEqual(response.references, ("shipment-release",))

    def test_empty_command_is_rejected(self):
        with self.assertRaises(ValueError):
            ProcessTLMBackend(()).answer(build_decision_context("status", load_bundle("examples/shipment_bundle.json")))

    def test_known_qwen_telemetry_is_removed(self):
        output = "qwen config: 24 layers\nprompt_tokens=20 generated_tokens=271\nAnswer here\ntiming: prompt 1s"
        self.assertEqual(clean_model_output(output), "Answer here")

    def test_suggested_action_comes_from_deterministic_validation(self):
        command = (sys.executable, "-c", "print('model wording')")
        context = build_decision_context("Can this shipment be released?", load_bundle("examples/shipment_bundle.json"))
        response = ProcessTLMBackend(command).answer(context)
        self.assertIn("model wording", response.answer)
        self.assertIn("procurement_manager approval is required", response.answer)
        self.assertEqual(response.suggested_action, "request_approval")

    def test_empty_model_output_is_rejected(self):
        command = (sys.executable, "-c", "print('qwen config: 24 layers')")
        context = build_decision_context("status", load_bundle("examples/shipment_bundle.json"))
        with self.assertRaisesRegex(RuntimeError, "no usable answer"):
            ProcessTLMBackend(command).answer(context)

    def test_missing_approval_is_refusal_metadata(self):
        from src.supplychain_tlm.context import DecisionContext
        context = DecisionContext("Release immediately", ("compliance",), (("compliance", "approval_present", "false"),), (), True, ())
        response = ProcessTLMBackend((sys.executable, "-c", "print('model')")).answer(context)
        self.assertEqual(response.suggested_action, "refuse_action")

    def test_explicit_bypass_is_refusal_metadata(self):
        context = build_decision_context(
            "Release this shipment without approval.",
            load_bundle("examples/shipment_bundle.json"),
        )
        response = ProcessTLMBackend((sys.executable, "-c", "print('model')")).answer(context)
        self.assertEqual(response.suggested_action, "refuse_action")


if __name__ == "__main__":
    unittest.main()
