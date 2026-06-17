from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .client_api import EnecessApi
from .client_modbus import EnecessModbusClient
from .const import (
    DOMAIN, CONST_DEVICE_TYPE, CONST_DEVICE_ECOMAIN, CONST_ADD_MODE, CONST_ADD_MODE_CLOUD, CONST_ENTRY_COORDINATOR, CONST_ENTRY_ENECESS_API, CONST_ENTRY_MODBUS_CLIENT,
    CONF_CLOUD_BASE_URL, CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT, CONST_ECOMAIN_HOST
)
from .extra import build_entry_device_identifiers, build_entry_sensor_unique_ids, build_entry_specs

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up enecess from a config entry."""
    options_at_setup = dict(entry.options)

    async def _async_reload_on_options_change(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        if dict(updated_entry.options) != options_at_setup:
            await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_async_reload_on_options_change))
    hass.data.setdefault(DOMAIN, {})
    entry_store: dict[str, object] = hass.data[DOMAIN].setdefault(entry.entry_id, {})
    entry_data = entry.data

    device_type = entry_data.get(CONST_DEVICE_TYPE)
    if device_type == CONST_DEVICE_ECOMAIN:
        mode = entry_data.get(CONST_ADD_MODE)
        if mode == CONST_ADD_MODE_CLOUD:
            from homeassistant.helpers.aiohttp_client import async_get_clientsession
            from .ecomain.coordinator import EcoMainCloudCoordinator

            session = async_get_clientsession(hass)
            api = EnecessApi(session=session, base_url=CONF_CLOUD_BASE_URL)
            coordinator = EcoMainCloudCoordinator(hass=hass, entry=entry, api=api)
            entry_store[CONST_ENTRY_ENECESS_API] = api
            entry_store[CONST_ENTRY_COORDINATOR] = coordinator
        else:
            from .ecomain.coordinator import EcoMainModbusCoordinator

            host: Optional[str] = entry_data.get(CONST_ECOMAIN_HOST, "")
            port: int = entry_data.get(CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT)
            client = EnecessModbusClient(host, port)
            specs = build_entry_specs(entry.data, entry.options)
            coordinator = EcoMainModbusCoordinator(hass=hass, entry=entry, client=client, specs=specs)
            entry_store[CONST_ENTRY_MODBUS_CLIENT] = client
            entry_store[CONST_ENTRY_COORDINATOR] = coordinator
    else:
        return False

    await coordinator.async_config_entry_first_refresh()
    _async_remove_unconfigured_registry_entries(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False
    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        return True
    entry_data = domain_data.pop(entry.entry_id, None) or {}
    client: Optional[EnecessModbusClient] = entry_data.get(CONST_ENTRY_MODBUS_CLIENT)
    if client is not None:
        await client.async_close()
    if not domain_data:
        hass.data.pop(DOMAIN, None)
    return True


def _async_remove_unconfigured_registry_entries(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove registry entries no longer present in current options."""
    entity_registry = er.async_get(hass)
    expected_unique_ids = build_entry_sensor_unique_ids(entry.data, entry.options)
    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.domain != Platform.SENSOR:
            continue
        unique_id = str(entity_entry.unique_id)
        if unique_id.startswith("ecomain:") and unique_id not in expected_unique_ids:
            entity_registry.async_remove(entity_entry.entity_id)

    device_registry = dr.async_get(hass)
    expected_identifiers = build_entry_device_identifiers(entry.data, entry.options)
    for device_entry in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        if not any(
            identifier[0] == DOMAIN and str(identifier[1]).startswith("ecomain:")
            for identifier in device_entry.identifiers
        ):
            continue
        if device_entry.identifiers.isdisjoint(expected_identifiers):
            device_registry.async_remove_device(device_entry.id)
