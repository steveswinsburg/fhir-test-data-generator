from ..base import BaseResourceGenerator


HEALTH_CONNECT_HEALTHCARE_SERVICE_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-healthcareservice"


class HealthConnectHealthcareServiceGenerator(BaseResourceGenerator):
    resource_type = "HealthcareService"
    csv_file = "HealthcareService.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        start_value, start_extension = ctx.make_time_extension(ctx.csv_value(row, "availableStartTime"), ctx.csv_value(row, "timeZone"))
        end_value, end_extension = ctx.make_time_extension(ctx.csv_value(row, "availableEndTime"), ctx.csv_value(row, "timeZone"))
        healthcare_service = {
            "resourceType": "HealthcareService",
            "id": ctx.csv_value(row, "resource.id"),
            "meta": ctx.build_meta(HEALTH_CONNECT_HEALTHCARE_SERVICE_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "extension": [
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/active-period",
                    "valuePeriod": {
                        "start": ctx.csv_value(row, "activePeriod.start"),
                        "end": ctx.csv_value(row, "activePeriod.end"),
                    },
                },
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/referral-information-for-referrer",
                    "valueMarkdown": ctx.csv_value(row, "referralInformation"),
                },
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/iar-levels-of-care",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": ctx.csv_value(row, "iarLevel.system"),
                                "code": ctx.csv_value(row, "iarLevel.code"),
                                "display": ctx.csv_value(row, "iarLevel.display"),
                            }
                        ]
                    },
                },
            ],
            "identifier": [{"system": ctx.HCPD_LOCAL_IDENTIFIER_SYSTEM, "value": ctx.csv_value(row, "identifier.value")}],
            "providedBy": {"reference": ctx.csv_value(row, "providedBy.reference")},
            "type": [{"coding": [{"system": ctx.csv_value(row, "type.system"), "code": ctx.csv_value(row, "type.code"), "display": ctx.csv_value(row, "type.display")}]}],
            "location": [{"reference": ctx.csv_value(row, "location.reference")}],
            "name": ctx.csv_value(row, "name"),
            "appointmentRequired": ctx.bool_value(ctx.csv_value(row, "appointmentRequired")),
            "coverageArea": [{"reference": ctx.csv_value(row, "coverageArea.reference")}],
            "endpoint": [{"reference": ctx.csv_value(row, "endpoint.reference")}],
            "availableTime": [
                {
                    "daysOfWeek": [ctx.csv_value(row, f"daysOfWeek{index}") for index in range(1, 6)],
                    "allDay": ctx.bool_value(ctx.csv_value(row, "allDay")),
                    "availableStartTime": start_value,
                    "_availableStartTime": start_extension,
                    "availableEndTime": end_value,
                    "_availableEndTime": end_extension,
                }
            ],
        }
        return ctx.clean(healthcare_service)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        organization_pool = count if count <= 10 else count // 10
        location_pool = count if count <= 5 else count // 5
        endpoint_pool = count if count <= 5 else count // 5
        organization_index = ctx.random.randint(1, organization_pool)
        location_index = ctx.random.randint(1, location_pool)
        endpoint_index = ctx.random.randint(1, endpoint_pool)
        service_type = ctx.random.choice(
            [
                ("1584801000168109", "Geriatric evaluation and management service"),
                ("288565001", "Physiotherapy service"),
                ("394814009", "General medical service"),
            ]
        )
        start_value, start_extension = ctx.make_time_extension("08:00:00", "Australia/Sydney")
        end_value, end_extension = ctx.make_time_extension("17:00:00", "Australia/Sydney")
        healthcare_service = {
            "resourceType": "HealthcareService",
            "id": ctx.bulk_resource_id("healthcareservice", index),
            "meta": ctx.build_meta(HEALTH_CONNECT_HEALTHCARE_SERVICE_PROFILE),
            "extension": [
                {"url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/active-period", "valuePeriod": {"start": ctx.faker.date_between(start_date="-3y", end_date="today").isoformat()}},
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/iar-levels-of-care",
                    "valueCodeableConcept": {"coding": [{"system": "http://ns.electronichealth.net.au/hc/CodeSystem/iar-levels-of-care", "code": "3", "display": "Level 3 (moderate intensity interventions)"}]},
                },
            ],
            "identifier": [{"system": ctx.HCPD_LOCAL_IDENTIFIER_SYSTEM, "value": f"HS{index:012d}"}],
            "providedBy": {"reference": ctx.organization_reference(organization_index)},
            "type": [{"coding": [{"system": "http://snomed.info/sct", "code": service_type[0], "display": service_type[1]}]}],
            "location": [{"reference": ctx.location_reference(location_index)}],
            "name": f"HealthConnect Service {index}",
            "appointmentRequired": ctx.random.choice([True, False]),
            "coverageArea": [{"reference": ctx.location_reference(location_index)}],
            "endpoint": [{"reference": ctx.endpoint_reference(endpoint_index)}],
            "availableTime": [{"daysOfWeek": ["mon", "tue", "wed", "thu", "fri"], "allDay": False, "availableStartTime": start_value, "_availableStartTime": start_extension, "availableEndTime": end_value, "_availableEndTime": end_extension}],
        }
        return ctx.clean(healthcare_service)
