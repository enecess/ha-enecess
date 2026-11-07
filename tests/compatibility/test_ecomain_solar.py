"""Solar metadata, child identity and availability with real HA entities."""

from types import SimpleNamespace
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.entity_platform import EntityPlatform

from custom_components.enecess.ecomain.coordinator import EcoMainModbusCoordinator
from custom_components.enecess.ecomain.sensor import EcoMainExtraSensor, EcoMainSensor
from custom_components.enecess.ecomain import sensor as sensor_platform
from custom_components.enecess.extra import build_entry_descriptions, build_entry_specs
import test_runtime as runtime_fixture


class SolarClient:
    """Return synthetic local measurements with a controllable solar status."""

    def __init__(self):
        self.online = 1
        self.calls = []
        self.daily = {4018: 0xFF85, 4019: 123456, 4023: 234567,
                      4027: 876, 4028: 345678, 4032: 456789}

    async def async_set_target(self, host, port):
        pass

    async def read_holding_registers(self, address, count):
        self.calls.append((address, count))
        if address == 3009:
            return SimpleNamespace(registers=[140])
        if address == 3101:
            return SimpleNamespace(registers=[1, 0, 0, self.online])
        values = {
            1000: 10000,
            4000: 1000,
            4002: 0xFF9C,
            4004: 200,
            4005: 987,
            4006: 1000,
            4008: 0xFF9C,
            4009: 0xFFFF,
            4013: 0x8000,
            4014: 1001,
            **{address + word: (value >> (word * 16)) & 0xFFFF
               for address, value in self.daily.items()
               for word in range(1 if address in (4018, 4027) else 4)},
        }
        return SimpleNamespace(
            registers=[values.get(i, 0) for i in range(address, address + count)]
        )


