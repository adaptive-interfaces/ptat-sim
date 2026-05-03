"""processor.py: PTAT sensor anomaly analysis utilities.

This module provides simple, inspectable anomaly detection for
synthetic PTAT sensor data. It is intentionally explicit rather
than optimized so that generated reasoning remains auditable.
"""

from __future__ import annotations

from statistics import mean

from ptat_sim.models import (
    AnomalyFinding,
    BatchResult,
    ProcessorConfig,
    SensorReading,
)


def _group_by_sensor(
    readings: list[SensorReading],
) -> dict[str, list[SensorReading]]:
    """Group readings by sensor identifier."""
    grouped: dict[str, list[SensorReading]] = {}
    for reading in readings:
        grouped.setdefault(reading.sensor_id, []).append(reading)
    for sensor_id in grouped:
        grouped[sensor_id].sort(key=lambda item: item.sample_index)
    return grouped


def _non_null_frequencies(readings: list[SensorReading]) -> list[float]:
    """Return frequency values excluding null readings."""
    return [
        reading.frequency_hz for reading in readings if reading.frequency_hz is not None
    ]


def detect_dropouts(readings: list[SensorReading]) -> list[AnomalyFinding]:
    """Detect null or zero-valued readings."""
    findings: list[AnomalyFinding] = []

    for reading in readings:
        if reading.frequency_hz is None or reading.frequency_hz == 0.0:
            findings.append(
                AnomalyFinding(
                    sensor_id=reading.sensor_id,
                    kind="dropout",
                    start_sample=reading.sample_index,
                    end_sample=reading.sample_index,
                    message="Sensor reported null or zero frequency.",
                    severity="high",
                )
            )

    return findings


def detect_spikes(
    readings: list[SensorReading],
    config: ProcessorConfig,
) -> list[AnomalyFinding]:
    """Detect abrupt single-sample spikes using local context."""
    findings: list[AnomalyFinding] = []

    if len(readings) < 3:
        return findings

    for i in range(1, len(readings) - 1):
        current = readings[i].frequency_hz
        prev = readings[i - 1].frequency_hz
        nxt = readings[i + 1].frequency_hz

        if current is None or prev is None or nxt is None:
            continue

        local_mean = (prev + nxt) / 2.0
        if local_mean == 0:
            continue

        delta = abs(current - local_mean)
        ratio = delta / abs(local_mean)

        if ratio > config.spike_relative_threshold:
            findings.append(
                AnomalyFinding(
                    sensor_id=readings[i].sensor_id,
                    kind="spike",
                    start_sample=readings[i].sample_index,
                    end_sample=readings[i].sample_index,
                    message=(
                        "Single-sample spike detected "
                        f"(delta={delta:.2f} Hz, ratio={ratio:.6f})."
                    ),
                    severity="high",
                )
            )

    return findings


def detect_drift(
    readings: list[SensorReading],
    config: ProcessorConfig,
) -> list[AnomalyFinding]:
    """Detect sustained deviation from an early baseline."""
    values = _non_null_frequencies(readings)
    if len(values) < config.baseline_window + config.comparison_window:
        return []

    baseline = mean(values[: config.baseline_window])
    threshold = baseline * (config.drift_offset_percent / 100.0)

    findings: list[AnomalyFinding] = []

    for start_index in range(
        config.baseline_window,
        len(values) - config.comparison_window + 1,
    ):
        window = values[start_index : start_index + config.comparison_window]
        window_mean = mean(window)

        offset = window_mean - baseline
        offset_pct = abs(offset) / baseline * 100.0

        if abs(offset) > threshold:
            findings.append(
                AnomalyFinding(
                    sensor_id=readings[0].sensor_id,
                    kind="drift",
                    start_sample=start_index,
                    end_sample=start_index + config.comparison_window - 1,
                    message=(
                        "Sustained deviation from calibrated baseline exceeds "
                        f"{config.drift_offset_percent:.1f}% "
                        f"(offset={offset:.2f} Hz, {offset_pct:.1f}%)."
                    ),
                    severity="medium",
                )
            )
            break

    return findings


def detect_divergence(
    grouped: dict[str, list[SensorReading]],
    config: ProcessorConfig,
) -> list[AnomalyFinding]:
    """Detect per-sample divergence between sensors."""
    findings: list[AnomalyFinding] = []

    if not grouped:
        return findings

    sample_count = min(len(v) for v in grouped.values())

    for i in range(sample_count):
        values: list[float] = []
        sensors: list[str] = []

        for sensor_id, readings in grouped.items():
            v = readings[i].frequency_hz
            if v is not None:
                values.append(v)
                sensors.append(sensor_id)

        if len(values) < 2:
            continue

        avg = mean(values)
        if avg == 0:
            continue

        # --- KEY FIX: compute max deviation first ---
        max_ratio = max(abs(v - avg) / abs(avg) for v in values)

        # --- KEY FIX: gate on group-level divergence ---
        if max_ratio > config.divergence_relative_threshold:
            for sensor_id, v in zip(sensors, values, strict=False):
                if abs(v - avg) / abs(avg) > config.divergence_relative_threshold:
                    findings.append(
                        AnomalyFinding(
                            sensor_id=sensor_id,
                            kind="divergence",
                            start_sample=i,
                            end_sample=i,
                            message="Sensor diverges from peer group.",
                            severity="medium",
                        )
                    )

    return findings


def detect_suspicious_trend(
    readings: list[SensorReading],
    config: ProcessorConfig,
) -> list[AnomalyFinding]:
    """Detect monotonic directional change that may remain within drift bounds."""
    values = _non_null_frequencies(readings)
    if len(values) < config.early_window + config.late_window:
        return []

    early_mean = mean(values[: config.early_window])
    late_mean = mean(values[-config.late_window :])

    if early_mean == 0:
        return []

    difference = late_mean - early_mean
    ratio = difference / abs(early_mean)

    if ratio <= 0:
        return []

    # --- KEY FIX: respect drift threshold to avoid double-classifying drift ---
    drift_threshold_ratio = config.drift_offset_percent / 100.0

    if ratio >= drift_threshold_ratio:
        return []

    return [
        AnomalyFinding(
            sensor_id=readings[0].sensor_id,
            kind="suspicious_trend",
            start_sample=len(values) - config.late_window,
            end_sample=len(values) - 1,
            message=(
                "Late-window mean exceeds early-window mean within drift tolerance "
                f"(delta={difference:.2f} Hz, ratio={ratio:.6f})."
            ),
            severity="low",
        )
    ]


def analyze_batch(
    readings: list[SensorReading],
    config: ProcessorConfig | None = None,
) -> BatchResult:
    """Run all supported anomaly checks over a batch."""
    if config is None:
        config = ProcessorConfig()

    grouped = _group_by_sensor(readings)
    findings: list[AnomalyFinding] = []

    findings.extend(detect_divergence(grouped, config))

    for _sensor_id, sensor_readings in grouped.items():
        findings.extend(detect_dropouts(sensor_readings))
        findings.extend(detect_spikes(sensor_readings, config))
        findings.extend(detect_drift(sensor_readings, config))
        findings.extend(detect_suspicious_trend(sensor_readings, config))

    return BatchResult(
        total_readings=len(readings),
        sensors=tuple(sorted(grouped.keys())),
        findings=tuple(findings),
    )
