from ..base import BaseResourceGenerator


HEALTH_CONNECT_SERVICE_COVERAGE_AREA_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-service-coverage-area"


class HealthConnectCoverageAreaGenerator(BaseResourceGenerator):
    resource_type = "Location"
    csv_file = "CoverageArea.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        coverage_area = {
            "resourceType": "Location",
            "id": ctx.csv_value(row, "resource.id"),
            "meta": ctx.build_meta(HEALTH_CONNECT_SERVICE_COVERAGE_AREA_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "status": ctx.csv_first(row, "status") or "active",
            "name": ctx.csv_value(row, "name"),
            "address": {
                "line": [value for value in [ctx.csv_value(row, "address.line1"), ctx.csv_value(row, "address.line2")] if value],
                "city": ctx.csv_value(row, "address.city"),
                "state": ctx.csv_value(row, "address.state"),
                "postalCode": ctx.csv_value(row, "address.postalCode"),
                "country": ctx.csv_value(row, "address.country") or "AU",
            },
            "managingOrganization": {
                "reference": ctx.csv_value(row, "managingOrganization.reference"),
            },
        }
        return ctx.clean(coverage_area)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        organization_pool = count if count <= 10 else count // 10
        organization_index = ctx.random.randint(1, organization_pool)

        coverage_area = {
            "resourceType": "Location",
            "id": ctx.bulk_resource_id("coveragearea", index),
            "meta": ctx.build_meta(HEALTH_CONNECT_SERVICE_COVERAGE_AREA_PROFILE),
            "status": "active",
            "name": f"Coverage Area {index}",
            "address": {
                "line": [ctx.faker.street_address()],
                "city": ctx.faker.city(),
                "state": ctx.faker.state_abbr(),
                "postalCode": ctx.faker.postcode(),
                "country": "AU",
            },
            "managingOrganization": {
                "reference": ctx.organization_reference(organization_index),
            },
        }
        return ctx.clean(coverage_area)
