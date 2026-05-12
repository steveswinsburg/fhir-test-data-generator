from ..base import BaseResourceGenerator


HEALTH_CONNECT_ORGANIZATION_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-organization"


class HealthConnectOrganizationGenerator(BaseResourceGenerator):
    resource_type = "Organization"
    csv_file = "Organization.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        identifiers = [
            {
                "extension": [
                    {
                        "url": "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hi-org-classification",
                        "valueCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://digitalhealth.gov.au/fhir/hcpd/CodeSystem/hi-org-classification-cs",
                                        "code": ctx.token_value(row, "hpio.coding.code"),
                                    "display": ctx.csv_value(row, "identifier.hpio.extension.HCOrgClassification.display"),
                                }
                            ]
                        },
                    }
                ],
                "type": {"coding": [{"system": "http://terminology.hl7.org.au/CodeSystem/v2-0203", "code": "NOI"}]},
                "system": "http://ns.electronichealth.net.au/id/hi/hpio/1.0",
                "value": ctx.csv_value(row, "identifier.hpio.value"),
            },
            {"type": {"text": "ABN"}, "system": "http://hl7.org.au/id/abn", "value": ctx.csv_value(row, "identifier.abn.value")},
            {"type": {"text": "ACN"}, "system": "http://hl7.org.au/id/acn", "value": ctx.csv_value(row, "identifier.acn.value")},
        ]
		
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
            if include_self != "":
                suppressed_extension["extension"][0]["valueCodeableConcept"]["coding"].append(
                    {
                        "url": "includeSelf",
                        "valueBoolean": include_self,
                    }
                )
            identifiers.append(suppressed_extension)
          
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
            "identifier": identifiers,
            "active": ctx.csv_value(row, "active").lower() == "true",
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
        }
        return ctx.clean(organization)

    def build_bulk(self, index):
        ctx = self.context
        org_id = ctx.bulk_resource_id("organization", index)
        company_root = ctx.normalize_text(ctx.faker.company())
        company_name = f"{company_root} {ctx.random.choice(['Clinic', 'Hospital', 'Health', 'Medical Centre'])}".strip()
        website = f"https://{ctx.slugify(company_name)}.example.com.au"
        alias = ctx.normalize_text(company_root.split()[0]) if company_root else "HealthConnect"
        organization = {
            "resourceType": "Organization",
            "id": org_id,
            "meta": ctx.build_meta(HEALTH_CONNECT_ORGANIZATION_PROFILE),
            "identifier": [
                {
                    "extension": [
                        {
                            "url": "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hi-org-classification",
                            "valueCodeableConcept": {
                                "coding": [
                                    {
                                        "system": "http://digitalhealth.gov.au/fhir/hcpd/CodeSystem/hi-org-classification-cs",
                                        "code": "network",
                                        "display": ctx.random.choice(["General Practice", "Public Hospital", "Allied Health Network"]),
                                    }
                                ]
                            },
                        }
                    ],
                    "type": {"coding": [{"system": "http://terminology.hl7.org.au/CodeSystem/v2-0203", "code": "NOI"}]},
                    "system": "http://ns.electronichealth.net.au/id/hi/hpio/1.0",
                    "value": f"80036{ctx.random_digits(11)}",
                },
                {"type": {"text": "ABN"}, "system": "http://hl7.org.au/id/abn", "value": ctx.random_digits(11)},
                {"type": {"text": "ACN"}, "system": "http://hl7.org.au/id/acn", "value": ctx.random_digits(9)},
            ],
            "active": True,
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
        return ctx.clean(organization)
