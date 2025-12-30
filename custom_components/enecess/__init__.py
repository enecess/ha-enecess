from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client_api import EnecessApi
from .client_modbus import EnecessModbusClient
from .const import (
    DOMAIN, CONST_DEVICE_TYPE, CONST_DEVICE_ECOMAIN, CONST_ADD_MODE, CONST_ADD_MODE_CLOUD, CONST_ENTRY_COORDINATOR, CONST_ENTRY_ENECESS_API, CONST_ENTRY_MODBUS_CLIENT,
    CONF_CLOUD_BASE_URL, CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT, CONST_ECOMAIN_HOST
)

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up enecess from a config entry."""
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
            from .ecomain.model import build_specs_local
            from .const import CONST_ECOMAIN_SELECTED_SLAVES

            host: Optional[str] = entry_data.get(CONST_ECOMAIN_HOST, "")
            port: int = entry_data.get(CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT)
            client = EnecessModbusClient(host, port)
            specs = build_specs_local(entry_data.get(CONST_ECOMAIN_SELECTED_SLAVES))
            coordinator = EcoMainModbusCoordinator(hass=hass, entry=entry, client=client, specs=specs)
            entry_store[CONST_ENTRY_MODBUS_CLIENT] = client
            entry_store[CONST_ENTRY_COORDINATOR] = coordinator
    else:
        return False

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


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
