from ..base import BaseResourceGenerator


HEALTH_CONNECT_PROVENANCE_PROFILE = "http://digitalhealth.gov.au/fhir/hcpd/StructureDefinition/hcpd-provenance"


class HealthConnectProvenanceGenerator(BaseResourceGenerator):
    resource_type = "Provenance"
    csv_file = "Provenance.data.csv"

    def build_from_row(self, row):
        ctx = self.context
        provenance = {
            "resourceType": "Provenance",
            "id": ctx.csv_value(row, "resource.id"),
            "meta": ctx.build_meta(HEALTH_CONNECT_PROVENANCE_PROFILE, ctx.csv_value(row, "meta.lastUpdated")),
            "target": [
                {
                    "extension": [{"url": "http://hl7.org/fhir/StructureDefinition/targetPath", "valueString": ctx.csv_value(row, "target.path")}],
                    "reference": ctx.infer_reference(
                        ctx.csv_value(row, "target.reference"),
                        default_resource_type="Practitioner",
                        candidate_types=["PractitionerRole", "Practitioner"],
                    ),
                }
            ],
            "recorded": ctx.csv_value(row, "recorded"),
            "activity": {
                "coding": [
                    {
                        "system": ctx.csv_first(row, "activity.system") or "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                        "code": ctx.csv_value(row, "activity.code"),
                    }
                ]
            },
            "agent": [
                {
                    "type": {
                        "coding": [
                            {
                                "system": ctx.csv_first(row, "agent.type.system") or "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
                                "code": ctx.csv_value(row, "agent.type.code"),
                            }
                        ]
                    },
                    "role": [
                        {
                            "coding": [
                                {
                                    "system": ctx.csv_first(row, "agent.role.system") or "http://terminology.hl7.org/CodeSystem/contractsignertypecodes",
                                    "code": ctx.csv_value(row, "agent.role.code"),
                                }
                            ]
                        }
                    ],
                    "who": {
                        "reference": ctx.infer_reference(
                            ctx.csv_value(row, "agent.who.reference"),
                            default_resource_type="Organization",
                            candidate_types=["Organization", "Practitioner"],
                        )
                    },
                }
            ],
            "entity": [
                {
                    "role": ctx.csv_value(row, "entity0.role"),
                    "what": {
                        "reference": ctx.infer_reference(
                            ctx.csv_value(row, "entity0.what.reference"),
                            candidate_types=["PractitionerRole", "Practitioner", "Organization", "Endpoint", "HealthcareService", "Location"],
                        )
                    },
                }
            ],
        }
        return ctx.clean(provenance)

    def build_bulk(self, index):
        ctx = self.context
        count = self.args.count
        practitioner_pool = count if count <= 2 else count // 2
        organization_pool = practitioner_pool if practitioner_pool <= 10 else practitioner_pool // 10
        practitioner_index = ((index - 1) % practitioner_pool) + 1
        organization_index = ctx.random.randint(1, organization_pool)

        # target can be Practitioner or PractitionerRole
        target_type = ctx.random.choice(["Practitioner", "PractitionerRole"])
        if target_type == "Practitioner":
            target_ref = ctx.practitioner_reference(practitioner_index)
            target_path = ctx.random.choice(["name[0].family", "telecom.where(system='phone').value"])
        else:
            target_ref = f"PractitionerRole/{ctx.bulk_resource_id('practitionerrole', practitioner_index)}"
            target_path = ctx.random.choice(["code[0].coding[0].display", "period.start"])

        # agent.who can be Organization or Practitioner
        agent_who_type = ctx.random.choice(["Organization", "Practitioner"])
        if agent_who_type == "Organization":
            agent_who_ref = ctx.organization_reference(organization_index)
        else:
            agent_who_ref = ctx.practitioner_reference(practitioner_index)

        provenance = {
            "resourceType": "Provenance",
            "id": ctx.bulk_resource_id("provenance", index),
            "meta": ctx.build_meta(HEALTH_CONNECT_PROVENANCE_PROFILE),
            "target": [{"extension": [{"url": "http://hl7.org/fhir/StructureDefinition/targetPath", "valueString": target_path}], "reference": target_ref}],
            "recorded": ctx.faker.iso8601(),
            "activity": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation", "code": "UPDATE"}]},
            "agent": [{"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type", "code": "author"}]}, "role": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/contractsignertypecodes", "code": "AMENDER"}]}], "who": {"reference": agent_who_ref}}],
            "entity": [{"role": "source", "what": {"reference": target_ref}}],
        }
        return ctx.clean(provenance)
