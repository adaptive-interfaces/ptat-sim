# ptat-sim

Synthetic PTAT sensor simulation engine and stable readings interface.

Part of the [Adaptive Interfaces](https://github.com/adaptive-interfaces) ecosystem.

## Contents

- [Glossary](glossary.md) - key terms for PTAT sensor data and this simulation engine
- [API Reference](api.md) - auto-generated from `src/ptat_sim/` docstrings

## What This Is

PTAT (Proportional To Absolute Temperature) circuits produce an output signal
that scales linearly with absolute temperature in Kelvin.
They appear in CPUs, power electronics, battery management systems,
and industrial thermal monitoring equipment.

In production systems, engineers watch streams of PTAT readings over time.
A single reading is rarely meaningful.
The shape of the stream is what matters:
slow drift, sudden spikes, sensor dropout, or divergence between sensors
are the signals that indicate problems before they become failures.

`ptat-sim` provides a deterministic engine that generates realistic PTAT reading streams
for each of those conditions.
It exists so that test programs and agent-assigned tasks can be built against
a stable, typed interface contract rather than a live sensor system.

## Scenario Kinds

Five named scenario kinds are defined in `ScenarioKind` (`src/ptat_sim/models.py`):

| Scenario | Description |
| -------- | ----------- |
| `clean` | Stable readings with small random noise; the baseline case |
| `drift` | Monotonic frequency drift beginning at sample 400 |
| `spike` | Single abrupt outlier at sample 600 on sensor S01 |
| `dropout` | `frequency_hz` is `None` at samples 250, 251, 252 on sensor S01 |
| `multi_sensor_divergence` | Last sensor diverges from peers starting at sample 500 |

## Quick Example

```python
from ptat_sim.generator import generate_batch
from ptat_sim.models import GeneratorConfig

readings = generate_batch(scenario="drift", config=GeneratorConfig(seed=42))

for r in readings:
    if r.frequency_hz is None:
        continue  # dropout; handle explicitly
    print(r.sensor_id, r.sample_index, r.temperature_celsius, r.frequency_hz)
```

## Repository

- [Repository](https://github.com/adaptive-interfaces/ptat-sim)
- [`SKILL.md`](https://github.com/adaptive-interfaces/ptat-sim/blob/main/SKILL.md) -
  agent operating guide
- [`DECISIONS.md`](https://github.com/adaptive-interfaces/ptat-sim/blob/main/DECISIONS.md) -
  design rationale
- [`AGENTS.md`](https://github.com/adaptive-interfaces/ptat-sim/blob/main/AGENTS.md) -
  workflow requirements
