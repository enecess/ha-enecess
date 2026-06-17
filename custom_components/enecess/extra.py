from __future__ import annotations

import re
from typing import Any, Optional

from homeassistant.components.sensor import SensorDeviceClass

from .const import (
    CONST_ADD_MODE,
    CONST_ADD_MODE_CLOUD,
    CONST_ADD_MODE_LOCAL,
    CONST_ECOMAIN_SERIAL,
    CONST_ECOMAIN_SELECTED_SLAVES,
    CONST_EXTRA_ENTITIES,
    CONST_EXTRA_ENTITY_NAME,
    CONST_EXTRA_ENTITY_OPERATION,
    CONST_EXTRA_ENTITY_SOURCE,
    CONST_EXTRA_ENTITY_SOURCE_KIND,
    CONST_EXTRA_ENTITY_SOURCES,
    CONST_EXTRA_OPERATION_ABSOLUTE,
    CONST_EXTRA_OPERATION_AVERAGE,
    CONST_EXTRA_OPERATION_INVERT,
    CONST_EXTRA_OPERATION_SUM,
    DOMAIN,
)
from .ecomain.model import (
    EnecessSensorDescription,
    RegisterSpec,
    build_sensor_descriptions,
    build_specs_cloud,
    build_specs_local,
)

EXTRA_TRANSFORM_OPERATIONS = [CONST_EXTRA_OPERATION_INVERT, CONST_EXTRA_OPERATION_ABSOLUTE]
EXTRA_AGGREGATE_OPERATIONS = [CONST_EXTRA_OPERATION_SUM, CONST_EXTRA_OPERATION_AVERAGE]
EXTRA_SOURCE_KINDS = ["power", "energy"]


def get_entry_slaves(entry_data: dict[str, Any], entry_options: Optional[dict[str, Any]] = None) -> list[int]:
    """Return selected slaves, preferring mutable options."""
    entry_options = entry_options or {}
    return entry_options.get(CONST_ECOMAIN_SELECTED_SLAVES, entry_data.get(CONST_ECOMAIN_SELECTED_SLAVES, []))


