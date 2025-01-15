import pandas as pd
import json
import os
import re

class BaseGenerator:
    """
    Base class providing common methods for all generators.
    """
    
    input_file = 'data/AU Core Test Data.ods'
    output_dir = 'generated';

    def load_template(self, file_path):
        """Load a JSON template file."""
        
        with open(file_path, "r") as f:
            return json.load(f)
        
    def load_data(self, sheet_name):
        """Load data from an Excel (ODS) file."""
        
        print(f"Loading data from sheet: {sheet_name}")
        return pd.read_excel(BaseGenerator.input_file, sheet_name=sheet_name, engine="odf")
    
    def get_column_value(self, row, column_name):
        """
        Validate and retrieve a value from the specified column in the row.
        Return None if the column is missing, null, or empty.
        """
        if column_name not in row or pd.isnull(row[column_name]) or str(row[column_name]).strip() == "":
            return None
        return str(row[column_name]).strip()
        

    def replace_placeholders(self, template, row):
        """Replace placeholders in the template with actual values"""
        
        if isinstance(template, dict):
            return {key: self.replace_placeholders(value, row) for key, value in template.items()}
        elif isinstance(template, list):
            return [self.replace_placeholders(item, row) for item in template]
        elif isinstance(template, str) and "{{" in template:
            placeholders = re.findall(r"{{(.*?)}}", template)
            for ph in placeholders:
                template = template.replace(f"{{{{{ph}}}}}", str(row.get(ph, "")).strip() if pd.notnull(row.get(ph)) else "")
            return template
        return template

    def group_columns_by_prefix(self, columns, prefix):
        """Group columns dynamically based on a prefix."""
        
        pattern = re.compile(rf"^({prefix}\d*)_(\w+)$")
        grouped = {}
        for col in columns:
            match = pattern.match(col)
            if match:
                group, suffix = match.groups()
                grouped.setdefault(group, {})[suffix] = col
        return grouped

    def parse_array_fields(self, row, grouped_columns, template):
        """Parse array-type fields using their template."""
        array_data = []
        for group, fields in grouped_columns.items():
            instance_data = {key: row[val] for key, val in fields.items() if pd.notnull(row[val])}
            populated_template = self.replace_placeholders(template, instance_data)
            if any(value for value in populated_template.values()):
                array_data.append(populated_template)
        return array_data

    def write_json(self, data, resource_type, id):
        """Save JSON data to a file."""
        
        os.makedirs(BaseGenerator.output_dir, exist_ok=True)
        
        # e.g. Patient-jsmith26.json
        file_name = f"{resource_type}-{id}.json"

        with open(os.path.join(BaseGenerator.output_dir, file_name), "w") as f:
            json.dump(data, f, indent=4)
        print(f"Saved: {file_name}")