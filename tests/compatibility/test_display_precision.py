"""Register display suggestions preserve native readings and user precision."""

from datetime import timedelta
import logging

from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.enecess.ecomain.model import (
    build_sensor_descriptions,
    build_specs_local,
)
from custom_components.enecess.ecomain.sensor import EcoMainExtraSensor, EcoMainSensor
import test_runtime as runtime_fixture


class DisplayPrecisionTests(runtime_fixture.RealHARuntimeFixture):
    async def test_register_suggestions_refresh_without_rounding_or_overwriting_user_precision(
        self,
    ):
        entry = self.make_entry("local")
        coordinator = DataUpdateCoordinator(
            self.hass,
            logging.getLogger(__name__),
            name="Fictional display precision",
            config_entry=entry,
        )
        cases = {
            "main_l1_power_rt": (2, 123.456789, None),
            "main_l2_power_rt": (2, -12.345678, 0),
            "main_l1_energy_fwd_total": (3, 1234.567891, None),
            "solar_irradiance": (1, 567.891234, None),
            "solar_performance_ratio": (1, 98.765432, None),
            "solar_actual_power": (2, -12.345678, None),
            "solar_estimated_power": (2, 456.789123, None),
            "solar_actual_energy": (3, 1234.567891, None),
            "solar_estimated_energy": (3, 2345.678912, None),
        }
        coordinator.async_set_updated_data(
            {key: value for key, (_, value, _) in cases.items()}
        )
        descriptions = build_sensor_descriptions(
            build_specs_local(
                [4],
                ["power", "energy_forward"],
                [
                    "solar_irradiance",
                    "solar_performance_ratio",
                    "solar_actual_power",
                    "solar_estimated_power",
                    "solar_actual_energy",
                    "solar_estimated_energy",
                ],
            )
        )
        devices = device_registry.async_get(self.hass)
        parent = devices.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("enecess", f"ecomain:{runtime_fixture.SERIAL}:mode_local")},
            manufacturer="enecess",
            model="ecoMain",
            name="Fictional precision master",
        )
        entities = [
            EcoMainSensor(
                coordinator,
                "local",
                runtime_fixture.SERIAL,
                desc,
                via_device_id=parent.id
                if "via_device_id" in DeviceInfo.__annotations__
                else None,
            )
            for desc in descriptions
            if desc.key in cases
        ]
        self.assertEqual(
            {entity.entity_description.key for entity in entities}, set(cases)
        )
        registry = entity_registry.async_get(self.hass)
        existing = {}
        for entity in entities:
            key = entity.entity_description.key
            record = registry.async_get_or_create(
                "sensor",
                "enecess",
                entity.unique_id,
                config_entry=entry,
                suggested_object_id=f"existing_{key}",
            )
            sensor_options = {"suggested_display_precision": 3}
            if cases[key][2] is not None:
                sensor_options["display_precision"] = cases[key][2]
            registry.async_update_entity_options(
                record.entity_id, "sensor", sensor_options
            )
            existing[key] = record
        platform = EntityPlatform(
            hass=self.hass,
            logger=logging.getLogger(__name__),
            domain="sensor",
            platform_name="enecess",
            platform=None,
            scan_interval=timedelta(seconds=30),
            entity_namespace=None,
        )
        platform.config_entry = entry
        self.addAsyncCleanup(platform.async_reset)
        await platform.async_add_entities(entities)
        for entity in entities:
            key = entity.entity_description.key
            precision, native_value, override = cases[key]
            with self.subTest(key=key):
                record = registry.async_get(entity.entity_id)
                self.assertEqual(record.id, existing[key].id)
                self.assertEqual(entity.entity_id, existing[key].entity_id)
                self.assertEqual(
                    record.options["sensor"]["suggested_display_precision"], precision
                )
                self.assertEqual(
                    record.options["sensor"].get("display_precision"), override
                )
                self.assertEqual(entity.native_value, native_value)
                self.assertEqual(
                    float(self.hass.states.get(entity.entity_id).state), native_value
                )

    async def test_derived_sensor_keeps_three_decimals_with_two_decimal_source(
        self,
    ):
        entry = self.make_entry("local")
        coordinator = DataUpdateCoordinator(
            self.hass,
            logging.getLogger(__name__),
            name="Fictional derived precision",
            config_entry=entry,
        )
        coordinator.async_set_updated_data({"main_l1_power_rt": -12.345678})
        source = build_sensor_descriptions(build_specs_local([], ["power"]))[0]
        entity = EcoMainExtraSensor(
            coordinator,
            "local",
            runtime_fixture.SERIAL,
            {
                "key": "extra_fictional_precision",
                "operation": "absolute",
                "sources": ["main_l1_power_rt"],
            },
            source,
            0,
        )
        self.assertEqual(entity.suggested_display_precision, 3)
        self.assertEqual(entity.native_value, 12.345678)
