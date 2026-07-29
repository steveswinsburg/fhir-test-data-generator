
from ..base import BaseResourceGenerator


AU_CORE_PRACTITIONER_ROLE_PROFILE = "http://hl7.org.au/fhir/core/StructureDefinition/au-core-practitionerrole"


class AUCorePractitionerRoleGenerator(BaseResourceGenerator):
    resource_type = "PractitionerRole"
    csv_file = "PractitionerRole.csv"

    def build_from_row(self, row):
        ctx = self.context
        practitioner_role = {
            "resourceType": "PractitionerRole",
            "id": ctx.resource_id(row),
            "meta": ctx.build_meta(AU_CORE_PRACTITIONER_ROLE_PROFILE),
            "identifier": self.build_identifiers(row),
            "active": ctx.bool_value(ctx.csv_value(row, "active")) if ctx.csv_value(row, "active") else None,
            "period": {"start": ctx.csv_value(row, "period_start"), "end": ctx.csv_value(row, "period_end")},
            "practitioner": self.build_reference(row, "Practitioner", "practitioner_reference_id", "practitioner_display"),
            "organization": self.build_organization_reference(row),
            "code": self.build_codeable_list(row, "code1", 3),
            "specialty": self.build_codeable_list(row, "specialty1", 2),
            "location": [self.build_plain_reference(row, "Location", "location_reference", "location_reference_id", "location_display")],
            "healthcareService": [self.build_plain_reference(row, None, "healthcareService_reference", None, None)],
            "telecom": self.build_telecom(row),
            "availableTime": self.build_available_times(row),
            "notAvailable": self.build_not_available(row),
            "availabilityExceptions": ctx.csv_value(row, "availabilityExceptions"),
        }
        return ctx.clean(practitioner_role)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        practitioner_pool = count if count <= 3 else count // 3
        organization_pool = count if count <= 4 else count // 4
        practitioner_index = ctx.random.randint(1, practitioner_pool)
        organization_index = ctx.random.randint(1, organization_pool)
        practitioner_role = {
            "resourceType": "PractitionerRole",
            "id": ctx.bulk_resource_id("practitionerrole", index),
            "meta": ctx.build_meta(AU_CORE_PRACTITIONER_ROLE_PROFILE),
            "identifier": [{"type": ctx.build_identifier_type(code="UPIN", system="http://terminology.hl7.org.au/CodeSystem/v2-0203", text="Medicare Provider Number"), "system": "http://ns.electronichealth.net.au/id/medicare-provider-number", "value": f"{ctx.random_digits(6)}{ctx.random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"}],
            "active": True,
            "period": {"start": ctx.faker.date_between(start_date="-4y", end_date="today").isoformat()},
            "practitioner": {"reference": ctx.practitioner_reference(practitioner_index)},
            "organization": {"reference": ctx.organization_reference(organization_index)},
            "code": [{"coding": [{"system": "http://snomed.info/sct", "code": ctx.random.choice(["62247001", "224535009", "309343006"])}]}],
            "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": ctx.random.choice(["394814009", "722165004", "394603008"])}]}],
            "location": [{"reference": ctx.location_reference(organization_index)}],
            "telecom": [{"system": "phone", "use": "work", "value": ctx.faker.phone_number()}],
            "availableTime": [{"daysOfWeek": ["mon", "tue", "wed"], "availableStartTime": "09:00:00", "availableEndTime": "17:00:00"}],
        }
        return ctx.clean(practitioner_role)

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
            identifier = {
                "type": identifier_type,
                "system": system,
                "value": value,
                "assigner": {"display": ctx.csv_value(row, f"identifier{index}_assigner_display")},
            }
            if ctx.csv_value(row, f"identifier{index}_dataAbsentReason"):
                identifier["extension"] = [ctx.data_absent_reason(ctx.csv_value(row, f"identifier{index}_dataAbsentReason"))["extension"][0]]
            identifiers.append(identifier)
        return identifiers

    def build_reference(self, row, resource_type, id_key, display_key):
        ctx = self.context
        reference_id = ctx.csv_value(row, id_key)
        display = ctx.csv_value(row, display_key)
        if not reference_id and not display:
            return None
        payload = {"reference": ctx.prefixed_reference(resource_type, reference_id), "display": display}
        if not reference_id and display:
            payload["extension"] = [ctx.data_absent_reason()["extension"][0]]
        return payload

    def build_organization_reference(self, row):
        ctx = self.context
        absolute_reference = ctx.csv_value(row, "organization_reference")
        reference_id = ctx.csv_value(row, "organization_reference_id")
        reference = absolute_reference or ctx.prefixed_reference("Organization", reference_id)
        return {"reference": reference} if reference else None

    def build_plain_reference(self, row, default_resource_type, absolute_key, id_key, display_key):
        ctx = self.context
        absolute_reference = ctx.csv_value(row, absolute_key)
        reference_id = ctx.csv_value(row, id_key) if id_key else ""
        display = ctx.csv_value(row, display_key) if display_key else ""
        reference = absolute_reference or ctx.prefixed_reference(default_resource_type, reference_id)
        if not reference and not display:
            return None
        return ctx.clean({"reference": reference, "display": display})

    def build_codeable_list(self, row, prefix, max_codings):
        ctx = self.context
        codings = []
        for index in range(1, max_codings + 1):
            coding = ctx.build_coding(
                ctx.csv_value(row, f"{prefix}_coding{index}_system"),
                ctx.csv_value(row, f"{prefix}_coding{index}_code"),
                ctx.csv_value(row, f"{prefix}_coding{index}_display"),
            )
            if coding:
                codings.append(coding)
        text = ctx.csv_value(row, f"{prefix}_text")
        if not codings and not text:
            return []
        return [{"coding": codings, "text": text}]

    def build_telecom(self, row):
        ctx = self.context
        telecom = []
        for index in (1, 2):
            value = ctx.csv_value(row, f"telecom{index}_value")
            if not value:
                continue
            telecom.append({"system": ctx.csv_value(row, f"telecom{index}_system"), "value": value, "use": ctx.csv_value(row, f"telecom{index}_use")})
        return telecom

    def build_available_times(self, row):
        ctx = self.context
        available_times = []
        for index in (1, 2):
            prefix = f"availableTime{index}"
            days = ctx.indexed_days(row, prefix)
            start_time = ctx.csv_value(row, f"{prefix}_availableStartTime")
            end_time = ctx.csv_value(row, f"{prefix}_availableEndTime")
            if not any([days, start_time, end_time]):
                continue
            available_times.append(
                {
                    "daysOfWeek": days,
                    "availableStartTime": start_time,
                    "availableEndTime": end_time,
                }
            )
        return available_times

    def build_not_available(self, row):
        ctx = self.context
        description = ctx.csv_value(row, "notAvailable1_description")
        start = ctx.csv_value(row, "notAvailable1_during_start")
        end = ctx.csv_value(row, "notAvailable1_during_end")
        if not any([description, start, end]):
            return []
        return [{"description": description, "during": {"start": start, "end": end}}]
