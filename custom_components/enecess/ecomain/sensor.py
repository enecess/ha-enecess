from homeassistant.components.sensor import RestoreSensor, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .model import EnecessSensorDescription, build_sensor_descriptions
from ..const import (
    CONF_SENSOR_DISPLAY_PRECISION,
    CONST_ADD_MODE,
    CONST_ADD_MODE_CLOUD,
    CONST_ADD_MODE_LOCAL,
    CONST_DEVICE_ECOMAIN,
    CONST_DEVICE_TYPE,
    CONST_ECOMAIN_SERIAL,
    CONST_ENTRY_COORDINATOR,
    CONST_EXTRA_OPERATION_ABSOLUTE,
    CONST_EXTRA_OPERATION_AVERAGE,
    CONST_EXTRA_OPERATION_INVERT,
    CONST_EXTRA_OPERATION_SUM,
    DOMAIN,
)
from ..extra import build_entry_descriptions, build_entry_specs, extra_entity_device_index, find_source_description, get_entry_extra_entities


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


class EcoMainAccumulatedEnergySensor(CoordinatorEntity, RestoreSensor):
    """Cloud accumulated energy sensor built from per-minute energy deltas."""

    entity_description: EnecessSensorDescription

    def __init__(
        self,
        coordinator,
        mode: str,
        serial: str,
        description: EnecessSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._total: float = 0.0

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
    def native_value(self) -> float:
        return round(self._total, 3)

    def _sync_accumulated_value(self) -> None:
        data = self.coordinator.data
        if data is not None:
            data[self.entity_description.key] = self.native_value

    async def async_added_to_hass(self) -> None:
        """Restore accumulated value after Home Assistant restart."""
        await super().async_added_to_hass()

        restored = await self.async_get_last_sensor_data()
        if restored is not None and restored.native_value is not None:
            try:
                self._total = float(restored.native_value)
                self._sync_accumulated_value()
                return
            except (TypeError, ValueError):
                self._total = 0.0

        # Fresh install only: count the already-fetched coordinator value once.
        # On restore we intentionally do not add the current pre-refresh delta,
        # because without a cloud sample timestamp we cannot know whether it was
        # already included before restart.
        self._add_current_delta()
        self._sync_accumulated_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Add one cloud delta on each coordinator update."""
        self._add_current_delta()
        self._sync_accumulated_value()
        self.async_write_ha_state()

    def _add_current_delta(self) -> None:
        source_key = self.entity_description.spec.source_key
        if not source_key:
            return

        raw_delta = (self.coordinator.data or {}).get(source_key)
        if raw_delta is None:
            return

        try:
            delta = float(raw_delta)
        except (TypeError, ValueError):
            return

        # Cloud energy should be a positive per-minute increment.
        # Ignore negative values to keep TOTAL_INCREASING safe.
        if delta < 0:
            return

        self._total += delta


class EcoMainExtraSensor(CoordinatorEntity, SensorEntity):
    """Derived EcoMain sensor from one or more source sensors."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator,
        mode: str,
        serial: str,
        extra_config: dict,
        source_description: SensorEntityDescription,
        device_index: int,
    ) -> None:
        super().__init__(coordinator)
        self._extra_config = extra_config
        self._sources = list(extra_config.get("sources") or [])
        self._operation = extra_config.get("operation")
        self.entity_description = SensorEntityDescription(
            key=extra_config["key"],
            name=extra_config.get("name") or extra_config["key"],
            native_unit_of_measurement=source_description.native_unit_of_measurement,
            device_class=source_description.device_class,
            state_class=source_description.state_class,
            suggested_display_precision=CONF_SENSOR_DISPLAY_PRECISION,
        )

        mode_key = CONST_ADD_MODE_CLOUD if mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL
        if device_index == 0:
            self._device_info = DeviceInfo(
                identifiers={_device_identifier(serial, 0, mode_key)},
                manufacturer="enecess",
                model="EcoMain",
                name=f"EcoMain {serial} ({mode_key.title()})",
            )
        else:
            self._device_info = DeviceInfo(
                identifiers={_device_identifier(serial, device_index, mode_key)},
                manufacturer="enecess",
                model="EcoSub",
                name=f"EcoSub {serial} #{device_index} ({mode_key.title()})",
                via_device=_device_identifier(serial, 0, mode_key),
            )
        self._unique_id = _sensor_unique_id(serial, device_index, extra_config["key"], mode_key)

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def available(self) -> bool:
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data or {}
        return all(source in data and data[source] is not None for source in self._sources)

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            values = [float(data[source]) for source in self._sources]
        except (KeyError, TypeError, ValueError):
            return None

        if not values:
            return None
        if self._operation == CONST_EXTRA_OPERATION_INVERT:
            return -values[0]
        if self._operation == CONST_EXTRA_OPERATION_ABSOLUTE:
            return abs(values[0])
        if self._operation == CONST_EXTRA_OPERATION_SUM:
            return sum(values)
        if self._operation == CONST_EXTRA_OPERATION_AVERAGE:
            return sum(values) / len(values)
        return None


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
            specs = build_entry_specs(entry.data, entry.options)
        else:
            return

    descs = build_sensor_descriptions(specs)
    entities = []
    for desc in descs:
        if desc.spec.kind == "energy_accumulated":
            entities.append(EcoMainAccumulatedEnergySensor(coordinator, mode, serial, desc))
        else:
            entities.append(EcoMainSensor(coordinator, mode, serial, desc))

    source_descs = build_entry_descriptions(entry.data, entry.options)
    for extra in get_entry_extra_entities(entry.options):
        sources = extra.get("sources") or []
        if not sources:
            continue
        source_desc = find_source_description(source_descs, sources[0])
        if source_desc is None:
            continue
        device_index = extra_entity_device_index(source_descs, extra)
        entities.append(EcoMainExtraSensor(coordinator, mode, serial, extra, source_desc, device_index))

    async_add_entities(entities)
