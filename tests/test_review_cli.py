import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from src.supplychain_tlm.review_cli import main


class ReviewCLITests(unittest.TestCase):
    def test_enqueue_list_and_resolve(self):
        with TemporaryDirectory() as directory:
            queue_path = str(Path(directory) / "review.jsonl")
            source = Path(directory) / "unreadable.txt"
            source.write_text("unreadable text", encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--queue", queue_path, "enqueue", str(source)]), 0)
            item_id = output.getvalue().split("queued: ", 1)[1].split()[0]
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--queue", queue_path, "list"]), 0)
            self.assertIn(item_id, output.getvalue())
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--queue", queue_path, "resolve", item_id, "analyst-1", "corrected"]), 0)
            self.assertEqual(main(["--queue", queue_path, "list"]), 0)


if __name__ == "__main__":
    unittest.main()
