import asyncio

from aiohttp import ClientError
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..client_api import EnecessApiError, EnecessAuthError
from ..const import CONST_ECOPLUG_DEVICES, CONST_ENTRY_COORDINATOR, DOMAIN
from .model import EcoPlugConfig, device_identifier, switch_unique_id


_CONTROL_ERRORS = (
    EnecessApiError,
    EnecessAuthError,
    ClientError,
    asyncio.TimeoutError,
    OSError,
)


class EcoPlugSwitch(CoordinatorEntity, SwitchEntity):
    """Control one selected EcoPlug through the cloud coordinator."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator, plug: EcoPlugConfig) -> None:
        super().__init__(coordinator)
        self._hardware_number = plug.hardware_number
        self._attr_unique_id = switch_unique_id(plug.hardware_number)
        self._attr_device_info = DeviceInfo(
            identifiers={device_identifier(plug.hardware_number)},
            manufacturer="enecess",
            model="EcoPlug",
            name=plug.name or f"EcoPlug {plug.hardware_number}",
        )

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return self._attr_device_info

    @property
    def available(self) -> bool:
        if not self.coordinator.last_update_success:
            return False
        snapshot = (self.coordinator.data or {}).get(self._hardware_number)
        return (
            snapshot is not None
            and snapshot.state_error is None
            and snapshot.is_on is not None
        )

    @property
    def is_on(self) -> bool | None:
        snapshot = (self.coordinator.data or {}).get(self._hardware_number)
        return None if snapshot is None else snapshot.is_on

    async def _async_control(self, is_on: bool) -> None:
        try:
            await self.coordinator.async_control(self._hardware_number, is_on)
        except _CONTROL_ERRORS as err:
            raise HomeAssistantError(str(err)) from err

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_control(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_control(False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoPlug switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][CONST_ENTRY_COORDINATOR]
    async_add_entities(
        EcoPlugSwitch(coordinator, EcoPlugConfig(**item))
        for item in entry.data[CONST_ECOPLUG_DEVICES]
    )
