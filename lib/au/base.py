import uuid

from lib.base import ProfileContext
from lib.base import BaseResourceGenerator as _BaseResourceGenerator


DATA_ABSENT_REASON_URL = "http://hl7.org/fhir/StructureDefinition/data-absent-reason"


class AUCoreContext(ProfileContext):
    def slugify(self, value):
        normalized = self.normalize_text(value).lower().replace(" ", "-")
        return normalized or "au-core"

    def bulk_resource_id(self, resource_name, index):
        return f"aucore-{resource_name}-{index:07d}"

    def practitioner_role_reference(self, index):
        return f"PractitionerRole/{self.bulk_resource_id('practitionerrole', index)}"

    def build_coding(self, system=None, code=None, display=None):
        return self.clean({"system": system, "code": code, "display": display})

    def build_codeable_concept(self, codings=None, text=None):
        value = {}
        if codings:
            cleaned_codings = [coding for coding in (self.clean(coding) for coding in codings) if coding]
            if cleaned_codings:
                value["coding"] = cleaned_codings
        if text:
            value["text"] = text
        return value or None

    def build_codings_from_prefix(self, row, prefix, count):
        codings = []
        for index in range(1, count + 1):
            coding = self.build_coding(
                self.csv_value(row, f"{prefix}_coding{index}_system"),
                self.csv_value(row, f"{prefix}_coding{index}_code"),
                self.csv_value(row, f"{prefix}_coding{index}_display"),
            )
            if coding:
                codings.append(coding)
        return codings

    def build_codeable_concept_from_prefix(self, row, prefix, count=3, text_key=None):
        text = self.csv_value(row, text_key or f"{prefix}_text")
        return self.build_codeable_concept(self.build_codings_from_prefix(row, prefix, count), text)

    def build_quantity(self, value=None, unit=None, system=None, code=None):
        return self.clean({"value": self._coerce_number(value), "unit": unit, "system": system, "code": code})

    def build_quantity_from_prefix(self, row, prefix):
        return self.build_quantity(
            self.csv_value(row, f"{prefix}_value"),
            self.csv_value(row, f"{prefix}_unit"),
            self.csv_value(row, f"{prefix}_system"),
            self.csv_value(row, f"{prefix}_code"),
        )

    def build_period(self, start=None, end=None):
        return self.clean({"start": start, "end": end})

    def build_period_from_prefix(self, row, prefix):
        return self.build_period(self.csv_value(row, f"{prefix}_start"), self.csv_value(row, f"{prefix}_end"))

    def build_age_from_prefix(self, row, prefix):
        return self.build_quantity_from_prefix(row, prefix)

    def build_reference(self, reference=None, resource_type=None, reference_id=None, display=None, identifier=None):
        resolved_reference = reference or self.prefixed_reference(resource_type, reference_id)
        return self.clean({"reference": resolved_reference, "display": display, "identifier": identifier})

    def build_reference_from_parts(self, row, prefix, resource_type_key=None, id_key=None, display_key=None):
        return self.build_reference(
            resource_type=self.csv_value(row, resource_type_key) if resource_type_key else None,
            reference_id=self.csv_value(row, id_key) if id_key else None,
            display=self.csv_value(row, display_key) if display_key else None,
        )

    def build_identifier(self, type_value=None, system=None, value=None, use=None, assigner_display=None, period=None, extension=None):
        identifier = {
            "use": use,
            "type": type_value,
            "system": system,
            "value": value,
            "assigner": {"display": assigner_display} if assigner_display else None,
            "period": period,
            "extension": extension,
        }
        return self.clean(identifier)

    def build_identifier_from_prefix(self, row, prefix):
        identifier_type = self.build_identifier_type(
            code=self.csv_value(row, f"{prefix}_type_code"),
            system=self.csv_value(row, f"{prefix}_type_system"),
            display=self.csv_value(row, f"{prefix}_type_display"),
            text=self.csv_value(row, f"{prefix}_type_text"),
        )
        return self.build_identifier(
            type_value=identifier_type,
            system=self.csv_value(row, f"{prefix}_system"),
            value=self.csv_value(row, f"{prefix}_value"),
            use=self.csv_value(row, f"{prefix}_use"),
            assigner_display=self.csv_value(row, f"{prefix}_assigner_display"),
            period=self.build_period_from_prefix(row, f"{prefix}_period"),
        )

    def build_reference_identifier(self, row, prefix):
        identifier_type = self.build_identifier_type(
            code=self.csv_value(row, f"{prefix}_type_code"),
            system=self.csv_value(row, f"{prefix}_type_system"),
            display=self.csv_value(row, f"{prefix}_type_display"),
            text=self.csv_value(row, f"{prefix}_type_text"),
        )
        return self.build_identifier(
            type_value=identifier_type,
            system=self.csv_value(row, f"{prefix}_system"),
            value=self.csv_value(row, f"{prefix}_value"),
            assigner_display=self.csv_value(row, f"{prefix}_assigner_display"),
        )

    def build_reference_with_identifier(self, row, resource_type_key, id_key, display_key, identifier_prefix):
        identifier = self.build_reference_identifier(row, identifier_prefix)
        if not identifier:
            identifier = None
        return self.build_reference(
            resource_type=self.csv_value(row, resource_type_key),
            reference_id=self.csv_value(row, id_key),
            display=self.csv_value(row, display_key),
            identifier=identifier,
        )

    def build_human_name(self, use=None, text=None, family=None, given=None, prefix=None, suffix=None):
        return self.clean(
            {
                "use": use,
                "text": text,
                "family": family,
                "given": given or [],
                "prefix": prefix or [],
                "suffix": suffix or [],
            }
        )

    def build_telecom(self, system=None, value=None, use=None):
        return self.clean({"system": system, "value": value, "use": use})

    def build_address(self, use=None, type_value=None, text=None, line=None, city=None, state=None, postal_code=None, country=None):
        return self.clean(
            {
                "use": use,
                "type": type_value,
                "text": text,
                "line": line or [],
                "city": city,
                "state": state,
                "postalCode": postal_code,
                "country": country,
            }
        )

    def _coerce_number(self, value):
        text = str(value).strip()
        if not text:
            return None
        try:
            if any(marker in text for marker in [".", "e", "E"]):
                return float(text)
            return int(text)
        except ValueError:
            return text

    def data_absent_reason(self, code="unknown"):
        return {"extension": [{"url": DATA_ABSENT_REASON_URL, "valueCode": code}]}

    def resource_id(self, row):
        direct_id = self.csv_value(row, "id") or self.csv_value(row, "old_id")
        if direct_id:
            return direct_id

        for key in (
            "name1_text",
            "name1_family",
            "name1_given1",
            "name",
            "identifier1_value",
            "identifier2_value",
        ):
            value = self.csv_value(row, key)
            if value:
                return self.slugify(value)

        return self.slugify(uuid.uuid4().hex)

    def indexed_days(self, row, prefix, max_days=7):
        days = []
        for index in range(1, max_days + 1):
            day = self.csv_value(row, f"{prefix}_daysOfWeek{index}")
            if day:
                days.append(day)
        return days


class BaseResourceGenerator(_BaseResourceGenerator):
    def __init__(self, args):
        self.args = args
        self.context = AUCoreContext(args)
