import argparse
import sys

# Import all generator classes
from lib.PatientGenerator import PatientGenerator

# Map of types to their respective generator classes
GENERATORS = {
    "patient": PatientGenerator
}

def main():
    parser = argparse.ArgumentParser(description="Generate FHIR JSON resources.")
    parser.add_argument("--type", required=True, help="The resource type to generate (e.g., 'patient', 'practitioner')")
    args = parser.parse_args()

    # Select the appropriate generator class
    generator_class = GENERATORS.get(args.type.lower())
    if not generator_class:
        print(f"Error: Unknown resource type '{args.type}'. Available types: {', '.join(GENERATORS.keys())}")
        sys.exit(1)

    # Instantiate and run the generator
    generator = generator_class()
    generator.run()

if __name__ == "__main__":
    main()