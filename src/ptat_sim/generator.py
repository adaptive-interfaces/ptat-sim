"""generator.py: Synthetic PTAT sensor batch generator.

This module generates deterministic or noisy PTAT-like sensor data
for evaluation scenarios including clean runs, drift, spikes,
dropouts, and cross-sensor divergence.
"""

from random import Random

from ptat_sim.models import GeneratorConfig, ScenarioKind, SensorReading


def _ptat_frequency_hz(
    temperature_celsius: float,
    nominal_frequency_at_25c_hz: float,
    sensitivity_hz_per_kelvin: float,
) -> float:
    """Return the ideal PTAT frequency for a given temperature."""
    return nominal_frequency_at_25c_hz + (
        sensitivity_hz_per_kelvin * (temperature_celsius - 25.0)
    )


def _sensor_name(index: int) -> str:
    """Return a stable sensor identifier."""
    return f"S{index + 1:02d}"


def generate_batch(
    scenario: ScenarioKind,
    config: GeneratorConfig | None = None,
) -> list[SensorReading]:
    """Generate a synthetic PTAT sensor batch for a named scenario.

    Scenarios:
        clean:
            Stable PTAT readings with small random noise.
        drift:
            Sustained monotonic drift begins near sample 400.
        spike:
            One abrupt outlier is injected.
        dropout:
            A small number of readings become null.
        multi_sensor_divergence:
            Multiple correlated sensors where one diverges from peers.
    """
    cfg = config if config is not None else GeneratorConfig()
    rng = Random(cfg.seed)

    readings: list[SensorReading] = []

    for sensor_index in range(cfg.num_sensors):
        sensor_id = _sensor_name(sensor_index)
        sensor_bias_hz = rng.uniform(-4.0, 4.0)

        for sample_index in range(cfg.batch_size):
            temperature_celsius = cfg.base_temperature_celsius + (
                sample_index * cfg.temperature_step_celsius
            )

            ideal_frequency_hz = _ptat_frequency_hz(
                temperature_celsius=temperature_celsius,
                nominal_frequency_at_25c_hz=cfg.nominal_frequency_at_25c_hz,
                sensitivity_hz_per_kelvin=cfg.sensitivity_hz_per_kelvin,
            )

            noisy_frequency_hz = (
                ideal_frequency_hz
                + sensor_bias_hz
                + rng.gauss(0.0, cfg.noise_stddev_hz)
            )

            frequency_hz: float | None = noisy_frequency_hz

            if scenario == "drift":
                if sample_index >= 400:
                    drift_amount_hz = (sample_index - 399) * 1.5
                    frequency_hz = noisy_frequency_hz + drift_amount_hz

            elif scenario == "spike":
                if sensor_index == 0 and sample_index == 600:
                    frequency_hz = noisy_frequency_hz + 500.0

            elif scenario == "dropout":
                if sensor_index == 0 and sample_index in {250, 251, 252}:
                    frequency_hz = None

            elif scenario == "multi_sensor_divergence":
                if cfg.num_sensors < 2:
                    raise ValueError(
                        "multi_sensor_divergence requires num_sensors >= 2"
                    )
                if sensor_index == cfg.num_sensors - 1 and sample_index >= 500:
                    divergence_amount_hz = (sample_index - 499) * 1.2
                    frequency_hz = noisy_frequency_hz + divergence_amount_hz

            elif scenario == "clean":
                pass

            else:
                raise ValueError(f"Unsupported scenario: {scenario}")

            readings.append(
                SensorReading(
                    sample_index=sample_index,
                    sensor_id=sensor_id,
                    temperature_celsius=temperature_celsius,
                    frequency_hz=frequency_hz,
                )
            )

    return readings
