from ..base import BaseResourceGenerator


AU_CORE_PRACTITIONER_PROFILE = "http://hl7.org.au/fhir/core/StructureDefinition/au-core-practitioner"


class AUCorePractitionerGenerator(BaseResourceGenerator):
    resource_type = "Practitioner"
    csv_file = "Practitioner.csv"

    def build_from_row(self, row):
        ctx = self.context
        practitioner = {
            "resourceType": "Practitioner",
            "id": ctx.resource_id(row),
            "meta": ctx.build_meta(AU_CORE_PRACTITIONER_PROFILE),
            "identifier": self.build_identifiers(row),
            "active": ctx.bool_value(ctx.csv_value(row, "active")) if ctx.csv_value(row, "active") else None,
            "name": [self.build_name(row)],
            "telecom": self.build_telecom(row),
            "address": self.build_addresses(row),
            "gender": ctx.csv_value(row, "gender"),
            "qualification": self.build_qualifications(row),
        }
        return ctx.clean(practitioner)

    def build_bulk(self, index):
        ctx = self.context
        gender = ctx.random.choice(["male", "female", "unknown"])
        given_name = ctx.faker.first_name_male() if gender == "male" else ctx.faker.first_name_female()
        family_name = ctx.faker.last_name()
        prefix = ctx.random.choice(["Dr.", "Ms.", "Mr.", "Prof."])
        practitioner = {
            "resourceType": "Practitioner",
            "id": ctx.bulk_resource_id("practitioner", index),
            "meta": ctx.build_meta(AU_CORE_PRACTITIONER_PROFILE),
            "identifier": [
                {
                    "type": ctx.build_identifier_type(code="NPI", system="http://terminology.hl7.org/CodeSystem/v2-0203", text="HPI-I"),
                    "system": "http://ns.electronichealth.net.au/id/hi/hpii/1.0",
                    "value": f"800361{ctx.random_digits(10)}",
                }
            ],
            "active": True,
            "name": [{"use": "official", "family": family_name, "given": [given_name], "prefix": [prefix], "text": f"{prefix} {given_name} {family_name}"}],
            "telecom": [
                {"system": "phone", "use": "work", "value": ctx.faker.phone_number()},
                {"system": "email", "use": "work", "value": f"{given_name}.{family_name}@example.com.au".lower()},
            ],
            "address": [{"use": "work", "line": [ctx.faker.street_address()], "city": ctx.faker.city(), "state": ctx.faker.state_abbr(), "postalCode": ctx.faker.postcode(), "country": "AU"}],
            "gender": gender,
            "qualification": [
                {
                    "identifier": [{"type": ctx.build_identifier_type(code="AHPRA", system="http://terminology.hl7.org.au/CodeSystem/v2-0203", text="Ahpra Registration Number"), "system": "http://hl7.org.au/id/ahpra-registration-number", "value": f"HAC{index:09d}"}],
                    "code": {"text": ctx.random.choice(["Medical Practitioner", "Registered Nurse", "Physiotherapist"])},
                    "issuer": {"display": "Australian Health Practitioner Regulation Agency"},
                }
            ],
        }
        return ctx.clean(practitioner)

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
            identifiers.append(
                {
                    "type": identifier_type,
                    "system": system,
                    "value": value,
                    "assigner": {"display": ctx.csv_value(row, f"identifier{index}_assigner_display")},
                }
            )
        return identifiers

    def build_name(self, row):
        ctx = self.context
        given = [ctx.csv_value(row, "name1_given1")] if ctx.csv_value(row, "name1_given1") else []
        prefix = [ctx.csv_value(row, "name1_prefix1")] if ctx.csv_value(row, "name1_prefix1") else []
        suffix = [ctx.csv_value(row, "name1_suffix1")] if ctx.csv_value(row, "name1_suffix1") else []
        return ctx.clean(
            {
                "use": ctx.csv_value(row, "name1_use") or "official",
                "family": ctx.csv_value(row, "name1_family"),
                "given": given,
                "prefix": prefix,
                "suffix": suffix,
                "text": ctx.csv_value(row, "name1_text"),
            }
        )

    def build_telecom(self, row):
        ctx = self.context
        telecom = []
        for index in (1, 2):
            value = ctx.csv_value(row, f"telecom{index}_value")
            if not value:
                continue
            telecom.append({"system": ctx.csv_value(row, f"telecom{index}_system"), "value": value, "use": ctx.csv_value(row, f"telecom{index}_use")})
        return telecom

    def build_addresses(self, row):
        ctx = self.context
        line1 = ctx.csv_value(row, "address1_line1")
        city = ctx.csv_value(row, "address1_city")
        state = ctx.csv_value(row, "address1_state")
        if not any([line1, city, state]):
            return []
        return [
            {
                "use": ctx.csv_value(row, "address1_use"),
                "line": [line1] if line1 else [],
                "city": city,
                "state": state,
                "postalCode": ctx.csv_value(row, "address1_postalCode"),
                "country": ctx.csv_value(row, "address1_country"),
                "text": ctx.csv_value(row, "address1_text"),
            }
        ]

    def build_qualifications(self, row):
        ctx = self.context
        qualification_value = ctx.csv_value(row, "qualification1_identifier_value")
        qualification_text = ctx.csv_value(row, "qualification1_code_text") or ctx.csv_value(row, "qualification1_ahpraProfessionDetails_Profession_text")
        if not any([qualification_value, qualification_text]):
            return []
        return [
            {
                "identifier": [
                    {
                        "type": ctx.build_identifier_type(
                            code=ctx.csv_value(row, "qualification1_identifier_type_code"),
                            system=ctx.csv_value(row, "qualification1_identifier_type_system"),
                            display=ctx.csv_value(row, "qualification1_identifier_type_display"),
                            text=ctx.csv_value(row, "qualification1_identifier_type_text"),
                        ),
                        "system": ctx.csv_value(row, "qualification1_identifier_system"),
                        "value": qualification_value,
                    }
                ],
                "code": ctx.build_codeable_concept(
                    [
                        ctx.build_coding(
                            ctx.csv_value(row, "qualification1_code_system"),
                            ctx.csv_value(row, "qualification1_code_code"),
                            ctx.csv_value(row, "qualification1_code_display"),
                        )
                    ],
                    qualification_text,
                ),
                "period": {"start": ctx.csv_value(row, "period_start")},
                "issuer": {"display": ctx.csv_value(row, "issuer_display")},
            }
        ]
