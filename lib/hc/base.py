import os

from lib.base import ProfileContext
from lib.base import BaseResourceGenerator as _BaseResourceGenerator


class HealthConnectContext(ProfileContext):
    HCPD_LOCAL_IDENTIFIER_SYSTEM = "http://digitalhealth.gov.au/fhir/hcpd/id/hcpd-local-identifier"
    SMD_TARGET_IDENTIFIER_SYSTEM = "http://ns.electronichealth.net.au/smd/target"
    RESPONSIBLE_PARTY_TYPE_SYSTEM = "http://digitalhealth.gov.au/fhir/cc/CodeSystem/responsible-party-type"
    ENDPOINT_PAYLOAD_TYPE_SYSTEM = "http://hl7.org.au/fhir/pd/CodeSystem/endpoint-payload-type"
    V2_0203_SYSTEM = "http://terminology.hl7.org.au/CodeSystem/v2-0203"
    V2_0203_R4_SYSTEM = "http://terminology.hl7.org/CodeSystem/v2-0203"
    SOURCE_NHSD_SYSTEM = "http://ns.electronichealth.net.au/id/source/nhsd"
    SOURCE_PCA_SYSTEM = "http://ns.electronichealth.net.au/id/source/pca"
    HI_SERVICES_IDENTIFIER_STATUS_SYSTEM = "http://digitalhealth.gov.au/fhir/hcpd/CodeSystem/hi-services-identifier-status-cs"

    IDENTIFIER_TYPE_BY_SYSTEM = {
        "http://ns.electronichealth.net.au/id/hi/hpio/1.0": ("NOI", "HPI-O"),
        "http://hl7.org.au/id/abn": ("ABN", "ABN"),
        "http://hl7.org.au/id/acn": ("ACN", "ACN"),
        "http://ns.electronichealth.net.au/id/hi/hpii/1.0": ("NPI", "HPI-I"),
        "http://hl7.org.au/id/ahpra-registration-number": ("AHPRA", "Ahpra Registration Number"),
        "http://ns.electronichealth.net.au/id/medicare-provider-number": ("UPIN", "Medicare Provider Number"),
    }

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

    def build_source_identifier(self, source_system, source_value):
        return {
            "type": self.build_identifier_type(
                code="RI",
                system=self.V2_0203_R4_SYSTEM,
                text="Resource identifier",
            ),
            "system": source_system,
            "value": source_value,
        }

    def build_hpii_status_extension(self, status_code, status_display=None, status_system=None):
        if not status_code:
            return None
        return {
            "url": "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hi-services-identifier-status",
            "valueCoding": {
                "system": status_system or self.HI_SERVICES_IDENTIFIER_STATUS_SYSTEM,
                "code": status_code,
                "display": status_display,
            },
        }

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

    def default_identifier_type_parts(self, identifier_system, fallback_code=None, fallback_text=None):
        default_code, default_text = self.IDENTIFIER_TYPE_BY_SYSTEM.get(
            identifier_system,
            (fallback_code, fallback_text),
        )
        return default_code, default_text

    def build_identifier_type_for_system(self, identifier_system, code=None, type_system=None, text=None):
        default_code, default_text = self.default_identifier_type_parts(identifier_system)
        resolved_code = code or default_code
        resolved_text = text or default_text
        resolved_system = type_system or self.V2_0203_SYSTEM
        return self.build_identifier_type(code=resolved_code, system=resolved_system, text=resolved_text)

    def build_identifier_type_from_row(self, row, field_prefix, identifier_system=None, fallback_code=None, fallback_text=None):
        type_system, type_code = self.tokenized_system_code(self.csv_first(row, f"{field_prefix}.type"))
        type_system = self.csv_first(row, f"{field_prefix}.type.coding.system") or type_system
        type_code = self.csv_first(row, f"{field_prefix}.type.coding.code") or type_code
        type_text = self.csv_first(row, f"{field_prefix}.type.text")

        if not type_code:
            type_code, default_text = self.default_identifier_type_parts(
                identifier_system,
                fallback_code=fallback_code,
                fallback_text=fallback_text,
            )
            if not type_text:
                type_text = default_text

        if not type_system:
            type_system = self.V2_0203_SYSTEM

        return self.build_identifier_type(code=type_code, system=type_system, text=type_text)


class BaseResourceGenerator(_BaseResourceGenerator):
    def __init__(self, args):
        self.args = args
        self.context = HealthConnectContext(args)
