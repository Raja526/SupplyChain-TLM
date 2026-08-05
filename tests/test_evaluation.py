import unittest
import json
from contextlib import redirect_stdout
from io import StringIO

from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.evaluation import content_overlap, evaluate


class EvaluationTests(unittest.TestCase):
    def test_rule_baseline_passes_sample_safety_tasks(self):
        result = evaluate(load_jsonl("examples/training_tasks.jsonl"))
        self.assertEqual(result.passed, 3)
        self.assertEqual(result.accuracy, 1.0)
        self.assertEqual(result.confusion_dict()[("request_approval", "request_approval")], 1)
        self.assertEqual(result.confusion_dict()[("request_document_review", "request_document_review")], 1)
        self.assertEqual(result.confusion_dict()[("refuse_action", "refuse_action")], 1)
        self.assertGreater(result.content_score, 0.0)

    def test_content_overlap_is_bounded(self):
        self.assertEqual(content_overlap("same answer", "same answer"), 1.0)
        self.assertEqual(content_overlap("different", "answer"), 0.0)

    def test_evaluation_json_output(self):
        from src.supplychain_tlm.evaluation import main
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/training_tasks.jsonl", "--json"]), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["accuracy"], 1.0)
        self.assertIn("content_score", payload)
        self.assertEqual(len(payload["confusion"]), 3)

    def test_evaluation_accepts_local_backend(self):
        from src.supplychain_tlm.evaluation import main
        self.assertEqual(main(["examples/training_tasks.jsonl", "--command", "/bin/cat"]), 0)


if __name__ == "__main__":
    unittest.main()
