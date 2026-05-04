"""Smoke tests for processor utilities."""

from __future__ import annotations

import importlib


def test_processor_module_imports() -> None:
    """The processor module should import cleanly."""

    module = importlib.import_module("ptat_sim.processor")

    assert module is not None
