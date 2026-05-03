# AGENTS.md (ptat-sim)

## Scope

This repository provides a synthetic PTAT sensor simulation engine
and a stable typed readings interface.
Changes must preserve:

- determinism (same seed, same config produces identical output)
- interface stability (`SensorReading`, `GeneratorConfig`, `ProcessorConfig`
  are the contract; downstream consumers depend on them)
- scenario fidelity (each `ScenarioKind` has a specified behavioral contract)

Do not modify the interface dataclasses without a corresponding DECISIONS.md entry.
Do not add scenarios without updating SKILL.md operating rules and test coverage table.

## WHY

This repo uses a uniform, reproducible workflow based on `uv` and `pyproject.toml`.
These instructions exist to prevent tool drift and OS mismatch.

## Requirements

Use `uv` for all environment, dependency, and run commands in this repo.
Do not recommend or use `pip install` as the primary workflow.
The canonical Python version is defined in `.python-version`.
Commands and guidance must work on Windows, macOS, and Linux.
If shell-specific commands are unavoidable, provide both:

- PowerShell (Windows)
- bash/zsh (macOS/Linux)

## Quickstart

```shell
uv self update
uv python pin $(cat .python-version)
uv sync --extra dev --upgrade
```

## Common Tasks

Lint and format:

```shell
uv run python -m ruff format .
uv run python -m ruff check . --fix
```

Run tests:

```shell
uv run pytest
```

Generate datasets:

```shell
uv run ptat-sim
uv run ptat-sim --config data/data_sets.toml --output-dir data
```

## Formatting Conventions

Document titles use the filename and repo name in parentheses:
`# DECISIONS.md (ptat-sim)`

Numbered decision sections use periods:
`## D-001. Purpose of this repository`

Avoid emdashes.
Avoid endashes.
Prefer semicolons, commas, or starting a new sentence.
Start each sentence on a new line to assist diffs.
Keep line length to 100 characters wherever possible.

## Agent Task Assignment

Before generating any test program or analysis tool that uses this API:

1. Read `SKILL.md`; it is the operating guide, not optional documentation.
2. Read `DECISIONS.md`; it explains why the interface is shaped the way it is.
3. Confirm understanding of the five `ScenarioKind` values and their behavioral contracts.
4. Confirm `frequency_hz: None` handling before writing any reading consumer.

## pre-commit

```shell
uvx pre-commit install
uvx pre-commit run --all-files
```
