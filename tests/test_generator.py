"""Smoke tests for generator utilities."""

from __future__ import annotations

import importlib


def test_generator_module_imports() -> None:
    """The generator module should import cleanly."""

    module = importlib.import_module("ptat_sim.generator")

    assert module is not None
