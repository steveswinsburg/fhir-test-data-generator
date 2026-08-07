from ..base import BaseResourceGenerator


HEALTH_CONNECT_LOCATION_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-location"


class HealthConnectLocationGenerator(BaseResourceGenerator):
    resource_type = "Location"
    csv_file = "Location.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        source_system = ctx.csv_first(row, "identifier.HCSourceIdentifier.system") or ctx.SOURCE_PCA_SYSTEM
        source_value = ctx.csv_first(row, "identifier.HCSourceIdentifier.value")
        address = {
            "extension": [
                {
                    "url": ctx.csv_value(row, "address.extension.url"),
                    "valueIdentifier": {
                        "type": ctx.build_identifier_type(
                            text=ctx.csv_first(row, "address.valueIdentifier.type.text", "address.valueIdentifier.type")
                        ),
                        "system": ctx.csv_value(row, "address.valueIdentifier.system"),
                        "value": ctx.csv_value(row, "address.valueIdentifier.value"),
                    },
                }
            ],
            "type": ctx.token_value(row, "address.type"),
            "text": ctx.csv_value(row, "address.text"),
            "line": [value for value in [ctx.csv_value(row, "address.line1"), ctx.csv_value(row, "address.line2")] if value],
            "city": ctx.csv_value(row, "address.city"),
            "state": ctx.csv_value(row, "address.state"),
            "postalCode": ctx.csv_value(row, "address.postalCode"),
            "country": ctx.csv_value(row, "address.country"),
        }

        preferred_postal = {
            "url": ctx.csv_value(row, "extension.url1"),
            "valueAddress": {
                "use": ctx.token_value(row, "extension.valueAddress.use"),
                "type": ctx.token_value(row, "extension.valueAddress.type"),
                "text": ctx.csv_value(row, "address.text"),
                "line": address["line"],
                "city": ctx.csv_value(row, "address.city"),
                "state": ctx.csv_value(row, "address.state"),
                "postalCode": ctx.csv_value(row, "address.postalCode"),
                "country": ctx.csv_value(row, "address.country"),
            },
        }

        location = {
            "resourceType": "Location",
            "id": ctx.csv_value(row, "resource.id"),
            "meta": ctx.build_meta(HEALTH_CONNECT_LOCATION_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "status": "active",
            "identifier": [
                ctx.build_source_identifier(
                    source_system=source_system,
                    source_value=source_value,
                ),
                {
                    "type": ctx.build_identifier_type(
                        code=ctx.csv_value(row, "identifier.type.coding.code"),
                        system=ctx.csv_value(row, "identifier.type.coding.system"),
                        text=ctx.csv_first(row, "identifier.type.text", "identifier.type"),
                    ),
                    "system": ctx.HCPD_LOCAL_IDENTIFIER_SYSTEM,
                    "value": ctx.csv_value(row, "identifier.value"),
                }
            ],
            "name": ctx.csv_value(row, "name"),
            "alias": [ctx.csv_value(row, "alias")] if ctx.csv_value(row, "alias") else [],
            "type": [
                {
                    "coding": [
                        {
                            "system": ctx.csv_value(row, "type.coding.system"),
                            "code": ctx.csv_value(row, "type.coding.code"),
                            "display": ctx.csv_value(row, "type.coding.display"),
                        }
                    ]
                }
            ],
            "address": address,
            "position": {
                "longitude": ctx.float_value(ctx.csv_value(row, "position.longitude")),
                "latitude": ctx.float_value(ctx.csv_value(row, "position.latitude")),
            },
            "managingOrganization": {"reference": ctx.csv_value(row, "managingOrganization")},
            "extension": [preferred_postal],
        }
        return ctx.clean(location)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        organization_pool = count if count <= 10 else count // 10
        organization_index = ctx.random.randint(1, organization_pool)
        location_type = ctx.random.choice(
            [
                ("MOBL", "Mobile Unit"),
                ("HOSP", "Hospital"),
                ("OF", "Office"),
            ]
        )
        location = {
            "resourceType": "Location",
            "id": ctx.bulk_resource_id("location", index),
            "meta": ctx.build_meta(HEALTH_CONNECT_LOCATION_PROFILE),
            "status": "active",
            "identifier": [
                ctx.build_source_identifier(
                    source_system=ctx.SOURCE_PCA_SYSTEM,
                    source_value=f"LOC-PCA-{index:06d}",
                ),
                {
                    "type": ctx.build_identifier_type(code="XX", system="http://terminology.hl7.org/CodeSystem/v2-0203", text="HealthConnect Local Identifier"),
                    "system": ctx.HCPD_LOCAL_IDENTIFIER_SYSTEM,
                    "value": ctx.random_digits(6),
                }
            ],
            "name": f"{ctx.normalize_text(ctx.faker.company())} {location_type[1]}",
            "alias": [ctx.normalize_text(ctx.faker.city())],
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": location_type[0], "display": location_type[1]}]}],
            "address": {
                "type": "physical",
                "line": [ctx.faker.street_address()],
                "city": ctx.faker.city(),
                "state": ctx.faker.state_abbr(),
                "postalCode": ctx.faker.postcode(),
                "country": "AUS",
            },
            "position": {"longitude": round(ctx.random.uniform(113.0, 153.6), 6), "latitude": round(ctx.random.uniform(-43.7, -10.7), 6)},
            "managingOrganization": {"reference": ctx.organization_reference(organization_index)},
        }
        return ctx.clean(location)
