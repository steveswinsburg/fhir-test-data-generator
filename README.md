# fhir-test-data-generator
A generator for producing FHIR resources from either CSV data or bulk synthetic data with IG support.

## Prerequisites
Python 3
Java (required for FHIR validator execution)

## Installation

```
pip3 install -r requirements.txt
```

## Running

Running the script will generate resources based on the selected IG, type, and mode.
Generated resources will be written to the selected IG output directory.

The CLI now supports subcommands:

`python3 generate.py generate ...` to run generation

`python3 generate.py list [--ig <ig>]` to inspect supported IGs and resource types

`python3 generate.py doctor` to validate the expected input/output folder layout

Backward compatibility is preserved, so existing commands without the `generate` subcommand still work.

### CSV mode

CSV mode reads CSV files from the selected IG input directory and writes FHIR resources to `output/<ig-name>/csv/`.
If `--type` is omitted, the generator scans the IG input directory and generates every supported resource that has a matching input CSV.

Examples:

`python3 generate.py generate --ig au-core-2.0.0 --mode csv`

`python3 generate.py generate --ig au-core-2.0.0 --type observation --mode csv`

### Bulk mode

Bulk mode uses Faker and writes NDJSON to `output/<ig-name>/bulk/`. It uses bounded pools so overlap stays realistic without doing full referential integrity tracking.
Bulk output is intentionally less strict than CSV mode: it aims for useful synthetic data rather than complete profile-level validity.
If `--type` is omitted, bulk mode generates all supported resource types for the selected IG.

Examples:

`python3 generate.py generate --ig hcpd-26.0.0 --mode bulk --count 100`

`python3 generate.py generate --ig au-core-2.0.0 --type patient --mode bulk --count 1000 --seed 42`

### Discovery and diagnostics

`python3 generate.py list`

`python3 generate.py list --ig hcpd-26.0.0`

`python3 generate.py doctor`

### Validator setup (required for `--validate`)

Validation uses the HL7 FHIR validator CLI JAR at `tools/validator_cli.jar`.
This file is intentionally not committed to git.

1. Download the validator CLI JAR from the official HL7 FHIR validator release page:
	https://github.com/hapifhir/org.hl7.fhir.core/releases
2. Place the downloaded file at:
	`tools/validator_cli.jar`

After that, validation-enabled generation works, for example:

`python3 generate.py generate --ig hcpd-26.0.0 --mode csv --validate`

### CLI switches

`--ig`
Required. The versioned IG package to use, for example `au-core-2.0.0` or `hcpd-26.0.0`.

`--mode`
Required. The generation mode. Supported values: `csv`, `bulk`.

`--type`
Optional. The resource type to generate. If omitted, CSV mode generates every supported type with a matching CSV in the IG input directory, and bulk mode generates every supported type for the selected IG.

`--count`
Number of resources to generate in bulk mode. Defaults to `100`.

`--seed`
Seed for deterministic random generation in bulk mode. Defaults to `42`.

Input and output directories are not configurable via CLI. The generator enforces the profile layout under `IGs/`, `input/`, and `output/`.


## Reference


### Layout

We use a profile-specific directory layout so IG assets, input data, and generated output stay aligned:

```text
IGs/<ig-name>/
input/<ig-name>/
output/<ig-name>/csv/
output/<ig-name>/bulk/
```

For Health Connect in this repo, that means:

```text
IGs/hcpd-26.0.0/
input/hcpd-26.0.0/
output/hcpd-26.0.0/csv/
output/hcpd-26.0.0/bulk/
```

The generator treats the versioned package directory as canonical and expects `IGs`, `input`, and `output` to use the same versioned name.

## Visualisation

Use [fhirviz](https://github.com/steveswinsburg/fhirviz) to render an interactive reference graph from the generated output files.

```sh
python fhirviz.py --dir output/hcpd-26.0.0/bulk
python fhirviz.py --dir output/au-core-2.0.0/scenario
```

The graph is written to `graph.html` inside the same directory. Open it in any browser.

