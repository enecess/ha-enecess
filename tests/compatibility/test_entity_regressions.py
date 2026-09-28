"""Entity regressions using real HA coordinators and entity registries."""

import logging
from datetime import timedelta
from unittest.mock import AsyncMock, Mock

from homeassistant.helpers import entity_registry
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.enecess.ecomain.model import (
    build_sensor_descriptions,
    build_specs_cloud,
)
from custom_components.enecess.ecomain.sensor import (
    EcoMainAccumulatedEnergySensor,
    EcoMainSensor,
    EcoMainExtraSensor,
)
import test_runtime as runtime_fixture


class RealHAEntityRegressionTests(runtime_fixture.RealHARuntimeFixture):
    def make_energy_sensor(self, updates):
        entry = self.make_entry("cloud")
        coordinator = DataUpdateCoordinator(
            self.hass,
            logging.getLogger(__name__),
            name="Fictional energy",
            config_entry=entry,
            update_method=AsyncMock(side_effect=updates),
        )
        description = next(
            item
            for item in build_sensor_descriptions(build_specs_cloud([]))
            if item.key == "main_all_energy_accumulated"
        )
        sensor = EcoMainAccumulatedEnergySensor(
            coordinator, "cloud", runtime_fixture.SERIAL, description
        )
        sensor._total = 100.0
        sensor.async_write_ha_state = Mock()
        unsubscribe = coordinator.async_add_listener(sensor._handle_coordinator_update)
        self.addCleanup(unsubscribe)
        return coordinator, sensor

    async def test_failed_refresh_does_not_count_stale_delta(self):
        coordinator, sensor = self.make_energy_sensor(
            [
                {"main_all_energy_total_1m": 5.0},
                UpdateFailed("Fictional temporary failure"),
                {"main_all_energy_total_1m": 5.0},
            ]
        )
        totals = [sensor.native_value]
        availability = []
        with self.assertLogs(__name__, level="ERROR"):
            for _ in range(3):
                await coordinator.async_refresh()
                totals.append(sensor.native_value)
                availability.append(sensor.available)
        self.assertEqual(totals, [100.0, 105.0, 105.0, 110.0])
        self.assertEqual(availability, [True, False, True])

    async def test_equal_successful_deltas_are_both_counted(self):
        coordinator, sensor = self.make_energy_sensor(
            [
                {"main_all_energy_total_1m": 5.0},
                {"main_all_energy_total_1m": 5.0},
            ]
        )
        await coordinator.async_refresh()
        self.assertEqual(sensor.native_value, 105.0)
        await coordinator.async_refresh()
        self.assertEqual(sensor.native_value, 110.0)

    async def test_existing_registry_identity_and_custom_names_survive(self):
        entry = self.make_entry("cloud")
        coordinator = DataUpdateCoordinator(
            self.hass,
            logging.getLogger(__name__),
            name="Fictional registry",
            config_entry=entry,
        )
        coordinator.async_set_updated_data({"main_all_power_avg_1m": 10.0})
        descriptions = build_sensor_descriptions(build_specs_cloud([]))
        power = EcoMainSensor(
            coordinator, "cloud", runtime_fixture.SERIAL, descriptions[0]
        )
        energy = EcoMainAccumulatedEnergySensor(
            coordinator,
            "cloud",
            runtime_fixture.SERIAL,
            next(
                item
                for item in descriptions
                if item.key == "main_all_energy_accumulated"
            ),
        )
        formula = EcoMainExtraSensor(
            coordinator,
            "cloud",
            runtime_fixture.SERIAL,
            {
                "key": "extra_formula_fixture",
                "name": "My chosen formula",
                "operation": "formula",
                "sources": ["main_all_power_avg_1m"],
                "result_type": "power",
                "variables": {"x": "main_all_power_avg_1m"},
                "expression": "x * 2",
            },
            None,
            0,
        )
        entities = [power, energy, formula]
        expected_unique_ids = [
            "ecomain:FICTIONAL-COMPAT-MAIN-001:key_main_all_power_avg_1m:mode_cloud",
            "ecomain:FICTIONAL-COMPAT-MAIN-001:key_main_all_energy_accumulated:mode_cloud",
            "ecomain:FICTIONAL-COMPAT-MAIN-001:key_extra_formula_fixture:mode_cloud",
        ]
        registry = entity_registry.async_get(self.hass)
        existing_ids = []
        for index, unique_id in enumerate(expected_unique_ids):
            existing = registry.async_get_or_create(
                "sensor",
                "enecess",
                unique_id,
                config_entry=entry,
                suggested_object_id=f"existing_fixture_{index}",
                original_name=f"Legacy name {index}",
            )
            registry.async_update_entity(existing.entity_id, name=f"User name {index}")
            existing_ids.append(existing.entity_id)
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
        self.assertEqual([entity.unique_id for entity in entities], expected_unique_ids)
        self.assertEqual([entity.entity_id for entity in entities], existing_ids)
        self.assertTrue(all(entity.has_entity_name for entity in entities))
        self.assertEqual(formula.name, "My chosen formula")
        self.assertEqual(formula.native_value, 20.0)
        for index, entity_id in enumerate(existing_ids):
            self.assertEqual(registry.async_get(entity_id).name, f"User name {index}")
            self.assertEqual(
                self.hass.states.get(entity_id).attributes["friendly_name"],
                f"User name {index}",
            )
