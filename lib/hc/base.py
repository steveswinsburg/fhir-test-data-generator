import os

from lib.base import ProfileContext
from lib.base import BaseResourceGenerator as _BaseResourceGenerator


class HealthConnectContext(ProfileContext):
    HCPD_LOCAL_IDENTIFIER_SYSTEM = "http://digitalhealth.gov.au/fhir/hcpd/id/hcpd-local-identifier"
    SMD_TARGET_IDENTIFIER_SYSTEM = "http://ns.electronichealth.net.au/smd/target"
    RESPONSIBLE_PARTY_TYPE_SYSTEM = "http://digitalhealth.gov.au/fhir/cc/CodeSystem/responsible-party-type"

    def candidate_input_paths(self, file_name):
        return [
            os.path.join(self.input_dir, file_name),
            os.path.join(self.input_dir, "health-connect-26.0.0", file_name),
        ]

    def normalize_token(self, value):
        text = str(value).strip()
        if text.startswith("#"):
            return text[1:]
        return text

    def token_value(self, row, key):
        return self.normalize_token(self.csv_value(row, key))

    def tokenized_system_code(self, value):
        token = self.normalize_token(value)
        if not token:
            return "", ""
        if "#" in token:
            system, code = token.split("#", 1)
            return system.strip(), code.strip()
        return token, ""

    def bool_value(self, value):
        return self.normalize_token(value).lower() == "true"

    def float_value(self, value):
        text = str(value).strip()
        return float(text) if text else None

    def slugify(self, value):
        normalized = self.normalize_text(value).lower().replace(" ", "")
        return normalized or "healthconnect"

    def bulk_resource_id(self, resource_name, index):
        return f"healthconnect-{resource_name}-{index:07d}"

    def make_time_extension(self, time_value, timezone):
        if not time_value:
            return None, None
        primitive_extension = None
        if timezone:
            primitive_extension = {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/timezone",
                        "valueCode": timezone,
                    }
                ]
            }
        return time_value, primitive_extension

    def healthcare_service_reference(self, index):
        return f"HealthcareService/{self.bulk_resource_id('healthcareservice', index)}"

    def endpoint_reference(self, index):
        return f"Endpoint/{self.bulk_resource_id('endpoint', index)}"

    def infer_reference(self, value, default_resource_type=None, candidate_types=None):
        reference = self.normalize_token(value)
        if not reference:
            return None
        if "/" in reference or reference.startswith("#"):
            return reference

        for resource_type in candidate_types or []:
            normalized = reference.lower()
            resource = resource_type.lower()
            known_prefixes = (
                f"{resource}-",
                f"healthconnect-{resource}-",
                f"example-healthconnect-{resource}-",
            )
            if normalized.startswith(known_prefixes):
                return f"{resource_type}/{reference}"

        if default_resource_type:
            return f"{default_resource_type}/{reference}"
        return reference

    def build_suppressed_extension(self, suppressed_by_code, include_self=None):
        if not suppressed_by_code:
            return None

        extension = {
            "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/suppressed",
            "extension": [
                {
                    "url": "suppressedBy",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": self.RESPONSIBLE_PARTY_TYPE_SYSTEM,
                                "code": suppressed_by_code,
                            }
                        ]
                    },
                }
            ],
        }

        if include_self not in (None, ""):
            extension["extension"].append(
                {
                    "url": "includeSelf",
                    "valueBoolean": self.bool_value(include_self),
                }
            )

        return extension


class BaseResourceGenerator(_BaseResourceGenerator):
    def __init__(self, args):
        self.args = args
        self.context = HealthConnectContext(args)