def get_entry_extra_entities(entry_options: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Return configured extra entities from options."""
    entry_options = entry_options or {}
    extras = entry_options.get(CONST_EXTRA_ENTITIES, [])
    return list(extras) if isinstance(extras, list) else []


def build_entry_specs(entry_data: dict[str, Any], entry_options: Optional[dict[str, Any]] = None) -> list[RegisterSpec]:
    """Build EcoMain specs using mutable options where applicable."""
    slaves = get_entry_slaves(entry_data, entry_options)
    if entry_data.get(CONST_ADD_MODE) == CONST_ADD_MODE_CLOUD:
        return build_specs_cloud(slaves)
    return build_specs_local(slaves)


def build_entry_descriptions(
    entry_data: dict[str, Any],
    entry_options: Optional[dict[str, Any]] = None,
) -> list[EnecessSensorDescription]:
    """Build EcoMain sensor descriptions using mutable options."""
    return build_sensor_descriptions(build_entry_specs(entry_data, entry_options))


def sensor_unique_id(serial: str, idx: int, key: str, mode: str) -> str:
    """Build the unique id used by EcoMain sensor entities."""
    mode_key = CONST_ADD_MODE_CLOUD if mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL
    sub = f":sub_{idx}" if idx != 0 else ""
    return f"ecomain:{serial}{sub}:key_{key}:mode_{mode_key}"


def device_identifier(serial: str, idx: int, mode: str) -> tuple[str, str]:
    """Build the device identifier used by EcoMain/EcoSub devices."""
    mode_key = CONST_ADD_MODE_CLOUD if mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL
    sub = f":sub_{idx}" if idx != 0 else ""
    return DOMAIN, f"ecomain:{serial}{sub}:mode_{mode_key}"


def build_entry_device_identifiers(
    entry_data: dict[str, Any],
    entry_options: Optional[dict[str, Any]] = None,
) -> set[tuple[str, str]]:
    """Build all device identifiers expected for an entry."""
    serial = str(entry_data.get(CONST_ECOMAIN_SERIAL))
    identifiers = {device_identifier(serial, 0, str(entry_data.get(CONST_ADD_MODE)))}
    identifiers.update(
        device_identifier(serial, int(slave), str(entry_data.get(CONST_ADD_MODE)))
        for slave in get_entry_slaves(entry_data, entry_options)
    )
    return identifiers


def build_entry_sensor_unique_ids(
    entry_data: dict[str, Any],
    entry_options: Optional[dict[str, Any]] = None,
) -> set[str]:
    """Build all sensor unique ids expected for an entry."""
    serial = str(entry_data.get(CONST_ECOMAIN_SERIAL))
    mode = str(entry_data.get(CONST_ADD_MODE))
    descriptions = build_entry_descriptions(entry_data, entry_options)
    unique_ids = {
        sensor_unique_id(serial, desc.spec.device_index, desc.spec.key, mode)
        for desc in descriptions
    }
    unique_ids.update(
        sensor_unique_id(serial, extra_entity_device_index(descriptions, extra), str(extra.get("key")), mode)
        for extra in get_entry_extra_entities(entry_options)
        if extra.get("key")
    )
    return unique_ids


def extra_entity_device_index(
    descriptions: list[EnecessSensorDescription],
    extra: dict[str, Any],
) -> int:
    """Return the target EcoMain/EcoSub device index for an extra entity."""
    desc_by_key = {desc.key: desc for desc in descriptions}
    indices = {
        desc_by_key[source].spec.device_index
        for source in (extra.get("sources") or [])
        if source in desc_by_key
    }
    if len(indices) == 1:
        return next(iter(indices))
    return 0


def _description_source_kind(desc: EnecessSensorDescription) -> Optional[str]:
    if desc.device_class == SensorDeviceClass.POWER:
        return "power"
    if desc.device_class == SensorDeviceClass.ENERGY:
        return "energy"
    return None


def build_source_options(
    entry_data: dict[str, Any],
    entry_options: Optional[dict[str, Any]],
    *,
    source_kind: str,
    power_only: bool = False,
) -> dict[str, str]:
    """Return selectable source key labels for extra entities."""
    options: dict[str, str] = {}
    for desc in build_entry_descriptions(entry_data, entry_options):
        kind = _description_source_kind(desc)
        if kind is None:
            continue
        if power_only and kind != "power":
            continue
        if kind != source_kind:
            continue
        options[desc.key] = desc.name or desc.key
    return options


def find_source_description(
    descriptions: list[EnecessSensorDescription],
    source_key: str,
) -> Optional[EnecessSensorDescription]:
    """Find a source sensor description by key."""
    return next((desc for desc in descriptions if desc.key == source_key), None)


def make_extra_key(operation: str, sources: list[str], existing: list[dict[str, Any]]) -> str:
    """Create a stable extra-entity key."""
    raw = f"extra_{operation}_{'_'.join(sources)}"
    key = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
    used = {str(item.get("key")) for item in existing}
    if key not in used:
        return key

    base = key
    idx = 2
    while f"{base}_{idx}" in used:
        idx += 1
    return f"{base}_{idx}"


def normalize_extra_entity(user_input: dict[str, Any], existing: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize form input into persisted extra-entity config."""
    operation = user_input[CONST_EXTRA_ENTITY_OPERATION]
    sources = user_input.get(CONST_EXTRA_ENTITY_SOURCES) or []
    source = user_input.get(CONST_EXTRA_ENTITY_SOURCE)
    if source:
        sources = [source]
    sources = [str(item) for item in sources]

    return {
        "key": make_extra_key(operation, sources, existing),
        "name": str(user_input[CONST_EXTRA_ENTITY_NAME]).strip(),
        "operation": operation,
        "source_kind": user_input.get(CONST_EXTRA_ENTITY_SOURCE_KIND),
        "sources": sources,
    }
