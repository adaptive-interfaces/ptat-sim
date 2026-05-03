# Glossary (ptat-sim)

Key terms for understanding PTAT sensor data and this simulation engine.

---

## PTAT

Proportional To Absolute Temperature.
A circuit or signal whose output scales linearly with temperature in Kelvin.
The relationship is:

```text
frequency_hz = nominal_frequency_at_25c_hz
             + sensitivity_hz_per_kelvin * (temperature_celsius - 25.0)
```

Real readings add per-sensor bias and Gaussian noise on top of this ideal value.

## CTAT

Complementary To Absolute Temperature.
A signal that decreases as temperature increases.
PTAT and CTAT signals are combined in bandgap reference circuits
to produce a stable voltage independent of temperature.
`ptat-sim` models PTAT only.

## Bandgap Reference Circuit

A circuit that combines a PTAT signal and a CTAT signal to produce
a stable output voltage independent of temperature.
The PTAT component increases with temperature at the same rate
the CTAT component decreases, so the sum remains constant.
Used in virtually all analog ICs as a stable voltage reference.
`ptat-sim` models the PTAT component only;
the bandgap combination is outside its scope.

## Frequency Output

Real PTAT circuits often convert temperature to a frequency output
via a voltage-controlled oscillator.
`ptat-sim` models this directly.
`frequency_hz` is the primary signal, not temperature alone.
Temperature is computed and carried alongside for reference.

## SensorReading

A single timestamped observation from one sensor.
Fields: `sample_index`, `sensor_id`, `temperature_celsius`, `frequency_hz`.
`frequency_hz` may be `None`; see Dropout.

## ScenarioKind

One of five named scenario types that define the behavioral contract
for a generated batch.
Values: `clean`, `drift`, `spike`, `dropout`, `multi_sensor_divergence`.
Defined as a `Literal` type in `src/ptat_sim/models.py`.

## Clean

Stable readings with small random Gaussian noise around the ideal PTAT curve.
The baseline scenario.
Used to establish whether anomaly detection produces false positives.

## Drift

A slow, monotonic deviation from the expected frequency curve.
In `ptat-sim`, drift begins at `sample_index == 400` and increases linearly.
In production systems, drift indicates sensor aging, calibration loss,
or sustained thermal load changes.

## Spike

A sudden, large deviation at a single sample that returns to baseline.
In `ptat-sim`, one spike is injected at `sample_index == 600` on sensor S01.
In production systems, spikes may indicate electrical interference,
transient thermal events, or ADC glitches.

## Dropout

A reading where `frequency_hz` is `None`.
Indicates the sensor or its connection failed to produce a valid output.
`None` is a signal, not missing data.
It must be handled explicitly; do not skip, impute, or treat as zero.
In `ptat-sim`, dropout occurs at samples 250, 251, 252 on sensor S01.

## Multi-Sensor Divergence

A condition where one sensor in a group deviates from its peers.
In `ptat-sim`, the last sensor diverges starting at `sample_index == 500`.
In production systems, divergence between sensors on the same thermal mass
indicates a failed sensor, a loose connection, or a localized thermal anomaly.

## GeneratorConfig

Configuration dataclass controlling all aspects of batch generation:
batch size, number of sensors, sampling rate, temperature parameters,
frequency parameters, noise level, and random seed.
All fields have defaults.
Same seed and config always produce identical output.

## ProcessorConfig

Configuration dataclass controlling anomaly detection thresholds and windows:
spike threshold, divergence threshold, drift offset percentage,
and baseline, comparison, early, and late window sizes.
The processor uses these to decide whether a deviation is anomalous.

## BatchResult

The structured output of processing one batch.
Contains total reading count, sensor IDs, and a tuple of `AnomalyFinding` objects.
`has_findings` is `True` when any anomaly was detected.
Anomaly claims must come from `BatchResult`; do not infer from raw readings.

## Sensor Bias

A stable per-sensor frequency offset drawn uniformly from `[-4, 4]` Hz at generation time.
Represents manufacturing variation between sensors.
Consistent within a batch for a given seed.
