from ..base import BaseResourceGenerator


AU_CORE_PATIENT_PROFILE = "http://hl7.org.au/fhir/core/StructureDefinition/au-core-patient"


class AUCorePatientGenerator(BaseResourceGenerator):
    resource_type = "Patient"
    csv_file = "Patient.csv"

    def build_from_row(self, row):
        ctx = self.context
        patient_id = ctx.resource_id(row)
        extensions = self.build_extensions(row)
        identifiers = self.build_identifiers(row)
        names = self.build_names(row)
        telecom = self.build_telecom(row)
        addresses = self.build_addresses(row)
        communications = self.build_communications(row)

        birth_date_extensions = []
        birth_time = ctx.csv_value(row, "birthDate_birthTime")
        if birth_time:
            birth_date_extensions.append(
                {"url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime", "valueDateTime": birth_time}
            )
        accuracy_code = ctx.csv_value(row, "birthDate_accurancyIndicator_code")
        accuracy_display = ctx.csv_value(row, "birthDate_accurancyIndicator_display")
        if accuracy_code or accuracy_display:
            birth_date_extensions.append(
                {
                    "url": "http://hl7.org.au/fhir/StructureDefinition/date-accuracy-indicator",
                    "valueCoding": ctx.build_coding(
                        system="http://hl7.org.au/fhir/CodeSystem/date-accuracy-indicator",
                        code=accuracy_code,
                        display=accuracy_display,
                    ),
                }
            )

        patient = {
            "resourceType": "Patient",
            "id": patient_id,
            "meta": ctx.build_meta(AU_CORE_PATIENT_PROFILE),
            "extension": extensions,
            "identifier": identifiers,
            "active": True,
            "name": names,
            "telecom": telecom,
            "gender": ctx.csv_value(row, "gender"),
            "birthDate": ctx.csv_value(row, "birthDate"),
            "_birthDate": {"extension": birth_date_extensions} if birth_date_extensions else None,
            "address": addresses,
            "communication": communications,
        }
        return ctx.clean(patient)

    def build_bulk(self, index):
        ctx = self.context
        gender = ctx.random.choice(["male", "female", "other", "unknown"])
        given_name = ctx.faker.first_name_male() if gender == "male" else ctx.faker.first_name_female()
        family_name = ctx.faker.last_name()
        patient = {
            "resourceType": "Patient",
            "id": ctx.bulk_resource_id("patient", index),
            "meta": ctx.build_meta(AU_CORE_PATIENT_PROFILE),
            "identifier": [
                {
                    "type": ctx.build_identifier_type(code="NI", system="http://terminology.hl7.org/CodeSystem/v2-0203", text="IHI"),
                    "system": "http://ns.electronichealth.net.au/id/hi/ihi/1.0",
                    "value": f"8003608{ctx.random_digits(9)}",
                }
            ],
            "name": [{"use": "official", "family": family_name, "given": [given_name], "text": f"{given_name} {family_name}"}],
            "telecom": [
                {"system": "phone", "use": "mobile", "value": ctx.faker.phone_number()},
                {"system": "email", "use": "home", "value": f"{given_name}.{family_name}@example.com.au".lower()},
            ],
            "gender": gender,
            "birthDate": ctx.faker.date_of_birth(minimum_age=0, maximum_age=95).isoformat(),
            "address": [
                {
                    "use": "home",
                    "line": [ctx.faker.street_address()],
                    "city": ctx.faker.city(),
                    "state": ctx.faker.state_abbr(),
                    "postalCode": ctx.faker.postcode(),
                    "country": "AU",
                }
            ],
            "communication": [
                {
                    "language": {
                        "coding": [{"system": "urn:ietf:bcp:47", "code": "en", "display": "English"}],
                        "text": "English",
                    },
                    "preferred": True,
                }
            ],
        }
        return ctx.clean(patient)

    def build_extensions(self, row):
        ctx = self.context
        extensions = []
        indigenous_code = ctx.csv_value(row, "indigenousStatus_code")
        indigenous_display = ctx.csv_value(row, "indigenousStatus_display")
        if indigenous_code or indigenous_display:
            extensions.append(
                {
                    "url": "http://hl7.org.au/fhir/StructureDefinition/indigenous-status",
                    "valueCoding": ctx.build_coding(
                        system="https://healthterminologies.gov.au/fhir/CodeSystem/australian-indigenous-status-1",
                        code=indigenous_code,
                        display=indigenous_display,
                    ),
                }
            )

        birth_place_text = ctx.csv_value(row, "birthPlace_text")
        birth_place_country = ctx.csv_value(row, "birthPlace_country")
        if birth_place_text or birth_place_country:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                    "valueAddress": {"text": birth_place_text, "country": birth_place_country},
                }
            )

        date_of_arrival = ctx.csv_value(row, "dateOfArrival")
        if date_of_arrival:
            extensions.append(
                {"url": "http://hl7.org.au/fhir/StructureDefinition/date-of-arrival", "valueDate": date_of_arrival}
            )

        interpreter_required = ctx.csv_value(row, "interpreterRequired")
        if interpreter_required:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-interpreterRequired",
                    "valueBoolean": ctx.bool_value(interpreter_required),
                }
            )

        gender_identity_code = ctx.csv_value(row, "individual_genderIdentity_value_code")
        gender_identity_display = ctx.csv_value(row, "individual_genderIdentity_value_display")
        gender_identity_system = ctx.csv_value(row, "individual_genderIdentity_value_system")
        gender_identity_text = ctx.csv_value(row, "individual_genderIdentity_value_text")
        if gender_identity_code or gender_identity_display or gender_identity_text:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/individual-genderIdentity",
                    "extension": [
                        {
                            "url": "value",
                            "valueCodeableConcept": ctx.build_codeable_concept(
                                [ctx.build_coding(gender_identity_system, gender_identity_code, gender_identity_display)],
                                gender_identity_text,
                            ),
                        }
                    ],
                }
            )

        pronouns_code = ctx.csv_value(row, "individual_pronouns_value_code")
        pronouns_display = ctx.csv_value(row, "individual_pronouns_value_display")
        pronouns_text = ctx.csv_value(row, "individual_pronouns_value_text")
        if pronouns_code or pronouns_display or pronouns_text:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/individual-pronouns",
                    "extension": [
                        {
                            "url": "value",
                            "valueCodeableConcept": ctx.build_codeable_concept(
                                [ctx.build_coding("http://loinc.org", pronouns_code, pronouns_display)],
                                pronouns_text,
                            ),
                        }
                    ],
                }
            )

        rsg_type_code = ctx.csv_value(row, "individual_recordedSexOrGender_type_code")
        rsg_type_system = ctx.csv_value(row, "individual_recordedSexOrGender_type_system")
        rsg_type_text = ctx.csv_value(row, "individual_recordedSexOrGender_type_text")
        rsg_value_code = ctx.csv_value(row, "individual_recordedSexOrGender_value_code")
        rsg_value_system = ctx.csv_value(row, "individual_recordedSexOrGender_value_system")
        rsg_value_text = ctx.csv_value(row, "individual_recordedSexOrGender_value_text")
        if rsg_type_code or rsg_type_text or rsg_value_code or rsg_value_text:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/individual-recordedSexOrGender",
                    "extension": [
                        {
                            "url": "type",
                            "valueCodeableConcept": ctx.build_codeable_concept(
                                [ctx.build_coding(rsg_type_system, rsg_type_code)],
                                rsg_type_text,
                            ),
                        },
                        {
                            "url": "value",
                            "valueCodeableConcept": ctx.build_codeable_concept(
                                [ctx.build_coding(rsg_value_system, rsg_value_code)],
                                rsg_value_text,
                            ),
                        },
                    ],
                }
            )
        return extensions

    def build_identifiers(self, row):
        ctx = self.context
        identifiers = []
        for index in range(1, 6):
            system = ctx.csv_value(row, f"identifier{index}_system")
            value = ctx.csv_value(row, f"identifier{index}_value")
            identifier_type = ctx.build_identifier_type(
                code=ctx.csv_value(row, f"identifier{index}_type_code"),
                system=ctx.csv_value(row, f"identifier{index}_type_system"),
                display=ctx.csv_value(row, f"identifier{index}_type_display"),
                text=ctx.csv_value(row, f"identifier{index}_type_text"),
            )
            if not system and not value and not identifier_type:
                continue
            identifier = {
                "use": ctx.csv_value(row, f"identifier{index}_use"),
                "type": identifier_type,
                "system": system,
                "value": value,
                "period": {"end": ctx.csv_value(row, f"identifier{index}_period_end")},
                "assigner": {"display": ctx.csv_value(row, f"identifier{index}_assigner_display")},
            }
            status_code = ctx.csv_value(row, f"identifier{index}_ihiStatus_code")
            record_status_code = ctx.csv_value(row, f"identifier{index}_ihiRecordStatus_code")
            identifier_extensions = []
            if status_code:
                identifier_extensions.append(
                    {
                        "url": "http://hl7.org.au/fhir/StructureDefinition/ihi-status",
                        "valueCode": status_code,
                    }
                )
            if record_status_code:
                identifier_extensions.append(
                    {
                        "url": "http://hl7.org.au/fhir/StructureDefinition/ihi-record-status",
                        "valueCode": record_status_code,
                    }
                )
            if identifier_extensions:
                identifier["extension"] = identifier_extensions
            identifiers.append(identifier)
        return identifiers or [ctx.data_absent_reason()]

    def build_names(self, row):
        ctx = self.context
        names = []
        for index in (1, 2):
            family = ctx.csv_value(row, f"name{index}_family")
            text = ctx.csv_value(row, f"name{index}_text")
            given = [value for value in [ctx.csv_value(row, f"name{index}_given1"), ctx.csv_value(row, f"name{index}_given2")] if value]
            prefix = [ctx.csv_value(row, f"name{index}_prefix")] if ctx.csv_value(row, f"name{index}_prefix") else []
            if not any([family, text, given, prefix]):
                continue
            names.append(
                {
                    "use": ctx.csv_value(row, f"name{index}_use"),
                    "text": text,
                    "family": family,
                    "given": given,
                    "prefix": prefix,
                }
            )
        return names or [ctx.data_absent_reason()]

    def build_telecom(self, row):
        ctx = self.context
        telecom = []
        for index in range(1, 5):
            value = ctx.csv_value(row, f"telecom{index}_value")
            if not value:
                continue
            telecom.append(
                {
                    "system": ctx.csv_value(row, f"telecom{index}_system"),
                    "use": ctx.csv_value(row, f"telecom{index}_use"),
                    "value": value,
                }
            )
        return telecom

    def build_addresses(self, row):
        ctx = self.context
        addresses = []
        for index in (1, 2):
            line = [value for value in [ctx.csv_value(row, f"address{index}_line1"), ctx.csv_value(row, f"address{index}_line2")] if value]
            city = ctx.csv_value(row, f"address{index}_city")
            state = ctx.csv_value(row, f"address{index}_state")
            if not any([line, city, state, ctx.csv_value(row, f"address{index}_postalCode"), ctx.csv_value(row, f"address{index}_country")]):
                continue
            addresses.append(
                {
                    "use": ctx.csv_value(row, f"address{index}_use"),
                    "line": line,
                    "city": city,
                    "state": state,
                    "postalCode": ctx.csv_value(row, f"address{index}_postalCode"),
                    "country": ctx.csv_value(row, f"address{index}_country"),
                }
            )
        return addresses

    def build_communications(self, row):
        ctx = self.context
        language_code = ctx.csv_value(row, "communication1_language_code")
        language_system = ctx.csv_value(row, "communication1_language_system")
        language_text = ctx.csv_value(row, "communication1_language_text")
        preferred = ctx.csv_value(row, "communication1_preferred")
        if not any([language_code, language_text]):
            return []
        return [
            {
                "language": ctx.build_codeable_concept(
                    [ctx.build_coding(language_system, language_code)],
                    language_text,
                ),
                "preferred": ctx.bool_value(preferred) if preferred else None,
            }
        ]
