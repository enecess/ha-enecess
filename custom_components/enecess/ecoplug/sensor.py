from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    CONF_SENSOR_DISPLAY_PRECISION,
    CONST_ECOPLUG_DEVICES,
    CONST_ENTRY_COORDINATOR,
    DOMAIN,
)
from .model import EcoPlugConfig, device_identifier, sensor_unique_id


SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="power_rt",
        name="power_rt",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=CONF_SENSOR_DISPLAY_PRECISION,
    ),
    SensorEntityDescription(
        key="energy_total",
        name="energy_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=CONF_SENSOR_DISPLAY_PRECISION,
    ),
)


class EcoPlugSensor(CoordinatorEntity, SensorEntity):
    """Expose one cloud reading for a selected EcoPlug."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        plug: EcoPlugConfig,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._hardware_number = plug.hardware_number
        self._attr_unique_id = sensor_unique_id(
            plug.hardware_number,
            description.key,
        )
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
            and snapshot.data_error is None
            and getattr(snapshot, self.entity_description.key) is not None
        )

    @property
    def native_value(self):
        snapshot = (self.coordinator.data or {}).get(self._hardware_number)
        if snapshot is None:
            return None
        return getattr(snapshot, self.entity_description.key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoPlug sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][CONST_ENTRY_COORDINATOR]
    plugs = (EcoPlugConfig(**item) for item in entry.data[CONST_ECOPLUG_DEVICES])
    async_add_entities(
        EcoPlugSensor(coordinator, plug, description)
        for plug in plugs
        for description in SENSOR_DESCRIPTIONS
    )
