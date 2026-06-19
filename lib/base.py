import csv
import json
import os
import random
import re


class ProfileContext:
    def __init__(self, args):
        self.args = args
        self.input_dir = args.input_dir
        self.output_dir = args.output_dir
        self.random = random.Random(args.seed)
        self._faker = None

    @property
    def faker(self):
        if self._faker is None:
            try:
                from faker import Faker
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Faker is required for bulk generation mode. Install it to use --mode bulk."
                ) from exc

            self._faker = Faker("en_AU")
            self._faker.seed_instance(self.args.seed)
        return self._faker

    def candidate_input_paths(self, file_name):
        return [os.path.join(self.input_dir, file_name)]

    def input_file_exists(self, file_name):
        return any(os.path.exists(path) for path in self.candidate_input_paths(file_name))

    def csv_rows(self, file_name):
        file_path = next((path for path in self.candidate_input_paths(file_name) if os.path.exists(path)), None)
        if not file_path:
            raise FileNotFoundError(f"Could not find input file '{file_name}' under '{self.input_dir}'")
        with open(file_path, "r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            return list(reader)

    def write_json(self, resource_type, resource_id, payload):
        os.makedirs(self.output_dir, exist_ok=True)
        file_name = f"{resource_type}-{resource_id}.json"
        output_path = os.path.join(self.output_dir, file_name)
        with open(output_path, "w") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        print(f"Saved: {file_name}")

    def write_ndjson(self, resource_type, resources):
        os.makedirs(self.output_dir, exist_ok=True)
        file_name = f"{resource_type}.ndjson"
        output_path = os.path.join(self.output_dir, file_name)
        with open(output_path, "w") as handle:
            for resource in resources:
                handle.write(json.dumps(resource, separators=(",", ":")))
                handle.write("\n")
        print(f"Saved: {file_name}")

    def clean(self, value):
        if isinstance(value, dict):
            cleaned = {}
            for key, child in value.items():
                child_value = self.clean(child)
                if child_value not in (None, [], {}):
                    cleaned[key] = child_value
            return cleaned
        if isinstance(value, list):
            cleaned = [self.clean(item) for item in value]
            return [item for item in cleaned if item not in (None, [], {})]
        if value == "":
            return None
        return value

    def csv_value(self, row, key):
        return row.get(key, "").strip()

    def csv_first(self, row, *keys):
        for key in keys:
            value = self.csv_value(row, key)
            if value:
                return value
        return ""

    def bool_value(self, value):
        return str(value).strip().lower() == "true"

    def row_has_data(self, row):
        return any(str(value).strip() for value in row.values())

    def random_digits(self, length):
        return "".join(self.random.choice("0123456789") for _ in range(length))

    def normalize_text(self, value):
        return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 -]", "", value or "")).strip()

    def build_meta(self, profile_url, last_updated=None):
        meta = {"profile": [profile_url]}
        if last_updated:
            meta["lastUpdated"] = last_updated
        return meta

    def build_identifier_type(self, code=None, system=None, display=None, text=None):
        identifier_type = {}
        coding = self.clean({"system": system, "code": code, "display": display})
        if coding:
            identifier_type["coding"] = [coding]
        if text:
            identifier_type["text"] = text
        return identifier_type or None

    def absolute_reference(self, value, default_resource_type=None):
        reference = str(value).strip()
        if not reference:
            return None
        if "/" in reference:
            return reference
        if default_resource_type:
            return f"{default_resource_type}/{reference}"
        return reference

    def prefixed_reference(self, resource_type, value):
        return self.absolute_reference(value, resource_type)

    def organization_reference(self, index):
        return f"Organization/{self.bulk_resource_id('organization', index)}"

    def practitioner_reference(self, index):
        return f"Practitioner/{self.bulk_resource_id('practitioner', index)}"

    def location_reference(self, index):
        return f"Location/{self.bulk_resource_id('location', index)}"


class BaseResourceGenerator:
    resource_type = None
    csv_file = None

    def __init__(self, args):
        self.args = args
        self.context = None  # set by profile subclass

    def run(self):
        if self.args.mode == "csv":
            generated_count = 0
            for row in self.context.csv_rows(self.csv_file):
                if not self.context.row_has_data(row):
                    continue
                resource = self.build_from_row(row)
                self.context.write_json(self.resource_type, resource["id"], resource)
                generated_count += 1
            return {
                "resource_type": self.resource_type,
                "mode": self.args.mode,
                "generated_count": generated_count,
                "output_dir": self.context.output_dir,
                "output_format": "json",
            }

        resources = [self.build_bulk(index) for index in range(1, self.args.count + 1)]
        self.context.write_ndjson(self.resource_type, resources)
        return {
            "resource_type": self.resource_type,
            "mode": self.args.mode,
            "generated_count": len(resources),
            "output_dir": self.context.output_dir,
            "output_format": "ndjson",
        }

    def build_from_row(self, row):
        raise NotImplementedError()

    def build_bulk(self, index):
        raise NotImplementedError()
