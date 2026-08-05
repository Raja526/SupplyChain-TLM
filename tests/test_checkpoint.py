import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.supplychain_tlm.checkpoint import inspect_checkpoint


class CheckpointTests(unittest.TestCase):
    def test_matching_checkpoint_passes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.json").write_text(json.dumps({"model_type": "qwen3_5", "hidden_size": 2048, "num_hidden_layers": 24}), encoding="utf-8")
            (root / "tokenizer.json").write_text("{}", encoding="utf-8")
            report = inspect_checkpoint(root)
            self.assertTrue(report.passed)

    def test_nested_qwen_text_config_passes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.json").write_text(json.dumps({"model_type": "qwen3_5", "text_config": {"hidden_size": 2048, "num_hidden_layers": 24}}), encoding="utf-8")
            (root / "tokenizer.json").write_text("{}", encoding="utf-8")
            self.assertTrue(inspect_checkpoint(root).passed)

    def test_35b_architecture_is_rejected_for_2b_backend(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.json").write_text(json.dumps({"model_type": "qwen3_5", "hidden_size": 4096, "num_hidden_layers": 40}), encoding="utf-8")
            (root / "tokenizer.json").write_text("{}", encoding="utf-8")
            report = inspect_checkpoint(root)
            self.assertFalse(report.passed)
            self.assertTrue(any("hidden_size=4096" in error for error in report.errors))

    def test_missing_files_are_reported(self):
        with TemporaryDirectory() as directory:
            report = inspect_checkpoint(directory)
            self.assertFalse(report.passed)
            self.assertIn("missing config.json", report.errors)


if __name__ == "__main__":
    unittest.main()
