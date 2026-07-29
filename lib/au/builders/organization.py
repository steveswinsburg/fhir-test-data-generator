from ..base import BaseResourceGenerator


AU_CORE_ORGANIZATION_PROFILE = "http://hl7.org.au/fhir/core/StructureDefinition/au-core-organization"


class AUCoreOrganizationGenerator(BaseResourceGenerator):
    resource_type = "Organization"
    csv_file = "Organization.csv"

    def build_from_row(self, row):
        ctx = self.context
        organization = {
            "resourceType": "Organization",
            "id": ctx.resource_id(row),
            "meta": ctx.build_meta(AU_CORE_ORGANIZATION_PROFILE),
            "identifier": self.build_identifiers(row),
            "active": ctx.bool_value(ctx.csv_value(row, "active")) if ctx.csv_value(row, "active") else None,
            "type": self.build_types(row),
            "name": ctx.csv_value(row, "name"),
            "alias": [ctx.csv_value(row, "alias1")] if ctx.csv_value(row, "alias1") else [],
            "telecom": self.build_telecom(row),
            "address": self.build_addresses(row),
            "partOf": {"reference": ctx.prefixed_reference(ctx.csv_value(row, "partOf_reference_type") or "Organization", ctx.csv_value(row, "partOf_reference_id"))},
        }
        return ctx.clean(organization)

    def build_bulk(self, index):
        ctx = self.context
        org_name = f"{ctx.normalize_text(ctx.faker.company())} {ctx.random.choice(['Clinic', 'Hospital', 'Health'])}".strip()
        organization = {
            "resourceType": "Organization",
            "id": ctx.bulk_resource_id("organization", index),
            "meta": ctx.build_meta(AU_CORE_ORGANIZATION_PROFILE),
            "identifier": [
                {
                    "type": ctx.build_identifier_type(code="NOI", system="http://terminology.hl7.org/CodeSystem/v2-0203", text="HPI-O"),
                    "system": "http://ns.electronichealth.net.au/id/hi/hpio/1.0",
                    "value": f"800362{ctx.random_digits(10)}",
                },
                {
                    "type": ctx.build_identifier_type(code="XX", system="http://terminology.hl7.org/CodeSystem/v2-0203", text="ABN"),
                    "system": "http://hl7.org.au/id/abn",
                    "value": ctx.random_digits(11),
                },
            ],
            "active": True,
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://www.abs.gov.au/ausstats/abs@.nsf/mf/1292.0",
                            "code": ctx.random.choice(["8401", "8512", "8539"]),
                        }
                    ]
                }
            ],
            "name": org_name,
            "telecom": [
                {"system": "phone", "use": "work", "value": ctx.faker.phone_number()},
                {"system": "email", "use": "work", "value": f"contact-{index}@example.com.au"},
            ],
            "address": [{"line": [ctx.faker.street_address()], "city": ctx.faker.city(), "state": ctx.faker.state_abbr(), "postalCode": ctx.faker.postcode(), "country": "AU"}],
        }
        return ctx.clean(organization)

    def build_identifiers(self, row):
        ctx = self.context
        identifiers = []
        for index in (1, 2):
            system = ctx.csv_value(row, f"identifier{index}_system")
            value = ctx.csv_value(row, f"identifier{index}_value")
            identifier_type = ctx.build_identifier_type(
                code=ctx.csv_value(row, f"identifier{index}_type_code"),
                system=ctx.csv_value(row, f"identifier{index}_type_system"),
                display=ctx.csv_value(row, f"identifier{index}_type_display"),
                text=ctx.csv_value(row, f"identifier{index}_type_text"),
            )
            if not any([system, value, identifier_type]):
                continue
            identifiers.append({"type": identifier_type, "system": system, "value": value})
        return identifiers

    def build_types(self, row):
        ctx = self.context
        codings = []
        for index in (1, 2):
            coding = ctx.build_coding(
                ctx.csv_value(row, f"type_coding{index}_system"),
                ctx.csv_value(row, f"type_coding{index}_code"),
                ctx.csv_value(row, f"type_coding{index}_display"),
            )
            if coding:
                codings.append(coding)
        if not codings and not ctx.csv_value(row, "type_text"):
            return []
        return [{"coding": codings, "text": ctx.csv_value(row, "type_text")}]

    def build_telecom(self, row):
        ctx = self.context
        telecom = []
        for index in (1, 2):
            value = ctx.csv_value(row, f"telecom{index}_value")
            if not value:
                continue
            telecom.append({"system": ctx.csv_value(row, f"telecom{index}_system"), "use": ctx.csv_value(row, f"telecom{index}_use"), "value": value})
        return telecom

    def build_addresses(self, row):
        ctx = self.context
        line1 = ctx.csv_value(row, "address1_line1")
        city = ctx.csv_value(row, "address1_city")
        state = ctx.csv_value(row, "address1_state")
        if not any([line1, city, state, ctx.csv_value(row, "address1_text")]):
            return []
        return [{"type": ctx.csv_value(row, "address1_type"), "line": [line1] if line1 else [], "city": city, "state": state, "postalCode": ctx.csv_value(row, "address1_postalCode"), "country": ctx.csv_value(row, "address1_country"), "text": ctx.csv_value(row, "address1_text")}]
