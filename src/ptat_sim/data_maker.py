"""data_maker.py: Generate CSV datasets from TOML configuration.

Usage:

    uv run python -m ptat_sim.data_maker

Optional arguments:

    uv run python -m ptat_sim.data_maker --config data/data_sets.toml
    uv run python -m ptat_sim.data_maker --output-dir data

Config format example:

    [defaults]
    batch_size = 1000
    num_sensors = 1
    sampling_rate_hz = 10
    base_temperature_celsius = 25.0
    temperature_step_celsius = 0.02
    nominal_frequency_at_25c_hz = 100000.0
    sensitivity_hz_per_kelvin = 512.0
    noise_stddev_hz = 8.0
    seed = 42

    [[datasets]]
    name = "sample_batch"
    scenario = "drift"

    [[datasets]]
    name = "clean_batch"
    scenario = "clean"
    batch_size = 500

    [[datasets]]
    name = "multi_sensor_batch"
    scenario = "multi_sensor_divergence"
    num_sensors = 3
"""

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
import tomllib
from typing import Any

from ptat_sim.generator import generate_batch
from ptat_sim.models import GeneratorConfig, SensorReading

DEFAULT_CONFIG_PATH = Path("data") / "data_sets.toml"
DEFAULT_OUTPUT_DIR = Path("data")


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate PTAT sensor datasets from TOML configuration."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to TOML dataset configuration file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where CSV files will be written.",
    )
    return parser.parse_args()


def _load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as file:
        return tomllib.load(file)


def _build_generator_config(
    defaults: dict[str, Any],
    dataset: dict[str, Any],
) -> GeneratorConfig:
    """Merge defaults with dataset overrides and build GeneratorConfig."""
    merged: dict[str, Any] = dict(defaults)
    merged.update(dataset)

    merged.pop("name", None)
    merged.pop("scenario", None)
    merged.pop("filename", None)

    valid_fields = set(GeneratorConfig.__dataclass_fields__.keys())
    filtered = {key: value for key, value in merged.items() if key in valid_fields}

    return GeneratorConfig(**filtered)


def _validate_dataset_entry(dataset: dict[str, Any]) -> None:
    """Validate required dataset fields."""
    if "name" not in dataset:
        raise ValueError("Each [[datasets]] entry must include 'name'.")

    if "scenario" not in dataset:
        raise ValueError(
            f"Dataset '{dataset.get('name', '<unknown>')}' is missing 'scenario'."
        )


def _output_filename(dataset: dict[str, Any]) -> str:
    """Determine the output CSV filename for a dataset."""
    if "filename" in dataset:
        filename = str(dataset["filename"])
        if not filename.endswith(".csv"):
            filename = f"{filename}.csv"
        return filename

    return f"{dataset['name']}.csv"


def _write_csv(path: Path, readings: list[SensorReading]) -> None:
    """Write sensor readings to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "sample_index",
        "sensor_id",
        "temperature_celsius",
        "frequency_hz",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for reading in readings:
            writer.writerow(asdict(reading))


def generate_from_config(
    config_path: Path,
    output_dir: Path,
) -> list[Path]:
    """Generate all datasets defined in a TOML config file.

    Returns a list of written CSV paths.
    """
    config = _load_toml(config_path)
    defaults = config.get("defaults", {})
    datasets = config.get("datasets", [])

    if not isinstance(datasets, list) or not datasets:
        raise ValueError("Config must define at least one [[datasets]] entry.")

    written_paths: list[Path] = []

    for dataset in datasets:
        if not isinstance(dataset, dict):
            raise ValueError("Each [[datasets]] entry must be a table/object.")

        _validate_dataset_entry(dataset)

        scenario = str(dataset["scenario"])
        dataset_name = str(dataset["name"])

        generator_config = _build_generator_config(defaults, dataset)
        readings = generate_batch(
            scenario=scenario,  # type: ignore[arg-type]
            config=generator_config,
        )

        output_path = output_dir / _output_filename(dataset)
        _write_csv(output_path, readings)
        written_paths.append(output_path)

        print(
            f"Wrote {dataset_name}: scenario={scenario}, "
            f"rows={len(readings)}, file={output_path}"
        )

    return written_paths


def main() -> None:
    """Run the dataset generator from the command line."""
    args = _parse_args()
    generate_from_config(config_path=args.config, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
