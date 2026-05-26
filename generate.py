import argparse
import os
import sys

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
    print()
    print(f"Generation complete for IG '{ig}' in {mode} mode.")
    print(f"Output directory: {output_dir}")
    print("Summary:")
    for summary in summaries:
        print(
            f"- {summary['resource_type']}: {summary['generated_count']} resources "
            f"({summary['output_format']})"
        )

def main():
    parser = argparse.ArgumentParser(description="Generate FHIR JSON resources.")
    parser.add_argument("--type", help="The resource type to generate. If omitted, generate all matching resources")
    parser.add_argument("--ig", required=True, help="The IG package to use")
    parser.add_argument("--mode", required=True, choices=["csv", "bulk"], help="Generation mode")
    parser.add_argument("--count", type=int, default=100, help="Number of resources to generate in bulk mode")
    parser.add_argument("--seed", type=int, default=42, help="Seed for deterministic bulk generation")
    args = parser.parse_args()

    try:
        ensure_ig_layout(args.ig)
        args.input_dir = default_input_dir(args.ig)
        args.output_dir = default_output_dir(args.ig, args.mode)
        generators = generators_for_args(args)
    except KeyError:
        type_display = args.type or "<all>"
        print(
            f"Error: Unknown generator for IG '{args.ig}' and type '{type_display}'. "
            f"Available combinations: {', '.join(available_generator_keys())}"
        )
        sys.exit(1)
    except FileNotFoundError as error:
        print(f"Error: {error}")
        sys.exit(1)

    summaries = [generator.run() for generator in generators]
    print_generation_summary(args.ig, args.mode, args.output_dir, summaries)

if __name__ == "__main__":
    main()