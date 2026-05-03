"""Command-line interface for ptat-sim.

Usage:
    uv run ptat-sim
    uv run ptat-sim --config data/data_sets.toml --output-dir data
"""

from ptat_sim.data_maker import main as data_maker_main


def main() -> None:
    """Entry point for the ptat-sim CLI."""
    data_maker_main()
