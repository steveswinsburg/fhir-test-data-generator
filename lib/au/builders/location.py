
from ..base import BaseResourceGenerator


AU_CORE_LOCATION_PROFILE = "http://hl7.org.au/fhir/core/StructureDefinition/au-core-location"


class AUCoreLocationGenerator(BaseResourceGenerator):
    resource_type = "Location"
    csv_file = "Location.csv"

    def build_from_row(self, row):
        ctx = self.context
        location = {
            "resourceType": "Location",
            "id": ctx.resource_id(row),
            "meta": ctx.build_meta(AU_CORE_LOCATION_PROFILE),
            "identifier": self.build_identifiers(row),
            "status": ctx.csv_value(row, "status"),
            "name": ctx.csv_value(row, "name"),
            "alias": [ctx.csv_value(row, "alias1")] if ctx.csv_value(row, "alias1") else [],
            "description": ctx.csv_value(row, "description"),
            "mode": ctx.csv_value(row, "mode"),
            "type": self.build_types(row),
            "telecom": self.build_telecom(row),
            "address": self.build_address(row),
            "physicalType": self.build_physical_type(row),
            "managingOrganization": {"reference": ctx.prefixed_reference("Organization", ctx.csv_value(row, "managingOrganization_reference_id"))},
            "partOf": {"reference": ctx.prefixed_reference("Location", ctx.csv_value(row, "partOf_reference_id"))},
        }
        return ctx.clean(location)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        organization_pool = count if count <= 5 else count // 5
        organization_index = ctx.random.randint(1, organization_pool)
        location = {
            "resourceType": "Location",
            "id": ctx.bulk_resource_id("location", index),
            "meta": ctx.build_meta(AU_CORE_LOCATION_PROFILE),
            "status": "active",
            "name": f"{ctx.normalize_text(ctx.faker.city())} {ctx.random.choice(['Clinic', 'Ward', 'Hospital'])}",
            "mode": "instance",
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": ctx.random.choice(['HOSP', 'FMC', 'PHARM'])}]}],
            "address": {"line": [ctx.faker.street_address()], "city": ctx.faker.city(), "state": ctx.faker.state_abbr(), "postalCode": ctx.faker.postcode(), "country": "AU"},
            "physicalType": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": ctx.random.choice(['si', 'bu', 'wi'])}]},
            "managingOrganization": {"reference": ctx.organization_reference(organization_index)},
        }
        return ctx.clean(location)

    def build_identifiers(self, row):
        ctx = self.context
        system = ctx.csv_value(row, "identifier1_system")
        value = ctx.csv_value(row, "identifier1_value")
        if not any([system, value, ctx.csv_value(row, "identifier1_type_text")]):
            return []
        return [{"type": ctx.build_identifier_type(code=ctx.csv_value(row, "identifier1_type_code"), system=ctx.csv_value(row, "identifier1_type_system"), display=ctx.csv_value(row, "identifier1_type_display"), text=ctx.csv_value(row, "identifier1_type_text")), "system": system, "value": value}]

    def build_types(self, row):
        ctx = self.context
        codings = []
        for index in (1, 2):
            coding = ctx.build_coding(
                ctx.csv_value(row, f"type1_coding{index}_system"),
                ctx.csv_value(row, f"type1_coding{index}_code"),
                ctx.csv_value(row, f"type1_coding{index}_display"),
            )
            if coding:
                codings.append(coding)
        return [{"coding": codings}] if codings else []

    def build_telecom(self, row):
        ctx = self.context
        value = ctx.csv_value(row, "telecom1_value")
        if not value:
            return []
        return [{"system": ctx.csv_value(row, "telecom1_system"), "use": ctx.csv_value(row, "telecom1_use"), "value": value}]

    def build_address(self, row):
        ctx = self.context
        line = [value for value in [ctx.csv_value(row, "address1_line1"), ctx.csv_value(row, "address1_line2")] if value]
        city = ctx.csv_value(row, "address1_city")
        state = ctx.csv_value(row, "address1_state")
        if not any([line, city, state, ctx.csv_value(row, "address1_text")]):
            return None
        return {"text": ctx.csv_value(row, "address1_text"), "line": line, "city": city, "state": state, "postalCode": ctx.csv_value(row, "address1_postalCode"), "country": ctx.csv_value(row, "address1_country")}

    def build_physical_type(self, row):
        ctx = self.context
        coding = ctx.build_coding(
            ctx.csv_value(row, "physicalType_coding1_system"),
            ctx.csv_value(row, "physicalType_coding1_code"),
            ctx.csv_value(row, "physicalType_coding1_display"),
        )
        return {"coding": [coding]} if coding else None
