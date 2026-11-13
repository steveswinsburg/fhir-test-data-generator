import io
import unittest
from unittest.mock import patch

from rich.console import Console

from generate import print_generation_summary


class GenerationSummaryTests(unittest.TestCase):
    def test_seed_only_reported_for_bulk(self):
        for mode in ("csv", "bulk"):
            with self.subTest(mode=mode):
                output = io.StringIO()
                with patch("generate.console", Console(file=output, width=120)):
                    print_generation_summary("hcpd-26.0.0", mode, "output", [], 42, 1, 2)

                text = output.getvalue()
                if mode == "bulk":
                    self.assertIn("Seed: 42", text)
                    self.assertIn("pass --seed 42", text)
                    self.assertIn("Index range: 1 to 2", text)
                else:
                    self.assertNotIn("Seed:", text)
                    self.assertNotIn("--seed", text)


if __name__ == "__main__":
    unittest.main()
