from dataclasses import dataclass
from typing import Optional

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import UnitOfEnergy, UnitOfPower

from ..const import CONF_ECOMAIN_AVAILABLE_SLAVES


@dataclass(frozen=True)
class RegisterSpec:
    key: str
    kind: str  # "power" or "energy"
    device_index: int  # 0=main, 1..3=slaves
    address: Optional[int] = None
    regs: Optional[int] = None  # 2 for int32, 4 for int64
    scale: float = 1.0


@dataclass(frozen=True, kw_only=True)
class EnecessSensorDescription(SensorEntityDescription):
    """Sensor description extended with register/spec metadata."""
    spec: RegisterSpec


# EcoMain Modbus register mapping.
_SLAVE_FWD_BASE: dict[int, int] = {1: 72, 2: 112, 3: 152}
_SLAVE_REV_BASE: dict[int, int] = {1: 232, 2: 272, 3: 312}
_SLAVE_PWR_BASE: dict[int, int] = {1: 1028, 2: 1048, 3: 1068}


def _slave_list(slaves: Optional[list]) -> list[int]:
    if slaves is None:
        return [int(s) for s in CONF_ECOMAIN_AVAILABLE_SLAVES]
    return sorted({int(s) for s in slaves})


def build_specs_local(slaves: Optional[list] = None) -> list[RegisterSpec]:
    """Build RegisterSpec list for local Modbus mode."""
    specs: list[RegisterSpec] = []
    slave_indices = CONF_ECOMAIN_AVAILABLE_SLAVES if slaves is None else slaves

    def add_energy(key: str, addr: int, device_index: int) -> None:
        specs.append(RegisterSpec(key=key, address=addr, regs=4, scale=0.001, kind="energy", device_index=device_index))

    def add_power(key: str, addr: int, device_index: int) -> None:
        specs.append(RegisterSpec(key=key, address=addr, regs=2, scale=0.01, kind="power", device_index=device_index))

    # Host main power
    add_power("main_l1_power_rt", 1000, 0)
    add_power("main_l2_power_rt", 1002, 0)
    add_power("main_l3_power_rt", 1004, 0)
    add_power("main_all_power_rt", 1006, 0)
    # Host main energy (forward)
    add_energy("main_l1_energy_fwd_total", 0, 0)
    add_energy("main_l2_energy_fwd_total", 4, 0)
    add_energy("main_l3_energy_fwd_total", 8, 0)
    add_energy("main_all_energy_fwd_total", 12, 0)
    # Host main energy (rev)
    add_energy("main_l1_energy_rev_total", 16, 0)
    add_energy("main_l2_energy_rev_total", 20, 0)
    add_energy("main_l3_energy_rev_total", 24, 0)
    add_energy("main_all_energy_rev_total", 28, 0)

    # Host branch
    for ch in range(1, 11):
        add_power(f"main_ch{ch}_power_rt", 1008 + (ch - 1) * 2, 0)
        add_energy(f"main_ch{ch}_energy_fwd_total", 32 + (ch - 1) * 4, 0)
        add_energy(f"main_ch{ch}_energy_rev_total", 192 + (ch - 1) * 4, 0)

    # Slave branch
    for s, ch in ((s, ch) for s in slave_indices for ch in range(1, 11)):
        base_pwr = _SLAVE_PWR_BASE[s]
        base_fwd = _SLAVE_FWD_BASE[s]
        base_rev = _SLAVE_REV_BASE[s]
        add_power(f"sub{s}_ch{ch}_power_rt", base_pwr + (ch - 1) * 2, s)
        add_energy(f"sub{s}_ch{ch}_energy_fwd_total", base_fwd + (ch - 1) * 4, s)
        add_energy(f"sub{s}_ch{ch}_energy_rev_total", base_rev + (ch - 1) * 4, s)

    return specs


def build_specs_cloud(slaves: Optional[list[int]] = None) -> list[RegisterSpec]:
    """Build RegisterSpec list for cloud mode (no Modbus addresses, only key/kind/device)."""
    specs: list[RegisterSpec] = []
    slave_indices = CONF_ECOMAIN_AVAILABLE_SLAVES if slaves is None else slaves

    def add_power(key: str, device_index: int) -> None:
        specs.append(RegisterSpec(key=key, kind="power", device_index=device_index))

    def add_energy(key: str, device_index: int) -> None:
        specs.append(RegisterSpec(key=key, kind="energy", device_index=device_index))

    add_power("main_all_power_avg_1m", 0)
    add_energy("main_all_energy_total_1m", 0)
    for ch in range(1, 11):
        add_power(f"main_ch{ch}_power_avg_1m", 0)
        add_energy(f"main_ch{ch}_energy_total_1m", 0)
    for s, ch in ((s, ch) for s in slave_indices for ch in range(1, 11)):
        add_power(f"sub{s}_ch{ch}_power_avg_1m", s)
        add_energy(f"sub{s}_ch{ch}_energy_total_1m", s)
    return specs


def build_sensor_descriptions(specs: list[RegisterSpec]) -> list[EnecessSensorDescription]:
    """Convert RegisterSpecs to HA SensorEntityDescriptions."""
    unit_map = {
        "power": UnitOfPower.WATT,
        "energy": UnitOfEnergy.WATT_HOUR,
    }
    descs: list[EnecessSensorDescription] = []
    for spec in specs:
        descs.append(
            EnecessSensorDescription(
                key=spec.key,
                name=spec.key,
                native_unit_of_measurement=unit_map.get(spec.kind),
                spec=spec,
            )
        )
    return descs
