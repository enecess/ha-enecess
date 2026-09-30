"""Real HA ecoSub availability with synthetic protocol register responses."""

from types import SimpleNamespace

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.enecess.ecomain.coordinator import EcoMainModbusCoordinator
from custom_components.enecess.ecomain.model import (
    build_sensor_descriptions,
    build_specs_local,
)
from custom_components.enecess.ecomain.sensor import EcoMainSensor, EcoMainExtraSensor
import test_runtime as runtime_fixture


class RegisterClient:
    """Return stale measurements even when a fictional ecoSub is offline."""

    def __init__(self):
        self.online = [0, 0, 1]
        self.calls = []

    async def async_set_target(self, host, port):
        pass

    async def read_holding_registers(self, address, count):
        self.calls.append((address, count))
        if address == 3009:
            return SimpleNamespace(registers=[139])
        if address == 3101:
            return SimpleNamespace(registers=self.online)
        values = {}
        for start in range(1000, 1088, 2):
            raw = start * 100
            values[start] = raw & 0xFFFF
            values[start + 1] = raw >> 16
        return SimpleNamespace(
            registers=[values.get(index, 0) for index in range(address, address + count)]
        )


class EcoSubOnlineTests(runtime_fixture.RealHARuntimeFixture):
    def make_coordinator(self, slaves=(1, 3)):
        entry = self.make_entry("local")
        client = RegisterClient()
        specs = build_specs_local(list(slaves), ["power"])
        coordinator = EcoMainModbusCoordinator(self.hass, entry, client, specs)
        self.addAsyncCleanup(coordinator.async_shutdown)
        return coordinator, client, specs

    async def test_offline_sub_is_not_read_or_published_and_other_devices_continue(self):
        coordinator, client, specs = self.make_coordinator()
        descriptions = build_sensor_descriptions(specs)
        sensors = {
            desc.key: EcoMainSensor(coordinator, "local", runtime_fixture.SERIAL, desc)
            for desc in descriptions
        }
        await coordinator.async_refresh()
        self.assertTrue(coordinator.last_update_success)
        self.assertNotIn("sub1_ch1_power_rt", coordinator.data)
        self.assertFalse(sensors["sub1_ch1_power_rt"].available)
        self.assertTrue(sensors["main_l1_power_rt"].available)
        self.assertTrue(sensors["sub3_ch1_power_rt"].available)
        self.assertEqual(coordinator.data["main_l1_power_rt"], 1000.0)
        self.assertEqual(coordinator.data["sub3_ch1_power_rt"], 1068.0)
        covered = {index for start, count in client.calls for index in range(start, start + count)}
        self.assertTrue({3101, 3102, 3103}.issubset(covered))
        self.assertTrue(set(range(1028, 1048)).isdisjoint(covered))
        self.assertTrue(set(range(1048, 1068)).isdisjoint(covered))
        identity = sensors["sub1_ch1_power_rt"].unique_id
        client.online = [1, 0, 1]
        await coordinator.async_refresh()
        self.assertEqual(coordinator.data["sub1_ch1_power_rt"], 1028.0)
        self.assertTrue(sensors["sub1_ch1_power_rt"].available)
        self.assertEqual(sensors["sub1_ch1_power_rt"].unique_id, identity)
        self.assertEqual(len(coordinator.specs), len(specs))

    async def test_cross_device_formula_unavailable_until_all_sources_online(self):
        coordinator, client, _ = self.make_coordinator()
        extra = EcoMainExtraSensor(
            coordinator,
            "local",
            runtime_fixture.SERIAL,
            {
                "key": "extra_formula_online_probe",
                "name": "Fictional combined power",
                "operation": "formula",
                "result_type": "power",
                "sources": ["main_l1_power_rt", "sub1_ch1_power_rt"],
                "variables": {"a": "main_l1_power_rt", "b": "sub1_ch1_power_rt"},
                "expression": "a + b",
            },
            None,
            0,
        )
        await coordinator.async_refresh()
        self.assertFalse(extra.available)
        self.assertIsNone(extra.native_value)
        client.online = [1, 0, 1]
        await coordinator.async_refresh()
        self.assertTrue(extra.available)
        self.assertEqual(extra.native_value, 2028.0)
        client.online = [0, 0, 1]
        await coordinator.async_refresh()
        self.assertFalse(extra.available)
        self.assertIsNone(extra.native_value)

    async def test_malformed_online_status_never_publishes_stale_sub_values(self):
        coordinator, client, _ = self.make_coordinator()
        for invalid in ([1], [True, 0, 1], [2, 0, 1], [1, None, 1]):
            with self.subTest(response=invalid):
                client.online = invalid
                with self.assertRaisesRegex(UpdateFailed, "ecoSub.*status"):
                    await coordinator._async_update_data()

    async def test_no_selected_sub_does_not_require_online_status_read(self):
        coordinator, client, _ = self.make_coordinator(slaves=())
        client.online = []
        await coordinator.async_refresh()
        self.assertTrue(coordinator.last_update_success)
        self.assertEqual(coordinator.data["main_l1_power_rt"], 1000.0)
        self.assertNotIn((3101, 3), client.calls)
