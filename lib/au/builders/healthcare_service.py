
from ..base import BaseResourceGenerator


AU_CORE_HEALTHCARE_SERVICE_PROFILE = "http://hl7.org.au/fhir/core/StructureDefinition/au-core-healthcareservice"


class AUCoreHealthcareServiceGenerator(BaseResourceGenerator):
    resource_type = "HealthcareService"
    csv_file = "HealthcareService.csv"

    def build_from_row(self, row):
        ctx = self.context
        healthcare_service = {
            "resourceType": "HealthcareService",
            "id": ctx.resource_id(row),
            "meta": ctx.build_meta(AU_CORE_HEALTHCARE_SERVICE_PROFILE),
            "identifier": self.build_identifiers(row),
            "active": ctx.bool_value(ctx.csv_value(row, "active")) if ctx.csv_value(row, "active") else None,
            "providedBy": ctx.build_reference(resource_type="Organization", reference_id=ctx.csv_value(row, "providedBy_reference_id")),
            "type": [ctx.build_codeable_concept_from_prefix(row, "type", 2)],
            "specialty": [ctx.build_codeable_concept_from_prefix(row, "specialty", 1)],
            "location": [ctx.build_reference(resource_type="Location", reference_id=ctx.csv_value(row, "location_reference_id"))],
            "name": ctx.csv_value(row, "name"),
            "telecom": self.build_telecoms(row),
        }
        return ctx.clean(healthcare_service)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        organization_pool = count if count <= 5 else count // 5
        location_pool = count if count <= 5 else count // 5
        organization_index = ctx.random.randint(1, organization_pool)
        location_index = ctx.random.randint(1, location_pool)
        healthcare_service = {
            "resourceType": "HealthcareService",
            "id": ctx.bulk_resource_id("healthcareservice", index),
            "meta": ctx.build_meta(AU_CORE_HEALTHCARE_SERVICE_PROFILE),
            "active": True,
            "providedBy": {"reference": ctx.organization_reference(organization_index)},
            "type": [{"coding": [{"system": "http://snomed.info/sct", "code": ctx.random.choice(["310000008", "394802001", "288565001"])}]}],
            "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": ctx.random.choice(["394592004", "408443003", "394582007"])}]}],
            "location": [{"reference": ctx.location_reference(location_index)}],
            "name": f"{ctx.normalize_text(ctx.faker.city())} {ctx.random.choice(['Clinic', 'Service', 'Centre'])}",
            "telecom": [
                {"system": "phone", "value": ctx.faker.phone_number(), "use": "work"},
                {"system": "email", "value": f"service-{index}@example.com.au", "use": "work"},
            ],
        }
        return ctx.clean(healthcare_service)

    def build_identifiers(self, row):
        identifiers = []
        for index in (1, 2):
            identifier = self.context.build_identifier_from_prefix(row, f"identifier{index}")
            if identifier:
                identifiers.append(identifier)
        return identifiers

    def build_telecoms(self, row):
        ctx = self.context
        telecoms = []
        for index in (1, 2):
            telecom = ctx.build_telecom(
                system=ctx.csv_value(row, f"telecom{index}_system"),
                value=ctx.csv_value(row, f"telecom{index}_value"),
                use=ctx.csv_value(row, f"telecom{index}_use"),
            )
            if telecom:
                telecoms.append(telecom)
        return telecoms
