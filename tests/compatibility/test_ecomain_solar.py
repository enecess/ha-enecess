"""Solar metadata, child identity and availability with real HA entities."""

from types import SimpleNamespace

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.enecess.ecomain.coordinator import EcoMainModbusCoordinator
from custom_components.enecess.ecomain.sensor import EcoMainExtraSensor, EcoMainSensor
from custom_components.enecess.extra import build_entry_descriptions, build_entry_specs
import test_runtime as runtime_fixture


class SolarClient:
    """Return synthetic local measurements with a controllable solar status."""

    def __init__(self):
        self.online = 1
        self.calls = []

    async def async_set_target(self, host, port):
        pass

    async def read_holding_registers(self, address, count):
        self.calls.append((address, count))
        if address == 3009:
            return SimpleNamespace(registers=[140])
        if address == 3101:
            return SimpleNamespace(registers=[1, 0, 0, self.online])
        values = {1000: 10000, 4000: 1000, 4002: 0xFF9C, 4004: 200,
                  4006: 1000, 4010: 0xFC18, 4011: 0xFFFF, 4012: 0xFFFF, 4013: 0xFFFF}
        return SimpleNamespace(registers=[values.get(i, 0) for i in range(address, address + count)])


class SolarRuntimeTests(runtime_fixture.RealHARuntimeFixture):
    async def test_metadata_device_ownership_and_offline_recovery_keep_identity(self):
        entry = self.make_entry("local")
        data = {**entry.data, "ecomain_firmware_version": 140, "ecomain_selected_slaves": [1, 4]}
        options = {"measurement_types": ["power"], "solar_measurement_types": [
            "solar_irradiance", "solar_tilt_angle", "solar_module_temperature",
            "solar_actual_power", "solar_estimated_power", "solar_performance_ratio",
            "solar_actual_energy", "solar_estimated_energy"]}
        descriptions = {desc.key: desc for desc in build_entry_descriptions(data, options)}
        self.assertIn("solar_actual_power", descriptions)
        self.assertEqual(descriptions["solar_irradiance"].device_class, SensorDeviceClass.IRRADIANCE)
        self.assertEqual(descriptions["solar_module_temperature"].device_class, SensorDeviceClass.TEMPERATURE)
        self.assertEqual(descriptions["solar_actual_energy"].state_class, SensorStateClass.TOTAL_INCREASING)
        self.assertIsNone(descriptions["solar_performance_ratio"].device_class)
        self.assertEqual(descriptions["solar_tilt_angle"].native_unit_of_measurement, "°")
        self.assertEqual(descriptions["solar_tilt_angle"].state_class, SensorStateClass.MEASUREMENT)
        self.assertEqual(descriptions["solar_actual_power"].translation_key, "solar_actual_power")
        self.assertIsNone(descriptions["solar_actual_power"].name)
        client = SolarClient()
        coordinator = EcoMainModbusCoordinator(self.hass, entry, client, build_entry_specs(data, options))
        self.addAsyncCleanup(coordinator.async_shutdown)
        sensor = EcoMainSensor(coordinator, "local", runtime_fixture.SERIAL, descriptions["solar_actual_power"])
        derived = EcoMainExtraSensor(coordinator, "local", runtime_fixture.SERIAL, {
            "key": "extra_solar_abs", "name": "Fictional positive output", "operation": "absolute",
            "sources": ["solar_actual_power"]}, descriptions["solar_actual_power"], 4)
        for entity in (sensor, derived):
            self.assertEqual(entity.device_info["model"], "ecoSolarMonitor")
            self.assertEqual(entity.device_info["name"], f"ecoSolarMonitor {runtime_fixture.SERIAL} (Local)")
            self.assertEqual(entity.device_info["via_device"], ("enecess", f"ecomain:{runtime_fixture.SERIAL}:mode_local"))
        identity = sensor.unique_id
        self.assertEqual(identity, f"ecomain:{runtime_fixture.SERIAL}:sub_4:key_solar_actual_power:mode_local")
        await coordinator.async_refresh()
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.native_value, -1)
        self.assertTrue(derived.available)
        self.assertEqual(derived.native_value, 1)
        client.online = 0
        client.calls.clear()
        await coordinator.async_refresh()
        self.assertFalse(sensor.available)
        self.assertFalse(derived.available)
        self.assertEqual(coordinator.data["main_l1_power_rt"], 100)
        self.assertTrue(all(address < 4000 for address, _ in client.calls))
        client.online = 1
        await coordinator.async_refresh()
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.unique_id, identity)
