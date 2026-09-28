"""Set up and unload enecess integrations."""

from copy import deepcopy

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
    CONST_ECOMAIN_FIRMWARE_VERSION,
    CONST_ECOMAIN_HOST,
    CONST_ECOMAIN_PORT,
    CONST_ECOPLUG_DEVICES,
)
from .ecomain.coordinator import EcoMainCloudCoordinator, EcoMainModbusCoordinator
from .ecoplug.coordinator import EcoPlugCloudCoordinator
from .extra import build_entry_specs
from .registry import (
    async_remove_unconfigured_registry_entries as _async_remove_unconfigured_registry_entries,
    normalize_entry_title,
)
from .runtime import EnecessConfigEntry, EnecessRuntimeData

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.SWITCH)


async def async_setup_entry(hass: HomeAssistant, entry: EnecessConfigEntry) -> bool:
    """Set up enecess from a config entry."""
    title = normalize_entry_title(entry.data, entry.title)
    if title != entry.title:
        hass.config_entries.async_update_entry(entry, title=title)
    options_at_setup = dict(entry.options)
    device_type = entry.data.get(CONST_DEVICE_TYPE)
    ecoplug_devices_at_setup = (
        deepcopy(entry.data.get(CONST_ECOPLUG_DEVICES, []))
        if device_type == CONST_DEVICE_ECOPLUG
        else None
    )

    async def _async_reload_on_entry_change(
        hass: HomeAssistant,
        updated_entry: EnecessConfigEntry,
    ) -> None:
        if dict(updated_entry.options) != options_at_setup:
            await hass.config_entries.async_reload(updated_entry.entry_id)
            return
        if (
            device_type == CONST_DEVICE_ECOMAIN
            and updated_entry.data.get(CONST_ADD_MODE) != CONST_ADD_MODE_CLOUD
            and updated_entry.data.get(CONST_ECOMAIN_FIRMWARE_VERSION) is not None
            and updated_entry.data[CONST_ECOMAIN_FIRMWARE_VERSION]
            != coordinator.firmware_version
        ):
            await hass.config_entries.async_reload(updated_entry.entry_id)
            return
        if (
            device_type == CONST_DEVICE_ECOPLUG
            and updated_entry.data.get(CONST_ECOPLUG_DEVICES, [])
            != ecoplug_devices_at_setup
        ):
            await hass.config_entries.async_reload(updated_entry.entry_id)

    entry_data = entry.data
    client = None

    if device_type == CONST_DEVICE_ECOMAIN:
        mode = entry_data.get(CONST_ADD_MODE)
        if mode == CONST_ADD_MODE_CLOUD:
            session = async_get_clientsession(hass)
            api = EnecessApi(session=session, base_url=CONF_CLOUD_BASE_URL)
            coordinator = EcoMainCloudCoordinator(hass=hass, entry=entry, api=api)
        else:
            host: str = entry_data.get(CONST_ECOMAIN_HOST, "")
            port: int = entry_data.get(CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT)
            client = EnecessModbusClient(host, port)
            specs = build_entry_specs(
                entry.data, entry.options, include_unsupported=True
            )
            coordinator = EcoMainModbusCoordinator(
                hass=hass,
                entry=entry,
                client=client,
                specs=specs,
            )
    elif device_type == CONST_DEVICE_ECOPLUG:
        session = async_get_clientsession(hass)
        api = EnecessApi(session=session, base_url=CONF_CLOUD_BASE_URL)
        coordinator = EcoPlugCloudCoordinator(hass=hass, entry=entry, api=api)
    else:
        return False

    setup_complete = False
    platforms_started = False
    try:
        await coordinator.async_config_entry_first_refresh()
        if isinstance(coordinator, EcoMainModbusCoordinator):
            firmware = coordinator.firmware_version
            if entry.data.get(CONST_ECOMAIN_FIRMWARE_VERSION) != firmware:
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONST_ECOMAIN_FIRMWARE_VERSION: firmware}
                )
        entry.runtime_data = EnecessRuntimeData(coordinator, client)
        _async_remove_unconfigured_registry_entries(hass, entry)
        platforms_started = True
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        if client is not None:

            async def _async_close_on_stop(event: Event) -> None:
                """Release the socket when HA stops without unloading entries."""
                await client.async_close()

            entry.async_on_unload(
                hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, _async_close_on_stop)
            )
        entry.async_on_unload(entry.add_update_listener(_async_reload_on_entry_change))
        setup_complete = True
    finally:
        # Cancelled setup must release the same resources as a failed attempt.
        if not setup_complete:
            try:
                if platforms_started:
                    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            finally:
                await coordinator.async_shutdown()
                if client is not None:
                    await client.async_close()
                if hasattr(entry, "runtime_data"):
                    del entry.runtime_data
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EnecessConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False
    runtime = getattr(entry, "runtime_data", None)
    if runtime is not None:
        await runtime.coordinator.async_shutdown()
        if runtime.modbus_client is not None:
            await runtime.modbus_client.async_close()
        del entry.runtime_data
    return True
