# ptat-sim

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Synthetic PTAT sensor simulation engine and stable readings interface.

Part of the [Adaptive Interfaces](https://github.com/adaptive-interfaces) ecosystem.

## Introduction

Proportional To Absolute Temperature (PTAT) circuits
produce an output signal that scales linearly
with absolute temperature in Kelvin.
PTAT circuits are used in thermal monitoring systems inside
CPUs, power electronics, battery management systems, and
industrial thermal monitoring equipment.

In production systems, engineers watch streams of PTAT readings over time.
A single reading is rarely meaningful.
The shape of the stream is what matters:
slow drift, sudden spikes, sensor dropout, or divergence between sensors
are the signals that indicate problems before they become failures.

This project, `ptat-sim` provides a deterministic engine that
generates realistic PTAT reading streams
for each of those conditions.
It exists so that test programs and agent-assigned tasks can be built against
a stable, typed interface contract rather than a live sensor system.

## PTAT for Agent Evaluation

PTAT was chosen as the reference domain for agent task assignment because:

- Deterministic physics (linear relationship, closed-form formula)
- Five well-defined anomaly types that are realistic and distinct
- Dual output (temperature AND frequency) requires the agent to understand the domain, not just pattern-match
- None as a valid signal value (dropout) is a common source of consumer bugs
- Multi-sensor scenarios require reasoning about relationships between streams

This PTAT profile makes it hard to fake understanding.
An agent that doesn't read SKILL.md will get it wrong in detectable ways.

## Artifacts for Downstream Use

```text
ptat-sim/
  data/*.csv
  data/data_sets.toml
  data/ptat-sim-output.lock
```

## Downstream Clients

Downstream clients call generate_batch(scenario, config),
get back a list of SensorReading objects, and
feed them into a processor, a test harness, or a monitoring dashboard.
The interface is the boundary.
They never touch sim internals.

## Scope: Included

A deterministic synthetic data generator for
PTAT (Proportional To Absolute Temperature) sensor readings.

Five named scenario kinds are defined in `ScenarioKind` (`src/ptat_sim/models.py`):

| Scenario                  | Description                                                     |
| ------------------------- | --------------------------------------------------------------- |
| `clean`                   | Stable readings with small random noise; the baseline case      |
| `drift`                   | Monotonic frequency drift beginning at sample 400               |
| `spike`                   | Single abrupt outlier at sample 600 on sensor S01               |
| `dropout`                 | `frequency_hz` is `None` at samples 250, 251, 252 on sensor S01 |
| `multi_sensor_divergence` | Last sensor diverges from peers starting at sample 500          |

The interface is the primary artifact.
The simulation engine implements it.
Downstream test programs and agent tasks are assigned
against the interface, not the implementation.

## Scope: Excluded

This repository does not include test programs, analysis tools,
dashboards, or live sensor integration.
Those are downstream assignments made against
the `SensorReading` interface defined here.

## Quickstart

```shell
# reset uv cache only after suspected cache corruption or strange dependency errors
# uv cache clean

uv self update
uv python pin 3.15
uv sync --extra dev --extra docs --upgrade

uvx pre-commit install

git add -A
uvx pre-commit run --all-files
# repeat if changes were made
git add -A
uvx pre-commit run --all-files

# validate MANIFEST.toml
uv run adaptive-manifest validate --strict

# generate data/*.csv from `data/data_sets.toml`
uv run ptat-sim

# do chores
uv run python -m pyright
uv run python -m pytest
uv run python -m zensical build

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

## Agent usage

Read [`SKILL.md`](SKILL.md) before generating any artifact that consumes this API.
Read [`DECISIONS.md`](DECISIONS.md) for design rationale.
Read [`AGENTS.md`](AGENTS.md) for workflow requirements.

## License

MIT © 2026 [Adaptive Interfaces](https://github.com/adaptive-interfaces)
