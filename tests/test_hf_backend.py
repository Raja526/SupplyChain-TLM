import unittest
from pathlib import Path


class HFBackendTests(unittest.TestCase):
    def test_backend_script_exists_and_mentions_local_only(self):
        script = Path("scripts/hf_chat_backend.py").read_text(encoding="utf-8")
        self.assertIn("local_files_only=True", script)
        self.assertIn("max_new_tokens", script)


if __name__ == "__main__":
    unittest.main()
