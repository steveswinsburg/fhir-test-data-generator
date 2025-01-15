# fhir-test-data-generator
A generator for producing FHIR resources based on data scenarios

## Prerequisites
Python 3

## Installation (in venv)

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Running

Running the script will generate resources based on the type passed in.
Generated resources will be in the `generated` directory

### Generating Patient resources
`python3 generate.py --type patient`
