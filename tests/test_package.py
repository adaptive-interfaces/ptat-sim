"""Package-level smoke tests for ptat_sim."""

from __future__ import annotations

import importlib.metadata


def test_package_imports() -> None:
    """The package should import cleanly."""

    import ptat_sim

    assert ptat_sim is not None


def test_installed_package_has_version() -> None:
    """The installed distribution should expose package metadata."""

    version = importlib.metadata.version("ptat-sim")

    assert version
