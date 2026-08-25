from ..base import BaseResourceGenerator


HEALTH_CONNECT_PRACTITIONER_ROLE_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-practitionerrole"


class HealthConnectPractitionerRoleGenerator(BaseResourceGenerator):
    resource_type = "PractitionerRole"
    csv_file = "PractitionerRole.data.csv"

    def random_active(self):
        # active is required by profile; mix true/false only.
        return self.context.random.choice([True, True, False])

    def build_from_row(self, row):
        ctx = self.context
        identifiers = [
            ctx.build_source_identifier(
                source_system=ctx.csv_first(row, "identifier.HCSourceIdentifier.system") or ctx.SOURCE_PCA_SYSTEM,
                source_value=ctx.csv_first(row, "identifier.HCSourceIdentifier.value"),
            ),
            {
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "XX", "display": "Organization identifier"}]},
                "system": "http://digitalhealth.gov.au/fhir/hcpd/id/hcpd-local-identifier",
                "value": ctx.csv_value(row, "identifier.HCLocalIdentifier.value"),
            },
            {
                "type": {"coding": [{"system": "http://terminology.hl7.org.au/CodeSystem/v2-0203", "code": "UPIN", "display": "Medicare Provider Number"}]},
                "system": "http://ns.electronichealth.net.au/id/medicare-provider-number",
                "value": ctx.csv_value(row, "identifier.medicareProvider.value"),
            },
            {
                "type": {"coding": [{"system": "http://terminology.hl7.org.au/CodeSystem/v2-0203", "code": "AHPRA"}]},
                "system": "http://hl7.org.au/id/ahpra-registration-number",
                "value": ctx.csv_value(row, "identifier.ahpraregistrationnumber.value"),
            },
        ]

        telecom = []
        for prefix in ("telecom", "telecom2"):
            telecom_value = ctx.csv_value(row, f"{prefix}.value")
            if telecom_value:
                telecom.append(
                    {
                        "system": ctx.token_value(row, f"{prefix}.system"),
                        "value": telecom_value,
                        "use": ctx.token_value(row, f"{prefix}.use"),
                    }
                )

        extensions = []
        if ctx.csv_value(row, "communication.code") and ctx.csv_value(row, "communication.display"):
            extensions.append(
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/practitioner-role-communication",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "urn:ietf:bcp:47",
                                "code": ctx.csv_value(row, "communication.code"),
                                "display": ctx.csv_value(row, "communication.display"),
                            }
                        ]
                    },
                }
            )
        if ctx.csv_value(row, "alternateName.family"):
            extensions.append(
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/alternate-name",
                    "valueHumanName": {
                        "use": ctx.token_value(row, "alternateName.use") or "usual",
                        "family": ctx.csv_value(row, "alternateName.family"),
                        "given": [ctx.csv_value(row, "alternateName.given")] if ctx.csv_value(row, "alternateName.given") else [],
                        "prefix": [ctx.csv_value(row, "alternateName.prefix")] if ctx.csv_value(row, "alternateName.prefix") else [],
                    },
                }
            )

        suppressed_by_code = ctx.csv_value(row, "suppressedBy.code")
        include_self = ctx.csv_value(row, "suppressed.includeSelf")
        suppressed_extension = ctx.build_suppressed_extension(suppressed_by_code, include_self)
        if suppressed_extension:
            extensions.append(suppressed_extension)

        available_time = []
        for index in range(1, 6):
            day = ctx.csv_value(row, f"availableTime{index}.daysOfWeek")
            if not day:
                continue
            start_value, start_extension = ctx.make_time_extension(
                ctx.csv_value(row, f"availableTime{index}.availableStartTime"),
                ctx.csv_value(row, f"availableTime{index}.timeZone"),
            )
            end_value, end_extension = ctx.make_time_extension(
                ctx.csv_value(row, f"availableTime{index}.availableEndTime"),
                ctx.csv_value(row, f"availableTime{index}.timeZone"),
            )
            available_time.append(
                ctx.clean(
                    {
                        "daysOfWeek": [day],
                        "allDay": ctx.csv_value(row, f"availableTime{index}.allDay").lower() == "true",
                        "availableStartTime": start_value,
                        "_availableStartTime": start_extension,
                        "availableEndTime": end_value,
                        "_availableEndTime": end_extension,
                    }
                )
            )

        healthcare_services = []
        for field in ("healthcareService", "healthcareService2"):
            reference = ctx.csv_value(row, field)
            if reference:
                healthcare_services.append({"reference": reference})

        endpoints = []
        for field in ("endpoint.reference", "endpoint2.reference"):
            reference = ctx.csv_value(row, field)
            if reference:
                endpoints.append({"reference": reference})

        practitioner_role = {
            "resourceType": "PractitionerRole",
            "id": ctx.csv_value(row, "resource.id"),
            "meta": ctx.build_meta(HEALTH_CONNECT_PRACTITIONER_ROLE_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "extension": extensions,
            "identifier": identifiers,
            "active": ctx.bool_value(ctx.csv_first(row, "active") or "true"),
            "period": {
                "start": ctx.csv_value(row, "period.start"),
                "end": ctx.csv_value(row, "period.end"),
            },
            "practitioner": {"reference": ctx.csv_value(row, "practitioner.reference")},
            "organization": {"reference": ctx.csv_value(row, "organization.reference")},
            "code": [{"coding": [{"system": "http://snomed.info/sct", "code": ctx.csv_value(row, "code.code"), "display": ctx.csv_value(row, "code.display")}]}],
            "location": [{"reference": ctx.csv_value(row, "location.reference")}],
            "healthcareService": healthcare_services,
            "endpoint": endpoints,
            "telecom": telecom,
            "availableTime": available_time,
        }
        return ctx.clean(practitioner_role)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        practitioner_pool = count if count <= 3 else count // 3
        organization_pool = count if count <= 15 else count // 15
        practitioner_index = ctx.random.randint(1, practitioner_pool)
        organization_index = ctx.random.randint(1, organization_pool)
        location_index = organization_index
        healthcare_service_index = organization_index
        role_gender = ctx.random.choice(["male", "female"])
        role_code = ctx.random.choice(
            [
                ("62247001", "General practice physician"),
                ("309343006", "Physiotherapist"),
                ("224565004", "Registered nurse"),
                ("59944000", "Psychologist"),
            ]
        )
        local_identifier = f"{index:08x}-{ctx.random_digits(4)}-{ctx.random_digits(4)}-{ctx.random_digits(4)}-{ctx.random_digits(12)}"
        reg_number = f"MED{str(practitioner_index).rjust(10, '0')}"
        day_templates = [("mon", "09:00:00", "17:00:00"), ("tue", "09:00:00", "17:00:00"), ("wed", "10:00:00", "16:00:00")]
        role_prefix = ctx.random.choice(["Dr.", "A/Prof.", "Prof."])
        role_given = ctx.faker.first_name_male() if role_gender == "male" else ctx.faker.first_name_female()
        role_family = ctx.faker.last_name()
        active_value = self.random_active()

        available_time = []
        for day, start_time, end_time in day_templates:
            start_value, start_extension = ctx.make_time_extension(start_time, "Australia/Sydney")
            end_value, end_extension = ctx.make_time_extension(end_time, "Australia/Sydney")
            available_time.append(
                {
                    "daysOfWeek": [day],
                    "allDay": False,
                    "availableStartTime": start_value,
                    "_availableStartTime": start_extension,
                    "availableEndTime": end_value,
                    "_availableEndTime": end_extension,
                }
            )

        preferred_name = f"{role_prefix} {role_given} {role_family}"
        practitioner_role = {
            "resourceType": "PractitionerRole",
            "id": ctx.bulk_resource_id("practitionerrole", index),
            "meta": ctx.build_meta(HEALTH_CONNECT_PRACTITIONER_ROLE_PROFILE),
            "extension": [
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/practitioner-role-communication",
                    "valueCodeableConcept": {"coding": [{"system": "urn:ietf:bcp:47", "code": "en", "display": "English"}]},
                },
                {
                    "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/alternate-name",
                    "valueHumanName": {"use": "usual", "text": preferred_name},
                },
            ],
            "identifier": [
                ctx.build_source_identifier(
                    source_system=ctx.SOURCE_PCA_SYSTEM,
                    source_value=f"PR-PCA-{index:06d}",
                ),
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "XX"}]},
                    "system": "http://digitalhealth.gov.au/fhir/hcpd/id/hcpd-local-identifier",
                    "value": local_identifier,
                },
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org.au/CodeSystem/v2-0203", "code": "UPIN"}]},
                    "system": "http://ns.electronichealth.net.au/id/medicare-provider-number",
                    "value": f"{ctx.random_digits(6)}{ctx.random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}",
                },
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org.au/CodeSystem/v2-0203", "code": "AHPRA"}]},
                    "system": "http://hl7.org.au/id/ahpra-registration-number",
                    "value": reg_number,
                },
            ],
            "period": {"start": ctx.faker.date_between(start_date="-4y", end_date="today").isoformat()},
            "practitioner": {"reference": ctx.practitioner_reference(practitioner_index)},
            "organization": {"reference": ctx.organization_reference(organization_index)},
            "code": [{"coding": [{"system": "http://snomed.info/sct", "code": role_code[0], "display": role_code[1]}]}],
            "location": [{"reference": ctx.location_reference(location_index)}],
            "healthcareService": [{"reference": ctx.healthcare_service_reference(healthcare_service_index)}],
            "telecom": [{"system": "phone", "value": ctx.faker.phone_number(), "use": "work"}],
            "availableTime": available_time,
        }
        practitioner_role["active"] = active_value
        return ctx.clean(practitioner_role)
