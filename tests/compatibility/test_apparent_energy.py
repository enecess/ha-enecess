"""Verify protocol 1.0.5 energy metadata and missing-channel availability."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.components.sensor import SensorStateClass

from custom_components.enecess.config_flow import ConfigFlow
from custom_components.enecess.ecomain.model import (
    available_local_measurements,
    build_sensor_descriptions,
    build_specs_local,
)
from custom_components.enecess.ecomain.sensor import EcoMainSensor, EcoMainExtraSensor
from custom_components.enecess.ecomain.coordinator import EcoMainModbusCoordinator
from test_runtime import RealHARuntimeFixture, SERIAL


class ApparentEnergyTests(RealHARuntimeFixture):
    async def test_poll_decodes_distinct_energy_registers_and_unsigned_high_bit(self):
        specs = build_specs_local(
            [],
            ["reactive_energy_forward", "reactive_energy_reverse", "apparent_energy"],
        )
        # Literal wire vectors distinguish each new bank and verify low-word first.
        wire = {
            352: [1000, 0, 0, 0],
            368: [2000, 0, 0, 0],
            384: [3000, 0, 0, 0],
            544: [4000, 0, 0, 0],
            704: [0x7788, 0x5566, 0x3344, 0x9122],
            720: [6000, 0, 0, 0],
        }
        registers = {
            address + i: word
            for address, words in wire.items()
            for i, word in enumerate(words)
        }

        async def read(address, count):
            return SimpleNamespace(
                registers=[139]
                if address == 3009
                else [registers.get(i, 0) for i in range(address, address + count)]
            )

        client = AsyncMock()
        client.read_holding_registers.side_effect = read
        coordinator = EcoMainModbusCoordinator(
            self.hass, self.make_entry("local"), client, specs
        )
        self.addAsyncCleanup(coordinator.async_shutdown)
        values = await coordinator._async_update_data()
        for key, expected in {
            "main_l1_reactive_energy_fwd_total": 1.0,
            "main_l1_reactive_energy_rev_total": 2.0,
            "main_ch1_reactive_energy_fwd_total": 3.0,
            "main_ch1_reactive_energy_rev_total": 4.0,
            "main_l1_apparent_energy_total": 0x9122334455667788 * 0.001,
            "main_ch1_apparent_energy_total": 6.0,
        }.items():
            self.assertEqual(values[key], expected)

    async def test_apparent_energy_metadata_and_formula_selection(self):
        self.assertIn("apparent_energy", available_local_measurements(139))
        self.assertNotIn("apparent_energy", available_local_measurements(138))
        specs = build_specs_local([1, 2, 3], ["apparent_energy"])
        self.assertEqual(len(specs), 44)
        descs = {d.key: d for d in build_sensor_descriptions(specs)}
        for key, address in {
            "main_l1_apparent_energy_total": 704,
            "main_all_apparent_energy_total": 716,
            "main_ch1_apparent_energy_total": 720,
            "sub1_ch1_apparent_energy_total": 760,
            "sub3_ch10_apparent_energy_total": 876,
        }.items():
            desc = descs[key]
            self.assertEqual(
                (desc.spec.address, desc.spec.regs, desc.spec.signed),
                (address, 4, False),
            )
            self.assertEqual(desc.spec.scale, 0.001)
            self.assertEqual(desc.native_unit_of_measurement, "VAh")
            self.assertIsNone(desc.device_class)
            self.assertEqual(desc.state_class, SensorStateClass.TOTAL_INCREASING)
        flow = ConfigFlow()
        flow.hass = self.hass
        flow._entry_data = {"mode": "manual", "ecomain_firmware_version": 139}
        flow._measurement_types = ["apparent_energy"]
        self.assertEqual(flow._formula_result_types(), ["apparent_energy", "number"])
        self.assertIn(
            "main_l1_apparent_energy_total",
            flow._formula_source_groups()["apparent_energy"],
        )

    async def test_formula_preserves_apparent_energy_units_and_total_semantics(self):
        coordinator = SimpleNamespace(data={"source": 12.5}, last_update_success=True)
        sensor = EcoMainExtraSensor(
            coordinator,
            "local",
            SERIAL,
            {
                "key": "extra_apparent",
                "operation": "formula",
                "sources": ["source"],
                "variables": {"a": "source"},
                "expression": "a * 2",
                "result_type": "apparent_energy",
            },
            None,
            0,
        )
        self.assertEqual(sensor.native_value, 25)
        self.assertEqual(sensor.native_unit_of_measurement, "VAh")
        self.assertIsNone(sensor.device_class)
        self.assertEqual(sensor.state_class, SensorStateClass.TOTAL)

    async def test_missing_subchannel_is_unavailable_until_value_returns(self):
        desc = build_sensor_descriptions(build_specs_local([1], ["power"]))[-1]
        coordinator = SimpleNamespace(data={}, last_update_success=True)
        sensor = EcoMainSensor(coordinator, "local", SERIAL, desc)
        self.assertFalse(sensor.available)
        coordinator.data[desc.key] = 0.0
        self.assertTrue(sensor.available)
        coordinator.last_update_success = False
        self.assertFalse(sensor.available)
