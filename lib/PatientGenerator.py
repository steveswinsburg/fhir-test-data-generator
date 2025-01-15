from lib.BaseGenerator import BaseGenerator
import pandas as pd
from builtins import next

class PatientGenerator(BaseGenerator):
    
    resource_type="Patient";
    
    def run(self):
        print("Generating FHIR Patient resources...")

        # Main template
        patient_template = self.load_template("templates/resources/Patient.json")
        
        # Additional templates
        name_template = self.load_template("templates/datatypes/HumanName.json")
        address_template = self.load_template("templates/datatypes/Address.json")
        telecom_template = self.load_template("templates/datatypes/ContactPoint.json")

        # Load input data
        data = self.load_data("Patient");

        for _, row in data.iterrows():
                        
            # get id
            id = self.get_column_value(row, 'id')
            if id is None:
                continue  # Skip this row if ID is invalid
            
            # Populate base values
            patient_json = self.replace_placeholders(patient_template, row)

            # Handle 'name' array
            name_columns = self.group_columns_by_prefix(data.columns, "name")
            patient_json["name"] = self.parse_array_fields(row, name_columns, name_template)

            # Handle 'address' array
            address_columns = self.group_columns_by_prefix(data.columns, "address")
            patient_json["address"] = self.parse_array_fields(row, address_columns, address_template)
            
            # Write JSON output
            self.write_json(patient_json, PatientGenerator.resource_type, id)
            