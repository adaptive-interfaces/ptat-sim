"""Smoke tests for the ptat_sim CLI."""

from __future__ import annotations

import importlib
import subprocess
import sys


def test_cli_module_imports() -> None:
    """The CLI module should import without side effects."""

    module = importlib.import_module("ptat_sim.cli")

    assert module is not None


def test_package_main_help_runs() -> None:
    """The package should be executable as a module and expose help."""

    result = subprocess.run(
        [sys.executable, "-m", "ptat_sim", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    combined_output = f"{result.stdout}\n{result.stderr}".lower()

    assert result.returncode == 0
    assert "usage" in combined_output or "help" in combined_output
