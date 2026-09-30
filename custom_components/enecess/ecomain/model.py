"""Build ecoMain register specifications and sensor descriptions."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)

from ..const import (
    CONF_ECOMAIN_AVAILABLE_SLAVES,
    CONF_ECOMAIN_EXTENDED_FIRMWARE_VERSION,
    CONF_SENSOR_DISPLAY_PRECISION,
)

DEFAULT_LOCAL_MEASUREMENTS = ("power", "energy_forward", "energy_reverse")
LOCAL_MEASUREMENTS = (
    *DEFAULT_LOCAL_MEASUREMENTS,
    "reactive_energy_forward",
    "reactive_energy_reverse",
    "apparent_energy",
    "apparent_power",
    "reactive_power",
    "voltage",
    "current",
    "power_factor",
    "frequency",
)
DEFAULT_CLOUD_MEASUREMENTS = ("power", "energy")
CLOUD_MEASUREMENTS = DEFAULT_CLOUD_MEASUREMENTS


def available_local_measurements(firmware_version: int | None) -> tuple[str, ...]:
    """Expose extended registers only after confirming compatible firmware."""
    if (
        firmware_version is not None
        and firmware_version >= CONF_ECOMAIN_EXTENDED_FIRMWARE_VERSION
    ):
        return LOCAL_MEASUREMENTS
    return DEFAULT_LOCAL_MEASUREMENTS


@dataclass(frozen=True)
class RegisterSpec:
    """Describe one physical register reading or derived cloud measurement."""

    key: str
    kind: str
    device_index: int
    address: int | None = None
    regs: int | None = None
    scale: float = 1.0
    source_key: str | None = None
    measurement_type: str | None = None
    signed: bool = False


@dataclass(frozen=True, kw_only=True)
class EnecessSensorDescription(SensorEntityDescription):
    """Sensor description extended with register/spec metadata."""

    spec: RegisterSpec


# Measurement: key suffix, main base, branch base, width, scale, signed, kind.
_LOCAL_LAYOUT = {
    "power": ("power_rt", 1000, 1008, 2, 0.01, True, "power"),
    "energy_forward": ("energy_fwd_total", 0, 32, 4, 0.001, False, "energy"),
    "energy_reverse": ("energy_rev_total", 16, 192, 4, 0.001, False, "energy"),
    "reactive_energy_forward": (
        "reactive_energy_fwd_total",
        352,
        384,
        4,
        0.001,
        False,
        "reactive_energy",
    ),
    "reactive_energy_reverse": (
        "reactive_energy_rev_total",
        368,
        544,
        4,
        0.001,
        False,
        "reactive_energy",
    ),
    "apparent_energy": (
        "apparent_energy_total",
        704,
        720,
        4,
        0.001,
        False,
        "apparent_energy",
    ),
    "apparent_power": ("apparent_power_rt", 900, 908, 2, 0.01, True, "apparent_power"),
    "reactive_power": (
        "reactive_power_rt",
        1100,
        1108,
        2,
        0.01,
        True,
        "reactive_power",
    ),
    "voltage": ("voltage_rt", 1200, 1209, 1, 0.01, False, "voltage"),
    "current": ("current_rt", 1201, 1210, 1, 0.01, False, "current"),
    "power_factor": ("power_factor_rt", 1202, 1211, 1, 0.01, True, "power_factor"),
}


def _slave_list(slaves: list | None) -> list[int]:
    return sorted(
        {int(s) for s in (CONF_ECOMAIN_AVAILABLE_SLAVES if slaves is None else slaves)}
    )


def build_specs_local(slaves=None, measurement_types=None) -> list[RegisterSpec]:
    """Build requested ecoMain and ecoSub registers before capability filtering."""
    selected = set(
        DEFAULT_LOCAL_MEASUREMENTS if measurement_types is None else measurement_types
    )
    specs = []
    for measurement, (
        suffix,
        main,
        branch,
        width,
        scale,
        signed,
        kind,
    ) in _LOCAL_LAYOUT.items():
        if measurement not in selected:
            continue

        # Calls finish in this iteration; the helper never escapes the loop.
        def add(prefix, address, device):
            specs.append(
                RegisterSpec(
                    key=f"{prefix}_{suffix}",  # noqa: B023
                    kind=kind,  # noqa: B023
                    device_index=device,
                    address=address,
                    regs=width,  # noqa: B023
                    scale=scale,  # noqa: B023
                    measurement_type=measurement,  # noqa: B023
                    signed=signed,  # noqa: B023
                )
            )

        step = 3 if width == 1 else width
        phases = ("l1", "l2", "l3") if width == 1 else ("l1", "l2", "l3", "all")
        for index, phase in enumerate(phases):
            add(f"main_{phase}", main + index * step, 0)
        for device in [0, *_slave_list(slaves)]:
            prefix = "main" if device == 0 else f"sub{device}"
            for channel in range(1, 11):
                add(
                    f"{prefix}_ch{channel}",
                    branch + (device * 10 + channel - 1) * step,
                    device,
                )
    if "frequency" in selected:
        specs.append(
            RegisterSpec(
                key="main_frequency_rt",
                kind="frequency",
                device_index=0,
                address=1400,
                regs=1,
                scale=0.01,
                measurement_type="frequency",
            )
        )
    return specs


def build_specs_cloud(slaves=None, measurement_types=None) -> list[RegisterSpec]:
    """Select cloud power or both delta and accumulated energy sensors."""
    selected = set(
        DEFAULT_CLOUD_MEASUREMENTS if measurement_types is None else measurement_types
    )
    specs = []
    targets = [("main_all", 0)]
    for device in [0, *_slave_list(slaves)]:
        prefix = "main" if device == 0 else f"sub{device}"
        targets.extend((f"{prefix}_ch{channel}", device) for channel in range(1, 11))
    for prefix, device in targets:
        if "power" in selected:
            specs.append(
                RegisterSpec(
                    key=f"{prefix}_power_avg_1m",
                    kind="power",
                    device_index=device,
                    measurement_type="power",
                )
            )
        if "energy" in selected:
            delta_key = f"{prefix}_energy_total_1m"
            specs.append(
                RegisterSpec(
                    key=delta_key,
                    kind="energy_delta",
                    device_index=device,
                    measurement_type="energy",
                )
            )
            specs.append(
                RegisterSpec(
                    key=f"{prefix}_energy_accumulated",
                    kind="energy_accumulated",
                    device_index=device,
                    source_key=delta_key,
                    measurement_type="energy",
                )
            )
    return specs


def build_sensor_descriptions(
    specs: list[RegisterSpec],
) -> list[EnecessSensorDescription]:
    """Convert register metadata to HA units and statistics semantics."""
    metadata = {
        "power": ("W", SensorDeviceClass.POWER),
        "energy": ("Wh", SensorDeviceClass.ENERGY),
        "energy_accumulated": ("Wh", SensorDeviceClass.ENERGY),
        "energy_delta": ("Wh", None),
        "reactive_energy": ("varh", SensorDeviceClass.REACTIVE_ENERGY),
        "apparent_energy": ("VAh", None),
        "apparent_power": ("VA", SensorDeviceClass.APPARENT_POWER),
        "reactive_power": ("var", SensorDeviceClass.REACTIVE_POWER),
        "voltage": ("V", SensorDeviceClass.VOLTAGE),
        "current": ("A", SensorDeviceClass.CURRENT),
        "power_factor": (None, SensorDeviceClass.POWER_FACTOR),
        "frequency": ("Hz", SensorDeviceClass.FREQUENCY),
    }
    descriptions = []
    for spec in specs:
        unit, device_class = metadata[spec.kind]
        state_class = SensorStateClass.MEASUREMENT
        if spec.kind in (
            "energy",
            "energy_accumulated",
            "reactive_energy",
            "apparent_energy",
        ):
            state_class = SensorStateClass.TOTAL_INCREASING
        elif spec.kind == "energy_delta":
            state_class = None
        descriptions.append(
            EnecessSensorDescription(
                key=spec.key,
                name=spec.key,
                native_unit_of_measurement=unit,
                device_class=device_class,
                state_class=state_class,
                suggested_display_precision=CONF_SENSOR_DISPLAY_PRECISION,
                spec=spec,
            )
        )
    return descriptions
