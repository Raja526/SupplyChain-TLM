import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO

from src.supplychain_tlm.answer_cli import main
from src.supplychain_tlm.ingest import load_bundle


class AnswerCLITests(unittest.TestCase):
    def test_answer_cli_prints_reviewable_response(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/shipment_bundle.json", "Can this shipment be released?"]), 0)
        self.assertIn("suggested_action: request_approval", output.getvalue())
        self.assertIn("references: shipment-release", output.getvalue())

    def test_invalid_context_is_explained(self):
        bundle = load_bundle("examples/shipment_bundle.json")
        invalid = replace(bundle, invoice=replace(bundle.invoice, total_amount=1200.0))
        from src.supplychain_tlm.context import build_decision_context
        from src.supplychain_tlm.model import RuleBasedSupplyChainTLM
        response = RuleBasedSupplyChainTLM().answer(build_decision_context("Why blocked?", invalid))
        self.assertEqual(response.suggested_action, "request_document_review")

    def test_cli_can_use_local_process_backend(self):
        output = StringIO()
        command = ["/bin/cat"]
        with redirect_stdout(output):
            self.assertEqual(main(["examples/shipment_bundle.json", "status", "--command", *command, "--timeout", "5"]), 0)
        self.assertIn("answer: You are SupplyChain-TLM", output.getvalue())

    def test_fast_path_skips_local_model(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/shipment_bundle.json", "Can this shipment be released?", "--fast-path", "--command", "/bin/false"]), 0)
        self.assertIn("mode: deterministic", output.getvalue())
        self.assertIn("suggested_action: request_approval", output.getvalue())

    def test_failed_local_model_can_fall_back(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/shipment_bundle.json", "Can this shipment be released?", "--command", "/bin/false", "--fallback-fast-path"]), 0)
        self.assertIn("mode: deterministic_fallback", output.getvalue())
        self.assertIn("suggested_action: request_approval", output.getvalue())


if __name__ == "__main__":
    unittest.main()
