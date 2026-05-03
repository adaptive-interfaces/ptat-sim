# ptat-sim

Synthetic PTAT sensor simulation engine and stable readings interface.

Part of the [Adaptive Interfaces](https://github.com/adaptive-interfaces) ecosystem.

## Scope: Included

A deterministic synthetic data generator for
PTAT (Proportional To Absolute Temperature) sensor readings.
Provides five named scenario kinds against a stable typed interface
contract:

1. clean
2. drift
3. spike
4. dropout
5. multi-sensor divergence

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
uv self update
uv python pin 3.15
uv sync --extra dev --extra docs --upgrade

uvx pre-commit install

uv run python -m ptat_sim.data_maker

git add -A
uvx pre-commit run --all-files
# repeat if changes were made
git add -A
uvx pre-commit run --all-files

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
