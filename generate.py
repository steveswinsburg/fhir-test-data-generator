import argparse
import os
import re
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lib.registry import available_generator_keys, builders_for_ig, create_generator


IG_LAYOUTS = {
    "hcpd-26.0.0": {
        "package_dir": "hcpd-26.0.0",
        "ig_dir": "hcpd-26.0.0",
    },
    "au-core-2.0.0": {
        "package_dir": "au-core-2.0.0",
        "ig_dir": "au-core-2.0.0",
    },
}

console = Console()
FHIR_VALIDATOR_VERSION = "4.0.1"
FHIR_VALIDATOR_JAR = os.path.join("tools", "validator_cli.jar")
FHIR_VALIDATOR_TX_CACHE = os.path.join(".fhir", "tx-cache")
FHIR_VALIDATOR_PACKAGES_DIR = "packages"


def ig_layout(ig):
    normalized_ig = ig.lower()
    if normalized_ig not in IG_LAYOUTS:
        raise KeyError(normalized_ig)
    return IG_LAYOUTS[normalized_ig]


def default_input_dir(ig):
    return os.path.join("input", ig_layout(ig)["package_dir"])


def default_output_dir(ig, mode):
    return os.path.join("output", ig_layout(ig)["package_dir"], mode)


def ensure_ig_layout(ig):
    layout = ig_layout(ig)
    ig_dir = os.path.join("IGs", layout["ig_dir"])
    input_dir = os.path.join("input", layout["package_dir"])
    output_root = os.path.join("output", layout["package_dir"])
    output_csv_dir = os.path.join(output_root, "csv")
    output_bulk_dir = os.path.join(output_root, "bulk")

    # IG artifacts are optional at runtime; CSV/BULK generation only requires input fixtures.
    missing_dirs = [path for path in [input_dir] if not os.path.isdir(path)]
    if missing_dirs:
        missing_display = ", ".join(missing_dirs)
        raise FileNotFoundError(f"Missing required layout directories for IG '{ig}': {missing_display}")

    os.makedirs(output_csv_dir, exist_ok=True)
    os.makedirs(output_bulk_dir, exist_ok=True)

    return {
        "ig_dir": ig_dir,
        "input_dir": input_dir,
        "output_root": output_root,
        "output_csv_dir": output_csv_dir,
        "output_bulk_dir": output_bulk_dir,
    }


def generators_for_args(args):
    if args.type:
        return [create_generator(args)]

    ig_builders = builders_for_ig(args.ig)
    if not ig_builders:
        raise KeyError(args.ig.lower())

    generators = []
    for resource_type, builder_class in sorted(ig_builders.items()):
        generator = builder_class(args)
        if args.mode == "csv" and not generator.context.input_file_exists(generator.csv_file):
            continue
        generators.append(generator)

    if generators:
        return generators

    if args.mode == "csv":
        raise FileNotFoundError(
            f"No CSV input files matched known resource generators under '{args.input_dir}'"
        )

    return generators


def print_generation_summary(ig, mode, output_dir, summaries):
    summary_table = Table(title="Generation Summary")
    summary_table.add_column("Resource Type", style="cyan")
    summary_table.add_column("Generated", justify="right", style="green")
    summary_table.add_column("Format", style="magenta")

    for summary in summaries:
        summary_table.add_row(
            summary["resource_type"],
            str(summary["generated_count"]),
            summary["output_format"],
        )

    console.print()
    console.print(
        Panel.fit(
            f"IG: [bold]{ig}[/bold]\nMode: [bold]{mode}[/bold]\nOutput: [bold]{output_dir}[/bold]",
            title="FHIR Test Data Generator",
            border_style="green",
        )
    )
    console.print(summary_table)


def run_fhir_cli_validation(args, summaries):
    file_paths = []
    for summary in summaries:
        file_paths.extend(summary.get("output_files", []))

    validate_files = [
        path
        for path in file_paths
        if path.lower().endswith(".json") or path.lower().endswith(".ndjson")
    ]
    if not validate_files:
        console.print("[yellow]Validation skipped: no JSON/NDJSON files produced in this run.[/yellow]")
        return 0

    if not os.path.exists(FHIR_VALIDATOR_JAR):
        raise FileNotFoundError(f"FHIR validator jar not found: {FHIR_VALIDATOR_JAR}")

    ig_package = os.path.join(
        FHIR_VALIDATOR_PACKAGES_DIR,
        f"{ig_layout(args.ig)['package_dir']}.tgz",
    )
    if not os.path.exists(ig_package):
        raise FileNotFoundError(f"FHIR validator IG package not found: {ig_package}")

    command = [
        "java",
        "-jar",
        FHIR_VALIDATOR_JAR,
        *validate_files,
        "-version",
        FHIR_VALIDATOR_VERSION,
        "-ig",
        ig_package,
        "-output-style",
        "compact",
        "-level",
        args.validator_level,
    ]

    if args.disable_tx:
        command.extend(["-tx", "n/a"])
    else:
        os.makedirs(FHIR_VALIDATOR_TX_CACHE, exist_ok=True)
        command.extend(["-txCache", FHIR_VALIDATOR_TX_CACHE])

    console.print()
    console.print(
        Panel.fit(
            f"Validator: [bold]{FHIR_VALIDATOR_JAR}[/bold]\n"
            f"Input files: [bold]{len(validate_files)}[/bold]\n"
            f"FHIR version: [bold]{FHIR_VALIDATOR_VERSION}[/bold]\n"
            f"IG package: [bold]{ig_package}[/bold]\n"
            f"TX mode: [bold]{'disabled (-tx n/a)' if args.disable_tx else f'cache at {FHIR_VALIDATOR_TX_CACHE}'}[/bold]",
            title="FHIR Validator CLI",
            border_style="cyan",
        )
    )

    result = subprocess.run(command)
    return result.returncode


