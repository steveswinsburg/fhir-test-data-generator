from ..base import BaseResourceGenerator


HEALTH_CONNECT_PRACTITIONER_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-practitioner"


class HealthConnectPractitionerGenerator(BaseResourceGenerator):
    resource_type = "Practitioner"
    csv_file = "Practitioner.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        practitioner_id = row["resource.id"]
        given_name = ctx.csv_value(row, "name.official.given")
        family_name = ctx.csv_value(row, "name.official.family")
        prefix = ctx.csv_value(row, "name.official.prefix")
        name_text = " ".join(part for part in [prefix, given_name, family_name] if part)

        identifiers = []
        hpii_value = ctx.csv_value(row, "identifier.hpii.value")
        if hpii_value:
            identifiers.append(
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "NPI",
                            }
                        ]
                    },
                    "system": "http://ns.electronichealth.net.au/id/hi/hpii/1.0",
                    "value": hpii_value,
                }
            )

        telecom = []
        for index in (1, 2):
            system = ctx.csv_value(row, f"telecom{index}.system")
            value = ctx.csv_value(row, f"telecom{index}.value")
            use = ctx.csv_value(row, f"telecom{index}.use")
            if value:
                telecom.append({"system": system, "value": value, "use": use})

        practitioner = {
            "resourceType": "Practitioner",
            "id": practitioner_id,
            "meta": ctx.build_meta(HEALTH_CONNECT_PRACTITIONER_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/individual-recordedSexOrGender",
                    "extension": [
                        {
                            "url": "value",
                            "valueCodeableConcept": {
                                "coding": [
                                    {
                                        "system": "http://hl7.org/fhir/administrative-gender",
                                        "code": ctx.csv_value(row, "recordedSexOrGender.code"),
                                        "display": ctx.csv_value(row, "recordedSexOrGender.display"),
                                    }
                                ]
                            },
                        }
                    ],
                }
            ],
            "identifier": identifiers,
            "name": [
                {
                    "use": "official",
                    "text": name_text,
                    "family": family_name,
                    "given": [given_name] if given_name else [],
                    "prefix": [prefix] if prefix else [],
                }
            ],
            "telecom": telecom,
            "gender": ctx.csv_value(row, "gender"),
            "address": [
                {
                    "text": ctx.csv_value(row, "address.text"),
                    "line": [ctx.csv_value(row, "address.line1")] if ctx.csv_value(row, "address.line1") else [],
                    "city": ctx.csv_value(row, "address.city"),
                    "state": ctx.csv_value(row, "address.state"),
                    "postalCode": ctx.csv_value(row, "address.postalCode"),
                    "country": ctx.csv_value(row, "address.country"),
                }
            ],
            "qualification": [self.build_default_qualification(row, practitioner_id)],
        }

        gender_identity_code = ctx.csv_value(row, "genderIdentity.code")
        gender_identity_display = ctx.csv_value(row, "genderIdentity.display")
        if gender_identity_code and gender_identity_display:
            practitioner["extension"].append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/individual-genderIdentity",
                    "extension": [
                        {
                            "url": "value",
                            "valueCodeableConcept": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": gender_identity_code,
                                        "display": gender_identity_display,
                                    }
                                ]
                            },
                        }
                    ],
                }
            )

        suppressed_by_code = ctx.csv_value(row, "suppressedBy.code")
        include_self = ctx.csv_value(row, "suppressed.includeSelf")
        if suppressed_by_code != "":
            suppressed_extension = {
                "url": "http://digitalhealth.gov.au/fhir/cc/StructureDefinition/suppressed",
                "extension": [
                    {
                        "url": "suppressedBy",
                        "valueCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://digitalhealth.gov.au/fhir/cc/CodeSystem/suppressed-cs",
                                    "code": suppressed_by_code,
                                },
                            ]
                        },
                    }
                ],
            }
            practitioner["extension"].append(suppressed_extension)

        return ctx.clean(practitioner)

    def build_bulk(self, index):
        ctx = self.context
        practitioner_id = ctx.bulk_resource_id("practitioner", index)
        gender = ctx.random.choice(["male", "female"])
        prefix = ctx.random.choice(["Dr", "A/Prof", "Prof", ""])
        given_name = ctx.faker.first_name_male() if gender == "male" else ctx.faker.first_name_female()
        family_name = ctx.faker.last_name()
        text_name = " ".join(part for part in [prefix, given_name, family_name] if part)
        phone = ctx.faker.phone_number()
        email = f"{given_name}.{family_name}@example.com".lower().replace(" ", "")

        practitioner = {
            "resourceType": "Practitioner",
            "id": practitioner_id,
            "meta": ctx.build_meta(HEALTH_CONNECT_PRACTITIONER_PROFILE),
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/individual-recordedSexOrGender",
                    "extension": [
                        {
                            "url": "value",
                            "valueCodeableConcept": {
                                "coding": [
                                    {
                                        "system": "http://hl7.org/fhir/administrative-gender",
                                        "code": gender,
                                        "display": gender.capitalize(),
                                    }
                                ]
                            },
                        }
                    ],
                }
            ],
            "identifier": [
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "NPI"}]},
                    "system": "http://ns.electronichealth.net.au/id/hi/hpii/1.0",
                    "value": f"80036{ctx.random_digits(11)}",
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": text_name,
                    "family": family_name,
                    "given": [given_name],
                    "prefix": [prefix] if prefix else [],
                }
            ],
            "telecom": [
                {"system": "phone", "value": phone, "use": "work"},
                {"system": "email", "value": email, "use": "work"},
            ],
            "gender": gender,
            "address": [
                {
                    "text": ctx.faker.address().replace("\n", ", "),
                    "line": [ctx.faker.street_address()],
                    "city": ctx.faker.city(),
                    "state": ctx.faker.state_abbr(),
                    "postalCode": ctx.faker.postcode(),
                    "country": "AUS",
                }
            ],
            "qualification": [self.build_default_qualification({}, practitioner_id)],
        }
        return ctx.clean(practitioner)

    def build_default_qualification(self, row, practitioner_id):
        registration_number = self.default_registration_number(practitioner_id)
        profession = row.get("qualification.code.text") or self.context.random.choice(
            [
                "General Practitioner",
                "Physiotherapist",
                "Registered Nurse",
                "Medical Practitioner",
                "Psychologist",
            ]
        )
        return {
            "identifier": [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org.au/CodeSystem/v2-0203",
                                "code": "AHPRA",
                            }
                        ]
                    },
                    "system": "http://hl7.org.au/id/ahpra-registration-number",
                    "value": registration_number,
                }
            ],
            "code": {"text": profession},
            "issuer": {"display": "Ahpra"},
        }

    def default_registration_number(self, practitioner_id):
        digits = "".join(character for character in practitioner_id if character.isdigit())
        suffix = (digits or "0000000000")[-10:].rjust(10, "0")
        return f"MED{suffix}"
