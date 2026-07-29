from copy import deepcopy
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client_api import EnecessApi
from .client_modbus import EnecessModbusClient
from .const import (
    CONF_CLOUD_BASE_URL,
    CONF_ECOMAIN_PORT,
    CONST_ADD_MODE,
    CONST_ADD_MODE_CLOUD,
    CONST_DEVICE_ECOMAIN,
    CONST_DEVICE_ECOPLUG,
    CONST_DEVICE_TYPE,
    CONST_ECOMAIN_HOST,
    CONST_ECOMAIN_PORT,
    CONST_ECOPLUG_DEVICES,
    CONST_ENTRY_COORDINATOR,
    CONST_ENTRY_ENECESS_API,
    CONST_ENTRY_MODBUS_CLIENT,
    DOMAIN,
)
from .extra import build_entry_specs
from .registry import (
    async_remove_unconfigured_registry_entries as _async_remove_unconfigured_registry_entries,
)

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.SWITCH)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up enecess from a config entry."""
    options_at_setup = dict(entry.options)
    device_type = entry.data.get(CONST_DEVICE_TYPE)
    ecoplug_devices_at_setup = (
        deepcopy(entry.data.get(CONST_ECOPLUG_DEVICES, []))
        if device_type == CONST_DEVICE_ECOPLUG
        else None
    )

    async def _async_reload_on_entry_change(
        hass: HomeAssistant,
        updated_entry: ConfigEntry,
    ) -> None:
        if dict(updated_entry.options) != options_at_setup:
            await hass.config_entries.async_reload(updated_entry.entry_id)
            return
        if (
            device_type == CONST_DEVICE_ECOPLUG
            and updated_entry.data.get(CONST_ECOPLUG_DEVICES, [])
            != ecoplug_devices_at_setup
        ):
            await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_async_reload_on_entry_change))
    hass.data.setdefault(DOMAIN, {})
    entry_store: dict[str, object] = hass.data[DOMAIN].setdefault(
        entry.entry_id,
        {},
    )
    entry_data = entry.data

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
            coordinator = EcoMainModbusCoordinator(
                hass=hass,
                entry=entry,
                client=client,
                specs=specs,
            )
            entry_store[CONST_ENTRY_MODBUS_CLIENT] = client
            entry_store[CONST_ENTRY_COORDINATOR] = coordinator
    elif device_type == CONST_DEVICE_ECOPLUG:
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        from .ecoplug.coordinator import EcoPlugCloudCoordinator

        session = async_get_clientsession(hass)
        api = EnecessApi(session=session, base_url=CONF_CLOUD_BASE_URL)
        coordinator = EcoPlugCloudCoordinator(hass=hass, entry=entry, api=api)
        entry_store[CONST_ENTRY_ENECESS_API] = api
        entry_store[CONST_ENTRY_COORDINATOR] = coordinator
    else:
        return False

    await coordinator.async_config_entry_first_refresh()
    _async_remove_unconfigured_registry_entries(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry after its runtime configuration changes."""
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
    client: Optional[EnecessModbusClient] = entry_data.get(
        CONST_ENTRY_MODBUS_CLIENT
    )
    if client is not None:
        await client.async_close()
    if not domain_data:
        hass.data.pop(DOMAIN, None)
    return True
