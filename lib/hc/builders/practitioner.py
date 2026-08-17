from ..base import BaseResourceGenerator


HEALTH_CONNECT_PRACTITIONER_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-practitioner"


class HealthConnectPractitionerGenerator(BaseResourceGenerator):
    resource_type = "Practitioner"
    csv_file = "Practitioner.data.csv"

    PRESCRIBER_NUMBER_SYSTEM = "http://ns.electronichealth.net.au/id/medicare-prescriber-number"

    HI_SERVICES_STATUS_CHOICES = [
        ("A", "Active"),
        ("D", "Deactivated"),
        ("R", "Retired"),
    ]

    def random_hi_services_status(self):
        return self.context.random.choice(self.HI_SERVICES_STATUS_CHOICES)

    def random_active_or_none(self):
        # Practitioner.active is optional; omit it for about half of generated records.
        return self.context.random.choice([None, None, True, False])

    def generate_valid_hpii_value(self):
        # HPI-I must be 16 digits with 800361 prefix and a valid Luhn check digit.
        base = "800361" + self.context.random_digits(9)
        digits = [int(ch) for ch in base]
        total = 0
        parity = (len(digits) + 1) % 2
        for idx, digit in enumerate(digits):
            value = digit
            if idx % 2 == parity:
                value *= 2
                if value > 9:
                    value -= 9
            total += value
        check_digit = (10 - (total % 10)) % 10
        return f"{base}{check_digit}"

    def build_from_row(self, row):
        ctx = self.context
        practitioner_id = row["resource.id"]
        given_name = ctx.csv_value(row, "name.official.given")
        family_name = ctx.csv_value(row, "name.official.family")
        prefix = ctx.csv_value(row, "name.official.prefix")
        name_text = " ".join(part for part in [prefix, given_name, family_name] if part)

        identifiers = []
        hpii_value = ctx.csv_value(row, "identifier.hpii.value")
        hpii_status_code = ctx.csv_value(row, "identifier.hpii.status.code")
        hpii_status_display = ctx.csv_value(row, "identifier.hpii.status.display")
        hpii_status_system = ctx.csv_value(row, "identifier.hpii.status.system")
        if hpii_value:
            identifier_extensions = []
            status_extension = ctx.build_hpii_status_extension(
                status_code=hpii_status_code or "A",
                status_display=hpii_status_display or "Active",
                status_system=hpii_status_system,
            )
            if status_extension:
                identifier_extensions.append(status_extension)
            identifiers.append(
                {
                    "extension": identifier_extensions,
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

        prescriber_number = ctx.csv_value(row, "identifier.prescriber.value")
        if prescriber_number:
            identifiers.append(self.build_prescriber_identifier(prescriber_number))

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
            "birthDate": ctx.csv_value(row, "birthDate"),
            "photo": self.build_photo(ctx.csv_value(row, "photo.url"), name_text),
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
        suppressed_extension = ctx.build_suppressed_extension(suppressed_by_code, include_self)
        if suppressed_extension:
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
        status_code, status_display = self.random_hi_services_status()
        active_value = self.random_active_or_none()
        birth_date = ctx.faker.date_of_birth(minimum_age=25, maximum_age=70).isoformat()

        if gender == "male":
            gender_identity_code, gender_identity_display = "446151000124109", "Identifies as male gender"
        else:
            gender_identity_code, gender_identity_display = "446141000124107", "Identifies as female gender"

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
                },
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
                },
            ],
            "identifier": [
                {
                    "extension": [
                        ctx.build_hpii_status_extension(
                            status_code=status_code,
                            status_display=status_display,
                        )
                    ],
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "NPI"}]},
                    "system": "http://ns.electronichealth.net.au/id/hi/hpii/1.0",
                    "value": self.generate_valid_hpii_value(),
                },
                self.build_prescriber_identifier(ctx.random_digits(7)),
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
            "birthDate": birth_date,
            "photo": self.build_photo(f"https://example.com/photo/{practitioner_id}.png", text_name),
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
        if active_value is not None:
            practitioner["active"] = active_value
        return ctx.clean(practitioner)

    def build_prescriber_identifier(self, value):
        return {
            "type": {
                "coding": [
                    {
                        "system": self.context.V2_0203_SYSTEM,
                        "code": "PRES",
                        "display": "Prescriber Number",
                    }
                ],
                "text": "Prescriber Number",
            },
            "system": self.PRESCRIBER_NUMBER_SYSTEM,
            "value": value,
        }

    def build_photo(self, url, name_text=None):
        if not url:
            return []
        photo = {"contentType": "image/png", "url": url}
        if name_text:
            photo["title"] = f"Photo of {name_text}"
        return [photo]

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