class SolarRuntimeTests(runtime_fixture.RealHARuntimeFixture):
    async def test_solar_only_platform_creates_real_master_parent_and_preserves_custom_names(
        self,
    ):
        entry = self.make_entry("local")
        self.hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                "ecomain_firmware_version": 140,
                "ecomain_selected_slaves": [4],
            },
            options={
                "measurement_types": [],
                "solar_measurement_types": ["solar_actual_power", "solar_today_actual_energy"],
                "extra_entities": [
                    {
                        "key": "extra_fictional_solar",
                        "name": "Fictional positive solar",
                        "operation": "absolute",
                        "sources": ["solar_actual_power"],
                    }
                ],
            },
        )
        coordinator = EcoMainModbusCoordinator(
            self.hass,
            entry,
            SolarClient(),
            build_entry_specs(entry.data, entry.options),
        )
        self.addAsyncCleanup(coordinator.async_shutdown)
        await coordinator.async_refresh()
        entry.runtime_data = SimpleNamespace(coordinator=coordinator)
        entities = []
        await sensor_platform.async_setup_entry(self.hass, entry, entities.extend)
        self.assertEqual(len(entities), 3)
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
        self.assertEqual(entities[0].name, "solar_actual_power")
        self.assertIsNone(entities[0].entity_description.translation_key)
        registry = device_registry.async_get(self.hass)
        registered = device_registry.async_entries_for_config_entry(
            registry, entry.entry_id
        )
        parent = next(
            (
                device
                for device in registered
                if ("enecess", f"ecomain:{runtime_fixture.SERIAL}:mode_local")
                in device.identifiers
            ),
            None,
        )
        self.assertIsNotNone(
            parent, "Solar-only setup must create the actual ecoMain registry parent"
        )
        child = next(
            (
                device
                for device in registered
                if ("enecess", f"ecomain:{runtime_fixture.SERIAL}:sub_4:mode_local")
                in device.identifiers
            ),
            None,
        )
        self.assertIsNotNone(child)
        self.assertEqual(child.via_device_id, parent.id)
        self.assertEqual(parent.model, "ecoMain")
        self.assertEqual(
            {
                entity_registry.async_get(self.hass)
                .async_get(entity.entity_id)
                .device_id
                for entity in entities
            },
            {child.id},
        )
        registry.async_update_device(parent.id, name_by_user="Fictional master name")
        daily_entity_id = entities[1].entity_id
        self.assertEqual(entities[1].name, "solar_today_actual_energy")
        self.assertEqual(entities[1].unique_id,
                         f"ecomain:{runtime_fixture.SERIAL}:sub_4:key_solar_today_actual_energy:mode_local")
        entity_registry.async_get(self.hass).async_update_entity(
            daily_entity_id, name="Fictional daily solar name")
        entity_id = entities[0].entity_id
        entity_registry.async_get(self.hass).async_update_entity(
            entity_id, name="Fictional solar name"
        )
        await platform.async_reset()
        entities = []
        await sensor_platform.async_setup_entry(self.hass, entry, entities.extend)
        await platform.async_add_entities(entities)
        self.assertEqual(entities[0].entity_id, entity_id)
        self.assertEqual(entities[1].entity_id, daily_entity_id)
        self.assertEqual(entity_registry.async_get(self.hass).async_get(daily_entity_id).name,
                         "Fictional daily solar name")
        self.assertEqual(
            registry.async_get(parent.id).name_by_user, "Fictional master name"
        )
        self.assertEqual(
            entity_registry.async_get(self.hass).async_get(entity_id).name,
            "Fictional solar name",
        )

    async def test_metadata_device_ownership_and_offline_recovery_keep_identity(self):
        entry = self.make_entry("local")
        data = {
            **entry.data,
            "ecomain_firmware_version": 140,
            "ecomain_selected_slaves": [1, 4],
        }
        options = {
            "measurement_types": ["power"],
            "solar_measurement_types": [
                "solar_irradiance",
                "solar_tilt_angle",
                "solar_module_temperature",
                "solar_actual_power",
                "solar_estimated_power",
                "solar_performance_ratio",
                "solar_actual_energy",
                "solar_estimated_energy",
                "solar_yesterday_performance_ratio",
                "solar_yesterday_estimated_energy",
                "solar_yesterday_actual_energy",
                "solar_today_performance_ratio",
                "solar_today_estimated_energy",
                "solar_today_actual_energy",
            ],
        }
        descriptions = {
            desc.key: desc for desc in build_entry_descriptions(data, options)
        }
        self.assertEqual({key for key in descriptions if key.startswith("solar_")},
                         set(options["solar_measurement_types"]))
        for key, unit, device_class, state_class, precision in (
            ("solar_yesterday_performance_ratio", "%", None, None, 1),
            ("solar_yesterday_estimated_energy", "Wh", SensorDeviceClass.ENERGY, None, 3),
            ("solar_yesterday_actual_energy", "Wh", SensorDeviceClass.ENERGY, None, 3),
            ("solar_today_performance_ratio", "%", None, None, 1),
            ("solar_today_estimated_energy", "Wh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, 3),
            ("solar_today_actual_energy", "Wh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, 3),
        ):
            with self.subTest(key=key):
                desc = descriptions[key]
                self.assertEqual((desc.native_unit_of_measurement, desc.device_class,
                                  desc.state_class, desc.suggested_display_precision),
                                 (unit, device_class, state_class, precision))
                self.assertEqual(desc.name, key)
                self.assertIsNone(desc.translation_key)
        self.assertEqual(
            descriptions["solar_irradiance"].device_class, SensorDeviceClass.IRRADIANCE
        )
        self.assertEqual(
            descriptions["solar_module_temperature"].device_class,
            SensorDeviceClass.TEMPERATURE,
        )
        self.assertEqual(
            descriptions["solar_actual_energy"].state_class,
            SensorStateClass.TOTAL_INCREASING,
        )
        self.assertIsNone(descriptions["solar_performance_ratio"].device_class)
        self.assertEqual(
            descriptions["solar_tilt_angle"].native_unit_of_measurement, "°"
        )
        self.assertEqual(
            descriptions["solar_tilt_angle"].state_class, SensorStateClass.MEASUREMENT
        )
        self.assertIsNone(descriptions["solar_actual_power"].translation_key)
        self.assertEqual(descriptions["solar_actual_power"].name, "solar_actual_power")
        client = SolarClient()
        coordinator = EcoMainModbusCoordinator(
            self.hass, entry, client, build_entry_specs(data, options)
        )
        self.addAsyncCleanup(coordinator.async_shutdown)
        sensor = EcoMainSensor(
            coordinator,
            "local",
            runtime_fixture.SERIAL,
            descriptions["solar_actual_power"],
        )
        derived = EcoMainExtraSensor(
            coordinator,
            "local",
            runtime_fixture.SERIAL,
            {
                "key": "extra_solar_abs",
                "name": "Fictional positive output",
                "operation": "absolute",
                "sources": ["solar_actual_power"],
            },
            descriptions["solar_actual_power"],
            4,
        )
        for entity in (sensor, derived):
            self.assertEqual(entity.device_info["model"], "ecoSolarMonitor")
            self.assertEqual(
                entity.device_info["name"],
                f"ecoSolarMonitor {runtime_fixture.SERIAL} (Local)",
            )
            self.assertEqual(
                entity.device_info["via_device"],
                ("enecess", f"ecomain:{runtime_fixture.SERIAL}:mode_local"),
            )
        identity = sensor.unique_id
        self.assertEqual(
            identity,
            f"ecomain:{runtime_fixture.SERIAL}:sub_4:key_solar_actual_power:mode_local",
        )
        await coordinator.async_refresh()
        for key, expected in {
            "solar_irradiance": 100,
            "solar_tilt_angle": 20,
            "solar_module_temperature": -10,
            "solar_actual_power": -1,
            "solar_estimated_power": 10,
            "solar_performance_ratio": 98.7,
            "solar_actual_energy": 1.001,
            "solar_estimated_energy": 9223372036854776.0,
            "solar_yesterday_performance_ratio": -12.3,
            "solar_yesterday_estimated_energy": 123.456,
            "solar_yesterday_actual_energy": 234.567,
            "solar_today_performance_ratio": 87.6,
            "solar_today_estimated_energy": 345.678,
            "solar_today_actual_energy": 456.789,
        }.items():
            with self.subTest(key=key):
                self.assertAlmostEqual(coordinator.data[key], expected)
        self.assertEqual([call for call in client.calls if call[0] >= 4000],
                         [(4000, 1), (4002, 1), (4004, 32)])
        daily_sensors = {key: EcoMainSensor(coordinator, "local", runtime_fixture.SERIAL, descriptions[key])
                         for key in ("solar_yesterday_estimated_energy", "solar_yesterday_actual_energy",
                                     "solar_today_estimated_energy", "solar_today_actual_energy")}
        for raw, expected in (
            ({4019: 123000, 4023: 235000, 4028: 0, 4032: 0}, (123, 235, 0, 0)),
            ({4019: 124000, 4023: 230000, 4028: 1100, 4032: 2200}, (124, 230, 1.1, 2.2)),
        ):
            client.daily.update(raw)
            await coordinator.async_refresh()
            self.assertEqual(tuple(entity.native_value for entity in daily_sensors.values()), expected)
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.native_value, -1)
        self.assertTrue(derived.available)
        self.assertEqual(derived.native_value, 1)
        client.online = 0
        client.calls.clear()
        await coordinator.async_refresh()
        self.assertFalse(sensor.available)
        self.assertFalse(derived.available)
        self.assertTrue(all(not entity.available for entity in daily_sensors.values()))
        self.assertEqual(coordinator.data["main_l1_power_rt"], 100)
        self.assertTrue(all(address < 4000 for address, _ in client.calls))
        client.online = 1
        client.daily.update({4019: 125000, 4023: 229000, 4027: 0xFF9C, 4028: 3500, 4032: 4500})
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data["solar_today_performance_ratio"], -10)
        self.assertTrue(all(entity.available for entity in daily_sensors.values()))
        self.assertEqual(tuple(entity.native_value for entity in daily_sensors.values()), (125, 229, 3.5, 4.5))
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.unique_id, identity)
