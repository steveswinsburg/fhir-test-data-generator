import csv
import unittest
from types import SimpleNamespace

from lib.hc.builders.practitioner import HealthConnectPractitionerGenerator


class PractitionerCsvTests(unittest.TestCase):
    def setUp(self):
        args = SimpleNamespace(
            input_dir="input/hcpd-26.0.0", output_dir="output/hcpd-26.0.0/csv", seed=1
        )
        self.generator = HealthConnectPractitionerGenerator(args)
        with open("input/hcpd-26.0.0/Practitioner.data.csv", newline="") as source:
            self.row = next(csv.DictReader(source))

    def test_explicit_active_state_is_preserved(self):
        for value, expected in (("true", True), ("false", False)):
            with self.subTest(value=value):
                self.row["active"] = value
                result = self.generator.build_from_row(self.row)
                self.assertIs(result["active"], expected)

    def test_unspecified_active_state_remains_omitted(self):
        self.row.pop("active", None)
        self.assertNotIn("active", self.generator.build_from_row(self.row))
        self.row["active"] = ""
        self.assertNotIn("active", self.generator.build_from_row(self.row))


if __name__ == "__main__":
    unittest.main()