def normalize_resource_type(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_args(args):
    args.ig = args.ig.lower()
    if getattr(args, "type", None):
        args.type = normalize_resource_type(args.type)


def print_error(message):
    console.print(f"[bold red]Error:[/bold red] {message}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="generate.py",
        description="Generate FHIR resources from CSV input or synthetic bulk generation.",
    )
    subparsers = parser.add_subparsers(dest="command")

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate resources",
        description="Generate resources for a selected IG in csv or bulk mode.",
    )
    generate_parser.add_argument(
        "--type",
        help="Resource type to generate. If omitted, generate all matching resources",
    )
    generate_parser.add_argument("--ig", required=True, help="The IG package to use")
    generate_parser.add_argument("--mode", required=True, choices=["csv", "bulk"], help="Generation mode")
    generate_parser.add_argument("--count", type=int, default=100, help="Resource count for bulk mode")
    generate_parser.add_argument("--seed", type=int, default=42, help="Seed for deterministic bulk generation")
    generate_parser.add_argument(
        "--validate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run post-generation validation through the FHIR validator CLI jar (default: enabled)",
    )
    generate_parser.add_argument(
        "--validator-level",
        choices=["hints", "warnings", "errors"],
        default="errors",
        help="Minimum issue level reported by validator jar",
    )
    generate_parser.add_argument(
        "--disable-tx",
        action="store_true",
        help="Disable external terminology server lookups during validation (passes -tx n/a to validator)",
    )
    generate_parser.add_argument(
        "--fail-on-validation",
        action="store_true",
        help="Return a non-zero exit code when validation errors are detected",
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List supported IGs and resource types",
        description="Show available IG packages and resource generators.",
    )
    list_parser.add_argument("--ig", help="Optional IG filter")

    subparsers.add_parser(
        "doctor",
        help="Validate expected repo layout",
        description="Check input and output directories for all configured IGs.",
    )
    return parser.parse_args(argv)


def command_list(args):
    ig_keys = sorted(IG_LAYOUTS)
    requested_ig = args.ig.lower() if args.ig else None

    if requested_ig and requested_ig not in IG_LAYOUTS:
        raise KeyError(requested_ig)

    ig_table = Table(title="Supported IGs")
    ig_table.add_column("IG", style="cyan")
    ig_table.add_column("Input Dir", style="green")
    ig_table.add_column("Output Root", style="magenta")

    for ig in ig_keys:
        if requested_ig and ig != requested_ig:
            continue
        ig_table.add_row(ig, default_input_dir(ig), os.path.join("output", ig_layout(ig)["package_dir"]))

    type_table = Table(title="Supported Resource Types")
    type_table.add_column("IG", style="cyan")
    type_table.add_column("Type", style="yellow")

    for ig in ig_keys:
        if requested_ig and ig != requested_ig:
            continue
        ig_builders = builders_for_ig(ig)
        for resource_type in sorted(ig_builders):
            type_table.add_row(ig, resource_type)

    console.print(ig_table)
    console.print(type_table)


def command_doctor():
    table = Table(title="Layout Validation")
    table.add_column("IG", style="cyan")
    table.add_column("Input", style="green")
    table.add_column("Output CSV", style="magenta")
    table.add_column("Output Bulk", style="magenta")
    table.add_column("Status")

    has_errors = False
    for ig in sorted(IG_LAYOUTS):
        input_dir = default_input_dir(ig)
        output_csv = default_output_dir(ig, "csv")
        output_bulk = default_output_dir(ig, "bulk")

        input_exists = os.path.isdir(input_dir)
        csv_exists = os.path.isdir(output_csv)
        bulk_exists = os.path.isdir(output_bulk)

        status = "ok" if input_exists else "missing input"
        if not input_exists:
            has_errors = True

        table.add_row(
            ig,
            "yes" if input_exists else "no",
            "yes" if csv_exists else "no",
            "yes" if bulk_exists else "no",
            status,
        )

    console.print(table)
    return 1 if has_errors else 0


def command_generate(args):
    if args.count <= 0:
        raise ValueError("--count must be greater than 0")

    ensure_ig_layout(args.ig)
    args.input_dir = default_input_dir(args.ig)
    args.output_dir = default_output_dir(args.ig, args.mode)
    generators = generators_for_args(args)

    if not generators:
        print_error("No generators resolved for the supplied options.")
        return 1

    summaries = []
    for generator in generators:
        console.print(f"[cyan]Generating[/cyan] {generator.resource_type}...")
        summaries.append(generator.run())

    print_generation_summary(args.ig, args.mode, args.output_dir, summaries)

    if args.validate:
        exit_code = run_fhir_cli_validation(args, summaries)
        if args.fail_on_validation and exit_code != 0:
            return 2

    return 0

def main():
    args = parse_args()
    if getattr(args, "ig", None):
        normalize_args(args)

    try:
        if args.command == "list":
            command_list(args)
            return
        if args.command == "doctor":
            sys.exit(command_doctor())
        if args.command == "generate":
            sys.exit(command_generate(args))

        raise ValueError("Unknown command")
    except KeyError:
        type_display = getattr(args, "type", None) or "<all>"
        print_error(
            f"Unknown generator for IG '{getattr(args, 'ig', '<missing>')}' and type '{type_display}'. "
            f"Available combinations: {', '.join(available_generator_keys())}"
        )
        sys.exit(1)
    except FileNotFoundError as error:
        print_error(str(error))
        sys.exit(1)
    except ValueError as error:
        print_error(str(error))
        sys.exit(1)

if __name__ == "__main__":
    main()