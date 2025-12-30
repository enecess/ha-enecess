from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .model import EnecessSensorDescription, build_sensor_descriptions
from ..const import (
    DOMAIN, CONST_ADD_MODE, CONST_ADD_MODE_CLOUD, CONST_ECOMAIN_SERIAL, CONST_ENTRY_COORDINATOR, CONST_ADD_MODE_LOCAL, CONST_DEVICE_TYPE, CONST_DEVICE_ECOMAIN,
    CONST_ECOMAIN_SELECTED_SLAVES
)


def _device_identifier(serial: str, idx: int, mode: str) -> tuple[str, str]:
    mode_key = CONST_ADD_MODE_CLOUD if mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL
    sub = f":sub_{idx}" if idx != 0 else ""
    idt = f"ecomain:{serial}{sub}:mode_{mode_key}"
    return DOMAIN, idt


def _sensor_unique_id(serial: str, idx: int, key: str, mode: str) -> str:
    mode_key = CONST_ADD_MODE_CLOUD if mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL
    sub = f":sub_{idx}" if idx != 0 else ""
    return f"ecomain:{serial}{sub}:key_{key}:mode_{mode_key}"


class EcoMainSensor(CoordinatorEntity, SensorEntity):
    """EcoMain sensor backed by a DataUpdateCoordinator."""

    entity_description: EnecessSensorDescription

    def __init__(self, coordinator, mode: str, serial: str, description: EnecessSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        mode_key = CONST_ADD_MODE_CLOUD if mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL

        spec = description.spec
        if spec.device_index == 0:
            self._device_info = DeviceInfo(
                identifiers={_device_identifier(serial, 0, mode_key)},
                manufacturer="enecess",
                model="EcoMain",
                name=f"EcoMain {serial} ({mode_key.title()})",
            )
            self._unique_id = _sensor_unique_id(serial, 0, spec.key, mode_key)
        else:
            self._device_info = DeviceInfo(
                identifiers={_device_identifier(serial, spec.device_index, mode_key)},
                manufacturer="enecess",
                model="EcoSub",
                name=f"EcoSub {serial} #{spec.device_index} ({mode_key.title()})",
                via_device=_device_identifier(serial, 0, mode_key),
            )
            self._unique_id = _sensor_unique_id(serial, spec.device_index, spec.key, mode_key)

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self.entity_description.key)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoMain sensors from config entry."""
    entry_data = entry.data
    device_type = entry_data.get(CONST_DEVICE_TYPE)
    mode = entry_data.get(CONST_ADD_MODE)
    serial = entry_data.get(CONST_ECOMAIN_SERIAL)
    coordinator = hass.data[DOMAIN][entry.entry_id][CONST_ENTRY_COORDINATOR]
    specs = getattr(coordinator, "specs", None)
    if specs is None:
        if device_type == CONST_DEVICE_ECOMAIN:
            if mode == CONST_ADD_MODE_CLOUD:
                from .model import build_specs_cloud
                specs = build_specs_cloud(entry_data.get(CONST_ECOMAIN_SELECTED_SLAVES))
            else:
                from .model import build_specs_local
                specs = build_specs_local(entry_data.get(CONST_ECOMAIN_SELECTED_SLAVES))
        else:
            return

    descs = build_sensor_descriptions(specs)
    async_add_entities([EcoMainSensor(coordinator, mode, serial, d) for d in descs])
