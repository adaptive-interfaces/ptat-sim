"""Smoke tests for PTAT simulation models."""

from __future__ import annotations

import importlib


def test_models_module_imports() -> None:
    """The models module should import cleanly."""

    module = importlib.import_module("ptat_sim.models")

    assert module is not None


def test_models_expose_public_names() -> None:
    """The models module should expose at least one public name."""

    module = importlib.import_module("ptat_sim.models")

    public_names = [name for name in dir(module) if not name.startswith("_")]

    assert public_names
