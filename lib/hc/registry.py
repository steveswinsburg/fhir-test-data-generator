from lib.hc.builders.coverage_area import HealthConnectCoverageAreaGenerator
from lib.hc.builders.endpoint import HealthConnectEndpointGenerator
from lib.hc.builders.healthcare_service import HealthConnectHealthcareServiceGenerator
from lib.hc.builders.location import HealthConnectLocationGenerator
from lib.hc.builders.organization import HealthConnectOrganizationGenerator
from lib.hc.builders.practitioner import HealthConnectPractitionerGenerator
from lib.hc.builders.practitioner_role import HealthConnectPractitionerRoleGenerator
from lib.hc.builders.provenance import HealthConnectProvenanceGenerator


BUILDERS = {
    ("hcpd-26.0.0", "practitioner"): HealthConnectPractitionerGenerator,
    ("hcpd-26.0.0", "practitionerrole"): HealthConnectPractitionerRoleGenerator,
    ("hcpd-26.0.0", "organization"): HealthConnectOrganizationGenerator,
    ("hcpd-26.0.0", "location"): HealthConnectLocationGenerator,
    ("hcpd-26.0.0", "coveragearea"): HealthConnectCoverageAreaGenerator,
    ("hcpd-26.0.0", "endpoint"): HealthConnectEndpointGenerator,
    ("hcpd-26.0.0", "healthcareservice"): HealthConnectHealthcareServiceGenerator,
    ("hcpd-26.0.0", "provenance"): HealthConnectProvenanceGenerator,
}
