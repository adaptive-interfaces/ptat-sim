# SKILL.md (ptat-sim)

Agent operating guide for the PTAT sensor simulation engine and readings interface.

This skill operates under the
[Adaptive Conformance Specification (ACS)](https://github.com/adaptive-interfaces/adaptive-conformance-specification).
Apply ACS discovery and conformance steps before executing any domain-specific actions below.

---

## Motivation

PTAT (Proportional To Absolute Temperature) circuits produce a signal
linearly proportional to absolute temperature in Kelvin.
In monitoring systems a stream of readings is watched for anomalies and trends,
not individual values.

This engine provides deterministic, inspectable reading streams so that
test programs and agent-assigned tasks can be built against a stable interface
rather than a live sensor system.

---

## Scope

### Included

- The `SensorReading` interface contract and its invariants
- The five named `ScenarioKind` values and their behavioral specifications
- `GeneratorConfig` parameters and their effect on output
- `ProcessorConfig` parameters and their role in anomaly detection
- All public functions: `generate_batch`, `analyze_batch`, and the five `detect_*` functions
- Operating rules an agent must follow when using this API
- Test coverage requirements
- Failure modes and stopping conditions

### Excluded

- Implementation details of `generator.py` internals
- CSV output and `data_maker.py`; use directly, not through this skill
- Visualization or dashboard tooling
- Live sensor integration or hardware interfaces

---

## The PTAT Physics

The ideal PTAT frequency relationship is:

```text
frequency_hz = nominal_frequency_at_25c_hz
             + sensitivity_hz_per_kelvin * (temperature_celsius - 25.0)
```

Real readings add per-sensor bias (stable offset, uniform in `[-4, 4]` Hz)
and Gaussian noise (`noise_stddev_hz`).
Anomalies are additive deviations on top of this noisy baseline.
Understanding this relationship is required to correctly interpret
whether a frequency deviation is anomalous or within expected noise bounds.

---

## Interface Contract

### `ScenarioKind`

Five valid literals. No others are accepted.

| Value | Behavioral contract |
| ----- | ------------------- |
| `"clean"` | Stable readings with small Gaussian noise. Baseline case. |
| `"drift"` | Monotonic frequency drift begins at `sample_index == 400`. Rate: 1.5 Hz per sample. |
| `"spike"` | Single outlier injected at `sample_index == 600` on sensor `S01`. Magnitude: +500 Hz. |
| `"dropout"` | `frequency_hz` is `None` at indices 250, 251, 252 on sensor `S01`. |
| `"multi_sensor_divergence"` | Last sensor diverges from peers at `sample_index == 500`. Rate: 1.2 Hz per sample. Requires `num_sensors >= 2`. |

### `SensorReading`

A single PTAT-style sensor reading. Frozen dataclass.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `sample_index` | `int` | Position within the batch, 0-based |
| `sensor_id` | `str` | Stable sensor identifier, e.g. `S01`, `S02` |
| `temperature_celsius` | `float` | Computed temperature at this sample |
| `frequency_hz` | `float \| None` | PTAT output frequency; `None` signals a dropout |

**Critical invariant:** `frequency_hz: None` is a dropout event, not missing data.
Handle it explicitly. Do not skip, impute, or treat as zero.

### `GeneratorConfig`

All fields have defaults. Override only what the scenario requires.

| Field | Default | Description |
| ----- | ------- | ----------- |
| `batch_size` | `1000` | Number of samples per sensor |
| `num_sensors` | `1` | Number of sensors in the batch |
| `sampling_rate_hz` | `10` | Samples per second |
| `base_temperature_celsius` | `25.0` | Starting temperature |
| `temperature_step_celsius` | `0.02` | Per-sample temperature increment |
| `nominal_frequency_at_25c_hz` | `100000.0` | PTAT output at 25°C reference point |
| `sensitivity_hz_per_kelvin` | `512.0` | Frequency change per degree |
| `noise_stddev_hz` | `8.0` | Gaussian noise standard deviation |
| `seed` | `42` | RNG seed; same seed produces identical output |

### `ProcessorConfig`

Thresholds and windows used by the anomaly detector.

| Field | Default | Role |
| ----- | ------- | ---- |
| `spike_relative_threshold` | `0.0000002` | Relative frequency deviation to flag a spike |
| `divergence_relative_threshold` | `0.00000002` | Relative deviation to flag sensor divergence |
| `drift_offset_percent` | `2.0` | Percent offset between windows to flag drift |
| `baseline_window` | `100` | Samples used to establish baseline |
| `comparison_window` | `100` | Samples compared against baseline |
| `early_window` | `100` | Early-batch window for trend comparison |
| `late_window` | `100` | Late-batch window for trend comparison |

### `AnomalyFinding`

A single anomaly result. Frozen dataclass.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `sensor_id` | `str` | Which sensor produced this finding |
| `kind` | `str` | One of: `dropout`, `spike`, `drift`, `divergence`, `suspicious_trend` |
| `start_sample` | `int` | First sample index of the anomaly window |
| `end_sample` | `int` | Last sample index of the anomaly window |
| `message` | `str` | Human-readable description with numeric detail |
| `severity` | `str` | One of: `high`, `medium`, `low` |

### `BatchResult`

Aggregated result from `analyze_batch()`.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `total_readings` | `int` | Total reading count across all sensors |
| `sensors` | `tuple[str, ...]` | Sensor IDs present in the batch, sorted |
| `findings` | `tuple[AnomalyFinding, ...]` | All findings from this batch |
| `has_findings` | `bool` (property) | `True` when `findings` is non-empty |

---

## Public Functions

### `generate_batch(scenario, config)`

```python
from ptat_sim.generator import generate_batch
from ptat_sim.models import GeneratorConfig

readings = generate_batch(scenario="drift", config=GeneratorConfig(seed=42))
```

Returns `list[SensorReading]`.
Always provide an explicit `seed` in tests that assert specific values.

### `analyze_batch(readings, config)`

```python
from ptat_sim.processor import analyze_batch
from ptat_sim.models import ProcessorConfig

result = analyze_batch(readings, config=ProcessorConfig())
```

Returns `BatchResult`.
Runs all five detectors: dropout, spike, drift, divergence, suspicious_trend.
This is the only authoritative source for anomaly claims.

### Individual detectors

Available for targeted use when only one anomaly type is relevant:

```python
from ptat_sim.processor import (
    detect_dropouts,
    detect_spikes,
    detect_drift,
    detect_divergence,
    detect_suspicious_trend,
)
```

`detect_divergence` takes `grouped: dict[str, list[SensorReading]]`, not a flat list.
Use `analyze_batch` unless you have a specific reason to call detectors individually.

---

## Operating Rules

**R-01. Always specify `ScenarioKind` explicitly.**
Never infer scenario from config values alone.
The scenario argument is the ground truth for what the batch contains.

**R-02. Treat `frequency_hz: None` as a dropout, not absent data.**
Do not skip these readings. Do not impute. Record them as dropout events.
A count of `None` values is a required output of dropout scenario tests.

**R-03. Do not claim drift detection without `detect_drift` or `analyze_batch`.**
Drift is not detectable from a single reading or visual inspection.
Detection requires comparing a baseline window to a later window using
`ProcessorConfig.baseline_window` and `comparison_window`.
The `drift_offset_percent` threshold is the decision boundary.

**R-04. `multi_sensor_divergence` requires `num_sensors >= 2`.**
Validate before invoking. A single-sensor config raises `ValueError`.

**R-05. Do not overclaim anomaly detection without running the processor.**
Anomaly findings come from `analyze_batch` or the `detect_*` functions.
Do not infer anomalies from raw `frequency_hz` values.
If `BatchResult.has_findings` is `False`, report no anomalies.

**R-06. Use `seed` for reproducibility in test assertions.**
Any test that asserts specific frequency values or finding counts must use
an explicit `seed`. Default `seed=42` is acceptable for nominal cases.
Do not assert exact values from runs with different seeds.

**R-07. Nominal test cases must include `"clean"` scenario.**
The clean scenario is the baseline.
A test suite without it cannot establish whether anomaly detection
is producing false positives.

**R-08. Boundary test cases must include `"dropout"`.**
`None` handling is the most common source of consumer bugs.
Every test suite must exercise it explicitly.

**R-09. `suspicious_trend` is distinct from `drift`.**
`detect_suspicious_trend` detects monotonic directional change
that remains within drift bounds.
It explicitly returns nothing when drift is already detected,
to avoid double-classification.
Do not conflate the two in test assertions.

---

## Test Coverage Requirements

A conforming test suite includes at minimum:

| Case type | Required scenarios |
| --------- | ------------------ |
| Nominal | `clean` with default config |
| Drift | `drift` with finding count assertion |
| Spike | `spike` with finding count assertion |
| Dropout | `dropout` with `None` count assertion |
| Multi-sensor | `multi_sensor_divergence`, `num_sensors=3` |
| Boundary | `batch_size=1`; invalid `ScenarioKind` string |
| Cross-run | Same seed, same config produces identical output |
| False positive | `clean` produces no findings from `analyze_batch` |

---

## Failure Modes and Stopping Conditions

Stop and report if any of the following are true:

- A `ScenarioKind` value is not one of the five valid literals
- `multi_sensor_divergence` is requested with `num_sensors < 2`
- A consumer treats `frequency_hz: None` as `0.0` or filters it silently
- Anomaly claims are made without running a detector or `analyze_batch`
- Test assertions use hardcoded frequency values without a fixed `seed`
- `suspicious_trend` and `drift` findings are treated as the same anomaly type

Do not proceed to test generation until the interface contract above has been
read and the operating rules are confirmed understood.

---

## Invocation

Skills that require synthetic PTAT data include this in their preamble:

> This skill uses `ptat-sim` for sensor data generation.
> Read `ptat-sim/SKILL.md` and apply all operating rules before
> generating any test artifacts or anomaly claims.

---

## Repository Contents

```text
ptat-sim/
  SKILL.md              this document
  DECISIONS.md          design history and rationale
  MANIFEST.toml         repository declaration
  AGENTS.md             workflow requirements
  CLAUDE.md             behavioral constraints for AI collaborators
  src/ptat_sim/
    models.py           interface contract (source of truth)
    generator.py        scenario implementations
    processor.py        anomaly detection
    data_maker.py       TOML-driven CSV batch generation
    cli.py              CLI entry point
  data/
    data_sets.toml      batch generation config
  tests/
```

---

*License: MIT © 2026 [Adaptive Interfaces](https://github.com/adaptive-interfaces)*
