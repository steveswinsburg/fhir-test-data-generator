import csv
import unittest
from pathlib import Path
from types import SimpleNamespace

from lib.hc.builders.endpoint import HealthConnectEndpointGenerator
from lib.hc.builders.healthcare_service import HealthConnectHealthcareServiceGenerator
from lib.hc.builders.location import HealthConnectLocationGenerator
from lib.hc.builders.organization import HealthConnectOrganizationGenerator
from lib.hc.builders.practitioner import HealthConnectPractitionerGenerator
from lib.hc.builders.practitioner_role import HealthConnectPractitionerRoleGenerator


ROOT = Path(__file__).parent
INPUT = ROOT / "input" / "hcpd-26.0.0"
GENERATORS = (
    (HealthConnectEndpointGenerator, ("identifier.HCSourceIdentifier.value", "identifier.HCEndpointIdentifier.value")),
    (HealthConnectHealthcareServiceGenerator, ("identifier.HCSourceIdentifier.value", "identifier.value")),
    (HealthConnectLocationGenerator, ("identifier.HCSourceIdentifier.value", "identifier.value")),
    (HealthConnectOrganizationGenerator, ("identifier.abn.value",)),
    (HealthConnectPractitionerGenerator, ("identifier.hpii.value",)),
    (HealthConnectPractitionerRoleGenerator, ("identifier.HCSourceIdentifier.value", "identifier.HCLocalIdentifier.value")),
)


def generator_and_row(generator_class):
    args = SimpleNamespace(input_dir=str(INPUT), output_dir="", seed=1)
    generator = generator_class(args)
    with (INPUT / generator.csv_file).open(newline="", encoding="utf-8-sig") as source:
        row = next(csv.DictReader(source))
    return generator, row


class HcpdIdentifierTests(unittest.TestCase):
    def test_existing_rows_have_no_valueless_identifiers(self):
        for generator_class, _ in GENERATORS:
            generator, _ = generator_and_row(generator_class)
            for row in generator.context.csv_rows(generator.csv_file):
                with self.subTest(resource=generator.resource_type, id=row["resource.id"]):
                    result = generator.build_from_row(row)
                    for identifier in result.get("identifier", []):
                        self.assertTrue(identifier.get("value"), identifier.get("system"))

    def test_missing_required_identifiers_are_reported(self):
        for generator_class, fields in GENERATORS:
            for field in fields:
                with self.subTest(resource=generator_class.resource_type, field=field):
                    generator, row = generator_and_row(generator_class)
                    row[field] = " "
                    with self.assertRaisesRegex(ValueError, field.replace(".", r"\.")):
                        generator.build_from_row(row)

    def test_missing_optional_identifiers_are_omitted(self):
        cases = (
            (HealthConnectEndpointGenerator, "identifier.HCSMDTargetIdentifier.value", "http://ns.electronichealth.net.au/smd/target"),
            (HealthConnectOrganizationGenerator, "identifier.hpio.value", "http://ns.electronichealth.net.au/id/hi/hpio/1.0"),
            (HealthConnectOrganizationGenerator, "identifier.acn.value", "http://hl7.org.au/id/acn"),
            (HealthConnectPractitionerRoleGenerator, "identifier.medicareProvider.value", "http://ns.electronichealth.net.au/id/medicare-provider-number"),
            (HealthConnectPractitionerRoleGenerator, "identifier.ahpraregistrationnumber.value", "http://hl7.org.au/id/ahpra-registration-number"),
        )
        for generator_class, field, system in cases:
            with self.subTest(resource=generator_class.resource_type, field=field):
                generator, row = generator_and_row(generator_class)
                self.assertIn(system, [identifier.get("system") for identifier in generator.build_from_row(row)["identifier"]])
                row[field] = ""
                result = generator.build_from_row(row)
                self.assertNotIn(system, [identifier.get("system") for identifier in result["identifier"]])


if __name__ == "__main__":
    unittest.main()
