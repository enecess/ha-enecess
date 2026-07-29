from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any


@dataclass(frozen=True)
class EcoPlugConfig:
    hardware_number: str
    name: str


@dataclass(frozen=True)
class EcoPlugSnapshot:
    power_rt: float | None = None
    energy_total: float | None = None
    is_on: bool | None = None
    data_error: str | None = None
    state_error: str | None = None


def normalize_plug(plug: dict[str, Any]) -> dict[str, str] | None:
    """Return the persisted EcoPlug fields, or None for an invalid serial."""
    hardware_number = plug.get("hardware_number")
    if not isinstance(hardware_number, str) or not hardware_number.strip():
        return None

    name = plug.get("name")
    return {
        "name": name.strip() if isinstance(name, str) else "",
        "hardware_number": hardware_number.strip(),
    }


def build_plug_options(plugs: list[dict[str, Any]]) -> dict[str, str]:
    """Build serial-to-label options from valid cloud hardware records."""
    options: dict[str, str] = {}
    for plug in plugs:
        normalized = normalize_plug(plug)
        if normalized is None:
            continue
        serial = normalized["hardware_number"]
        if serial in options:
            continue
        name = normalized["name"]
        options[serial] = f"{name}（{serial}）" if name else serial
    return options


def select_plugs(
    plugs: list[dict[str, Any]], selected_hardware_numbers: list[str]
) -> list[dict[str, str]]:
    """Persist selected plugs once each, preserving cloud-list order."""
    selected = set(selected_hardware_numbers)
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for plug in plugs:
        normalized = normalize_plug(plug)
        if normalized is None:
            continue
        serial = normalized["hardware_number"]
        if serial not in selected or serial in seen:
            continue
        seen.add(serial)
        result.append(normalized)
    return result


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_non_negative_finite(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    return parsed


def parse_latest_plug_data(payload: Any) -> tuple[float | None, float | None]:
    """Return power and total energy from an EcoPlug data payload."""
    if not isinstance(payload, dict):
        return None, None
    samples = payload.get("data")
    if not isinstance(samples, list):
        return None, None

    latest_sample: dict[str, Any] | None = None
    latest_time: datetime | None = None
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        sample_time = _parse_timestamp(sample.get("time"))
        if sample_time is None:
            continue
        if latest_time is None or sample_time > latest_time:
            latest_time = sample_time
            latest_sample = sample

    if latest_sample is None:
        return None, None
    return (
        _parse_non_negative_finite(latest_sample.get("power")),
        _parse_non_negative_finite(latest_sample.get("total_energy")),
    )


def parse_plug_is_on(response: Any) -> bool | None:
    """Parse property 106 from a plug configuration response."""
    if not isinstance(response, dict):
        return None
    response_data = response.get("response")
    if not isinstance(response_data, dict):
        return None
    data = response_data.get("data")
    if not isinstance(data, dict):
        return None
    properties = data.get("p")
    if not isinstance(properties, list):
        return None

    for item in properties:
        if not isinstance(item, dict) or item.get("id") != 106:
            continue
        value = item.get("val")
        if isinstance(value, bool):
            return None
        if value in (0, "0"):
            return False
        if value in (1, "1"):
            return True
        return None
    return None


def device_identifier(hardware_number: str) -> tuple[str, str]:
    return "enecess", f"ecoplug:{hardware_number}:mode_cloud"


def sensor_unique_id(hardware_number: str, sensor_key: str) -> str:
    return f"ecoplug:{hardware_number}:key_{sensor_key}:mode_cloud"


def switch_unique_id(hardware_number: str) -> str:
    return f"ecoplug:{hardware_number}:switch:mode_cloud"
