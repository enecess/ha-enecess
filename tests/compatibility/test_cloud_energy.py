"""Cloud totals remain independent of entity registration and callback order."""

from datetime import timedelta
import logging
from unittest.mock import AsyncMock, patch

from homeassistant.helpers import entity_registry
from homeassistant.components.sensor import SensorExtraStoredData
from homeassistant.core import State
from homeassistant.helpers import restore_state
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from custom_components import enecess
from custom_components.enecess.client_api import EnecessApiError
from custom_components.enecess.ecomain.coordinator import EcoMainCloudCoordinator
from custom_components.enecess.ecomain.model import build_sensor_descriptions
from custom_components.enecess.ecomain.sensor import (
    EcoMainAccumulatedEnergySensor,
    EcoMainExtraSensor,
)
from test_runtime import RealHARuntimeFixture, SERIAL


class CloudEnergyTests(RealHARuntimeFixture):
    def make_coordinator(self, entry=None):
        entry = entry or self.make_entry("cloud")
        api = AsyncMock()
        api.get_passageway.return_value = {
            "household_electricity": {"power": 20, "energy": 5},
        }
        coordinator = EcoMainCloudCoordinator(self.hass, entry, api)
        self.addAsyncCleanup(coordinator.async_shutdown)
        return entry, api, coordinator

    def make_entities(self, coordinator):
        description = next(
            desc
            for desc in build_sensor_descriptions(coordinator.specs)
            if desc.key == "main_all_energy_accumulated"
        )
        source = EcoMainAccumulatedEnergySensor(
            coordinator, "cloud", SERIAL, description
        )
        formula = EcoMainExtraSensor(
            coordinator,
            "cloud",
            SERIAL,
            {
                "key": "extra_energy_fixture",
                "name": "Double energy",
                "operation": "formula",
                "sources": [description.key],
                "variables": {"a": description.key},
                "expression": "a * 2",
                "result_type": "energy",
            },
            None,
            0,
        )
        return source, formula

    async def add_entities(self, entry, entities):
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
        return platform

    async def test_disabled_source_does_not_disable_formula_or_aggregate(self):
        entry, api, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        source, formula = self.make_entities(coordinator)
        aggregate = EcoMainExtraSensor(
            coordinator,
            "cloud",
            SERIAL,
            {
                "key": "extra_sum_fixture",
                "name": "Energy sum",
                "operation": "sum",
                "sources": [
                    "main_all_energy_accumulated",
                    "main_ch1_energy_accumulated",
                ],
            },
            source.entity_description,
            0,
        )
        registry = entity_registry.async_get(self.hass)
        registry.async_get_or_create(
            "sensor",
            "enecess",
            source.unique_id,
            config_entry=entry,
            disabled_by=entity_registry.RegistryEntryDisabler.USER,
        )
        await self.add_entities(entry, [formula, aggregate, source])
        api.get_passageway.return_value = {
            "household_electricity": {"power": 20, "energy": 3},
            "ch_info": [{"ch_number": 0, "energy": 2}],
        }
        await coordinator.async_refresh()
        self.assertEqual(formula.native_value, 16)
        self.assertEqual(self.hass.states.get(formula.entity_id).state, "16.0")
        self.assertEqual(aggregate.native_value, 10)
        self.assertTrue(aggregate.available)

    async def test_formula_published_before_source_sees_current_total(self):
        entry, _, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        source, formula = self.make_entities(coordinator)
        await self.add_entities(entry, [formula, source])
        await coordinator.async_refresh()
        self.assertEqual(self.hass.states.get(formula.entity_id).state, "20.0")
        self.assertEqual(source.native_value, 10)

    async def test_equal_deltas_count_but_failed_poll_does_not(self):
        _, api, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        self.assertEqual(coordinator.data.get("main_all_energy_accumulated"), 5)
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data["main_all_energy_accumulated"], 10)
        api.get_passageway.side_effect = EnecessApiError("Fictional outage")
        with self.assertLogs("custom_components.enecess.ecomain.coordinator", "ERROR"):
            await coordinator.async_refresh()
        self.assertFalse(coordinator.last_update_success)
        api.get_passageway.side_effect = None
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data["main_all_energy_accumulated"], 15)

    async def test_invalid_delta_hides_total_then_zero_recovers_without_reset(self):
        _, api, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        for invalid in (None, "bad", True, float("nan"), float("inf"), -1):
            api.get_passageway.return_value = {
                "household_electricity": {"energy": invalid}
            }
            await coordinator.async_refresh()
            self.assertNotIn("main_all_energy_accumulated", coordinator.data)
        api.get_passageway.return_value = {"household_electricity": {"energy": 0}}
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data.get("main_all_energy_accumulated"), 5)

    async def test_total_restores_without_source_entity_and_skips_initial_sample(self):
        entry, _, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        await coordinator.async_refresh()
        await coordinator.async_shutdown()
        _, _, restarted = self.make_coordinator(entry)
        await restarted.async_config_entry_first_refresh()
        self.assertEqual(restarted.data.get("main_all_energy_accumulated"), 10)
        await restarted.async_refresh()
        self.assertEqual(restarted.data["main_all_energy_accumulated"], 15)

    async def test_fresh_cloud_storage_accumulates_first_energy_sample(self):
        _, _, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        self.assertEqual(coordinator.data["main_all_energy_accumulated"], 5)
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data["main_all_energy_accumulated"], 10)

    async def test_fresh_power_only_cloud_storage_loads(self):
        entry = self.make_entry("cloud")
        self.hass.config_entries.async_update_entry(
            entry, options={"measurement_types": ["power_avg_1m"]}
        )
        _, _, coordinator = self.make_coordinator(entry)
        await coordinator.async_config_entry_first_refresh()
        self.assertEqual(coordinator.data["main_all_power_avg_1m"], 20)
        self.assertNotIn("main_all_energy_accumulated", coordinator.data)

    async def test_disabled_renamed_legacy_sensor_total_is_preserved_on_upgrade(self):
        entry, _, coordinator = self.make_coordinator()
        source, _ = self.make_entities(coordinator)
        registry = entity_registry.async_get(self.hass)
        registered = registry.async_get_or_create(
            "sensor",
            "enecess",
            source.unique_id,
            config_entry=entry,
            disabled_by=entity_registry.RegistryEntryDisabler.USER,
        )
        registered = registry.async_update_entity(
            registered.entity_id,
            new_entity_id="sensor.fictional_renamed_energy",
            name="My retained energy name",
        )
        stored = restore_state.StoredState(
            State(registered.entity_id, "0.1", {"unit_of_measurement": "kWh"}),
            SensorExtraStoredData(100, "Wh"),
            dt_util.utcnow(),
        )
        restored = restore_state.async_get(self.hass)
        await restored.store.async_save(
            [stored.as_dict() | {"entity_registry_id": registered.id}]
        )
        await restored.async_load()
        await coordinator.async_config_entry_first_refresh()
        self.assertEqual(coordinator.data["main_all_energy_accumulated"], 100)
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data["main_all_energy_accumulated"], 105)
        self.assertEqual(
            registry.async_get(registered.entity_id).name, "My retained energy name"
        )
        self.assertEqual(
            registry.async_get(registered.entity_id).disabled_by,
            entity_registry.RegistryEntryDisabler.USER,
        )
        await coordinator.async_shutdown()
        _, _, restarted = self.make_coordinator(entry)
        await restarted.async_config_entry_first_refresh()
        self.assertEqual(restarted.data["main_all_energy_accumulated"], 105)

    async def test_existing_cloud_storage_owns_totals_even_when_empty(self):
        for stored, first, second in (
            ({}, 5, 10),
            ({"main_all_energy_accumulated": 40}, 40, 45),
        ):
            with self.subTest(stored=stored):
                entry, _, coordinator = self.make_coordinator()
                source, _ = self.make_entities(coordinator)
                registered = entity_registry.async_get(self.hass).async_get_or_create(
                    "sensor", "enecess", source.unique_id, config_entry=entry
                )
                restored = restore_state.async_get(self.hass)
                await restored.store.async_save(
                    [
                        restore_state.StoredState(
                            State(registered.entity_id, "999"),
                            SensorExtraStoredData(999, "Wh"),
                            dt_util.utcnow(),
                        ).as_dict()
                        | {"entity_registry_id": registered.id}
                    ]
                )
                await restored.async_load()
                store = Store(self.hass, 1, f"enecess.{entry.entry_id}.cloud_energy")
                await store.async_save(stored)
                await coordinator.async_config_entry_first_refresh()
                self.assertEqual(coordinator.data["main_all_energy_accumulated"], first)
                await coordinator.async_refresh()
                self.assertEqual(
                    coordinator.data["main_all_energy_accumulated"], second
                )

    async def test_removing_entry_deletes_totals(self):
        entry, _, coordinator = self.make_coordinator()
        await coordinator.async_config_entry_first_refresh()
        await coordinator.async_refresh()
        await coordinator.async_shutdown()
        await enecess.async_remove_entry(self.hass, entry)
        _, _, restarted = self.make_coordinator(entry)
        await restarted.async_config_entry_first_refresh()
        self.assertEqual(restarted.data.get("main_all_energy_accumulated"), 5)

    async def test_refreshes_do_not_postpone_pending_storage_checkpoint(self):
        entry, _, coordinator = self.make_coordinator()
        scheduled = []
        store = coordinator._energy._store
        # Replace only the 60-second scheduler; write and reload real HA storage.
        with patch.object(
            store,
            "async_delay_save",
            side_effect=lambda callback, delay: scheduled.append(callback),
        ):
            await coordinator.async_config_entry_first_refresh()
            await coordinator.async_refresh()
            await coordinator.async_refresh()
            self.assertEqual(len(scheduled), 1)
            await store.async_save(scheduled.pop()())
            _, _, restored = self.make_coordinator(entry)
            await restored.async_config_entry_first_refresh()
            self.assertEqual(restored.data["main_all_energy_accumulated"], 15)
            await coordinator.async_refresh()
            self.assertEqual(len(scheduled), 1)
