import argparse
import os
import re
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

    args, unknown = parser.parse_known_args(argv)

    # Backward compatibility: allow legacy invocation without explicit subcommand.
    if args.command is None:
        legacy_parser = argparse.ArgumentParser(
            prog="generate.py",
            description="Generate FHIR resources from CSV input or synthetic bulk generation.",
        )
        legacy_parser.add_argument("--type")
        legacy_parser.add_argument("--ig", required=True)
        legacy_parser.add_argument("--mode", required=True, choices=["csv", "bulk"])
        legacy_parser.add_argument("--count", type=int, default=100)
        legacy_parser.add_argument("--seed", type=int, default=42)
        legacy_args = legacy_parser.parse_args(argv)
        legacy_args.command = "generate"
        return legacy_args

    # Now that we have a subcommand, enforce strict parsing for that command.
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