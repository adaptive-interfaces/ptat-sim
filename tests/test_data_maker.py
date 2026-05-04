"""Smoke tests for data-making utilities."""

from __future__ import annotations

import importlib


def test_data_maker_module_imports() -> None:
    """The data_maker module should import cleanly."""

    module = importlib.import_module("ptat_sim.data_maker")

    assert module is not None
