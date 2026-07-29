from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    CONST_DEVICE_ECOPLUG,
    CONST_DEVICE_TYPE,
    CONST_ECOPLUG_DEVICES,
    DOMAIN,
)
from .extra import (
    build_entry_device_identifiers,
    build_entry_sensor_unique_ids,
)


def async_remove_unconfigured_registry_entries(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    data: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> None:
    """Remove stale registry entries for the configured device type."""
    entry_data = entry.data if data is None else data
    entry_options = entry.options if options is None else options
    device_type = entry_data.get(CONST_DEVICE_TYPE)
    if device_type == CONST_DEVICE_ECOPLUG:
        from .ecoplug.model import (
            device_identifier,
            sensor_unique_id,
            switch_unique_id,
        )

        serials = [
            str(device["hardware_number"])
            for device in entry_data.get(CONST_ECOPLUG_DEVICES, [])
        ]
        expected_unique_ids = {
            unique_id
            for serial in serials
            for unique_id in (
                sensor_unique_id(serial, "power_rt"),
                sensor_unique_id(serial, "energy_total"),
                switch_unique_id(serial),
            )
        }
        expected_identifiers = {device_identifier(serial) for serial in serials}
        prefix = "ecoplug:"
        entity_domains = (Platform.SENSOR, Platform.SWITCH)
    else:
        expected_unique_ids = build_entry_sensor_unique_ids(
            entry_data,
            entry_options,
        )
        expected_identifiers = build_entry_device_identifiers(
            entry_data,
            entry_options,
        )
        prefix = "ecomain:"
        entity_domains = (Platform.SENSOR,)

    entity_registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(
        entity_registry,
        entry.entry_id,
    ):
        if entity_entry.domain not in entity_domains:
            continue
        unique_id = str(entity_entry.unique_id)
        if unique_id.startswith(prefix) and unique_id not in expected_unique_ids:
            entity_registry.async_remove(entity_entry.entity_id)

    device_registry = dr.async_get(hass)
    for device_entry in dr.async_entries_for_config_entry(
        device_registry,
        entry.entry_id,
    ):
        if not any(
            identifier[0] == DOMAIN and str(identifier[1]).startswith(prefix)
            for identifier in device_entry.identifiers
        ):
            continue
        identifiers = device_entry.identifiers
        if device_type != CONST_DEVICE_ECOPLUG:
            if identifiers.isdisjoint(expected_identifiers):
                device_registry.async_remove_device(device_entry.id)
            continue

        config_entries = getattr(device_entry, "config_entries", None)
        is_exclusively_owned = config_entries == {entry.entry_id}
        has_only_matching_identifiers = bool(identifiers) and all(
            identifier[0] == DOMAIN and str(identifier[1]).startswith(prefix)
            for identifier in identifiers
        )
        if (
            is_exclusively_owned
            and has_only_matching_identifiers
            and identifiers.isdisjoint(expected_identifiers)
        ):
            device_registry.async_remove_device(device_entry.id)
