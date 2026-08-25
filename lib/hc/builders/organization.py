from ..base import BaseResourceGenerator


HEALTH_CONNECT_ORGANIZATION_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-organization"


class HealthConnectOrganizationGenerator(BaseResourceGenerator):
    resource_type = "Organization"
    csv_file = "Organization.data.csv"

    HI_SERVICES_STATUS_CHOICES = [
        ("A", "Active"),
        ("D", "Deactivated"),
        ("R", "Retired"),
    ]

    def random_hi_services_status(self):
        return self.context.random.choice(self.HI_SERVICES_STATUS_CHOICES)

    def random_active(self):
        # active is required by profile; mix true/false only.
        return self.context.random.choice([True, True, False])

    def generate_valid_hpio_value(self):
        # HPI-O must be 16 digits with 800362 prefix and a valid Luhn check digit.
        base = "800362" + self.context.random_digits(9)
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

    def build_hpio_identifier_extensions(self, classification_code, classification_display, status_code, status_display):
        return [
            {
                "url": "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hi-org-classification",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://digitalhealth.gov.au/fhir/hcpd/CodeSystem/hi-org-classification-cs",
                            "code": classification_code,
                            "display": classification_display,
                        }
                    ]
                },
            },
            self.context.build_hpii_status_extension(
                status_code=status_code,
                status_display=status_display,
            ),
        ]

    def build_from_row(self, row):
        ctx = self.context
        hpio_system = "http://ns.electronichealth.net.au/id/hi/hpio/1.0"
        abn_system = "http://hl7.org.au/id/abn"
        acn_system = "http://hl7.org.au/id/acn"
        extensions = []
        hpio_type_display = ctx.csv_value(row, "hpio.coding.display") or "Network"

        abn_type = {"text": "ABN"}
        if ctx.csv_first(row, "identifier.abn.type", "identifier.abn.type.coding.code", "identifier.abn.type.text"):
            abn_type = ctx.build_identifier_type_from_row(
                row,
                "identifier.abn",
                identifier_system=abn_system,
            )

        acn_type = {"text": "ACN"}
        if ctx.csv_first(row, "identifier.acn.type", "identifier.acn.type.coding.code", "identifier.acn.type.text"):
            acn_type = ctx.build_identifier_type_from_row(
                row,
                "identifier.acn",
                identifier_system=acn_system,
            )

        identifiers = [
            {
                "extension": self.build_hpio_identifier_extensions(
                    classification_code=ctx.token_value(row, "hpio.coding.code"),
                    classification_display=hpio_type_display,
                    status_code=ctx.csv_first(row, "identifier.hpio.status.code") or "A",
                    status_display=ctx.csv_first(row, "identifier.hpio.status.display") or "Active",
                ),
                "type": ctx.build_identifier_type_from_row(
                    row,
                    "identifier.hpio",
                    identifier_system=hpio_system,
                    fallback_code="NOI",
                    fallback_text="HPI-O",
                ),
                "system": hpio_system,
                "value": ctx.csv_value(row, "identifier.hpio.value"),
            },
            {
                "type": abn_type,
                "system": abn_system,
                "value": ctx.csv_value(row, "identifier.abn.value"),
            },
            {
                "type": acn_type,
                "system": acn_system,
                "value": ctx.csv_value(row, "identifier.acn.value"),
            },
        ]

        suppressed_by_code = ctx.csv_value(row, "suppressedBy.code")
        include_self = ctx.csv_value(row, "suppressed.includeSelf")
        suppressed_extension = ctx.build_suppressed_extension(suppressed_by_code, include_self)
        if suppressed_extension:
            extensions.append(suppressed_extension)
          
        telecom = []
        for index in range(1, 7):
            system = ctx.token_value(row, f"telecom.system{index}")
            value = ctx.csv_value(row, f"telecom.value{index}")
            use = ctx.token_value(row, f"telecom.use{index}")
            if value:
                telecom.append({"system": system, "value": value, "use": use})

        organization = {
            "resourceType": "Organization",
            "id": ctx.csv_value(row, "resource.id") or ctx.csv_value(row, "name").lower().replace(" ", "-"),
            "meta": ctx.build_meta(HEALTH_CONNECT_ORGANIZATION_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "extension": extensions,
            "identifier": identifiers,
            "active": ctx.bool_value(ctx.csv_first(row, "active") or "true"),
            "name": ctx.csv_value(row, "name"),
            "alias": [ctx.csv_value(row, "alias")] if ctx.csv_value(row, "alias") else [],
            "telecom": telecom,
            "address": [
                {
                    "type": "physical",
                    "line": [ctx.csv_value(row, "address.line")] if ctx.csv_value(row, "address.line") else [],
                    "city": ctx.csv_value(row, "address.city"),
                    "state": ctx.csv_value(row, "address.state"),
                    "postalCode": ctx.csv_value(row, "address.postalCode"),
                    "country": ctx.csv_value(row, "address.country"),
                }
            ],
            "endpoint": [
                {"reference": ctx.csv_value(row, "endpoint.reference")},
                {"reference": ctx.csv_value(row, "endpoint2.reference")},
            ],
        }
        return ctx.clean(organization)

    def build_bulk(self, index):
        ctx = self.context
        org_id = ctx.bulk_resource_id("organization", index)
        hpio_system = "http://ns.electronichealth.net.au/id/hi/hpio/1.0"
        abn_system = "http://hl7.org.au/id/abn"
        acn_system = "http://hl7.org.au/id/acn"
        company_root = ctx.normalize_text(ctx.faker.company())
        company_name = f"{company_root} {ctx.random.choice(['Clinic', 'Hospital', 'Health', 'Medical Centre'])}".strip()
        website = f"https://{ctx.slugify(company_name)}.example.com.au"
        alias = ctx.normalize_text(company_root.split()[0]) if company_root else "HealthConnect"
        status_code, status_display = self.random_hi_services_status()
        active_value = self.random_active()
        organization = {
            "resourceType": "Organization",
            "id": org_id,
            "meta": ctx.build_meta(HEALTH_CONNECT_ORGANIZATION_PROFILE),
            "identifier": [
                {
                    "extension": self.build_hpio_identifier_extensions(
                        classification_code="network",
                        classification_display="Network",
                        status_code=status_code,
                        status_display=status_display,
                    ),
                    "type": ctx.build_identifier_type_for_system(hpio_system),
                    "system": hpio_system,
                    "value": self.generate_valid_hpio_value(),
                },
                    {
                        "type": {"text": "ABN"},
                        "system": abn_system,
                        "value": ctx.random_digits(11),
                    },
                    {
                        "type": {"text": "ACN"},
                        "system": acn_system,
                        "value": ctx.random_digits(9),
                    },
            ],
            "name": company_name,
            "alias": [alias],
            "telecom": [
                {"system": "phone", "value": ctx.faker.phone_number(), "use": "work"},
                {"system": "email", "value": f"contact{index}@example.com.au", "use": "work"},
                {"system": "url", "value": website, "use": "work"},
            ],
            "address": [
                {
                    "type": "physical",
                    "line": [ctx.faker.street_address()],
                    "city": ctx.faker.city(),
                    "state": ctx.faker.state_abbr(),
                    "postalCode": ctx.faker.postcode(),
                    "country": "AUS",
                }
            ],
        }
        organization["active"] = active_value
        return ctx.clean(organization)
