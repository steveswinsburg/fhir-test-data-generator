from ..base import BaseResourceGenerator


HEALTH_CONNECT_ENDPOINT_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-endpoint"


class HealthConnectEndpointGenerator(BaseResourceGenerator):
    resource_type = "Endpoint"
    csv_file = "Endpoint.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        payload_mime_types = [ctx.csv_value(row, f"payloadMimeType{index}") for index in range(1, 4)]
        endpoint_type_system, endpoint_type_code = ctx.tokenized_system_code(
            ctx.csv_first(row, "identifier.HCEndpointIdentifier.type")
        )
        endpoint_type_code = ctx.csv_first(row, "identifier.HCEndpointIdentifier.type.code") or endpoint_type_code
        endpoint = {
            "resourceType": "Endpoint",
            "id": ctx.csv_value(row, "resource.id"),
            "meta": ctx.build_meta(HEALTH_CONNECT_ENDPOINT_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "status": ctx.token_value(row, "status"),
            "connectionType": {
                "system": ctx.csv_value(row, "connectionType.system"),
                "code": ctx.csv_value(row, "connectionType.code"),
                "display": ctx.csv_value(row, "connectionType.display"),
            },
            "name": ctx.csv_value(row, "name"),
            "managingOrganization": {"reference": ctx.csv_value(row, "managingOrganization.reference")},
            "period": {
                "start": ctx.csv_value(row, "period.start"),
                "end": ctx.csv_value(row, "period.end"),
            },
            "address": ctx.csv_value(row, "address"),
            "identifier": [
                {
                    "system": ctx.SMD_TARGET_IDENTIFIER_SYSTEM,
                    "value": ctx.csv_value(row, "identifier.HCSMDTargetIdentifier.value"),
                },
                {
                    "type": ctx.build_identifier_type(
                        code=endpoint_type_code,
                        system=endpoint_type_system,
                        text=ctx.csv_first(row, "identifier.HCEndpointIdentifier.type.text"),
                    ),
                    "system": ctx.HCPD_LOCAL_IDENTIFIER_SYSTEM,
                    "value": ctx.csv_value(row, "identifier.HCEndpointIdentifier.value"),
                },
            ],
            "payloadType": [
                {
                    "coding": [
                        {
                            "system": ctx.csv_value(row, "payloadType.system"),
                            "code": ctx.csv_value(row, "payloadType.code"),
                            "display": ctx.csv_value(row, "payloadType.display"),
                        }
                    ]
                }
            ],
            "payloadMimeType": payload_mime_types,
        }
        return ctx.clean(endpoint)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        organization_pool = count if count <= 10 else count // 10
        organization_index = ctx.random.randint(1, organization_pool)
        endpoint = {
            "resourceType": "Endpoint",
            "id": ctx.bulk_resource_id("endpoint", index),
            "meta": ctx.build_meta(HEALTH_CONNECT_ENDPOINT_PROFILE),
            "status": "active",
            "connectionType": {
                "system": "http://terminology.hl7.org.au/CodeSystem/endpoint-connection-type",
                "code": "secure-messaging",
                "display": "Secure Messaging",
            },
            "name": f"HealthConnect Endpoint {index}",
            "managingOrganization": {"reference": ctx.organization_reference(organization_index)},
            "period": {"start": ctx.faker.date_between(start_date="-3y", end_date="today").isoformat()},
            "address": f"https://endpoint{index}.example.com.au/fhir",
            "identifier": [
                {"system": ctx.SMD_TARGET_IDENTIFIER_SYSTEM, "value": f"SMD{index:012d}"},
                {
                    "type": ctx.build_identifier_type(code="RI", system="http://terminology.hl7.org/CodeSystem/v2-0203", text="Resource Identifier"),
                    "system": ctx.HCPD_LOCAL_IDENTIFIER_SYSTEM,
                    "value": f"EP{index:012d}",
                },
            ],
            "payloadType": [{"coding": [{"system": "AustralianEndpointPayloadTypesCodeSystem", "code": "application/fhir+json", "display": "FHIR JSON"}]}],
            "payloadMimeType": ["application/fhir+json"],
        }
        return ctx.clean(endpoint)
