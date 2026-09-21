"""Offline register mapping and polling regression tests."""
from dataclasses import make_dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch


def load_runtime():
    root = Path(__file__).resolve().parents[1] / "custom_components/enecess"
    modules = {}

    def module(name, **attrs):
        result = ModuleType(name)
        result.__dict__.update(attrs)
        modules[name] = result
        return result

    module("register_test", __path__=[str(root)], CONF_ECOMAIN_PORT=502)
    module("register_test.ecomain", __path__=[str(root / "ecomain")])
    classes = "POWER ENERGY REACTIVE_ENERGY APPARENT_POWER REACTIVE_POWER VOLTAGE CURRENT POWER_FACTOR FREQUENCY".split()
    description = make_dataclass("SensorEntityDescription", [(name, object, None) for name in (
        "key", "name", "native_unit_of_measurement", "device_class", "state_class", "suggested_display_precision"
    )], frozen=True, kw_only=True)
    module("homeassistant.components.sensor", SensorDeviceClass=SimpleNamespace(**{k: k.lower() for k in classes}),
           SensorEntityDescription=description, SensorStateClass=SimpleNamespace(MEASUREMENT="measurement", TOTAL_INCREASING="total_increasing"))
    module("homeassistant.const", UnitOfPower=SimpleNamespace(WATT="W"), UnitOfEnergy=SimpleNamespace(WATT_HOUR="Wh"))
    module("homeassistant.config_entries", ConfigEntry=object)
    module("homeassistant.core", HomeAssistant=object)

    class Coordinator:
        def __init__(self, *args, **kwargs):
            pass

        @classmethod
        def __class_getitem__(cls, item):
            return cls

    module("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=Coordinator, UpdateFailed=RuntimeError)
    module("register_test.client_api", EnecessApi=object, EnecessApiError=ValueError, EnecessAuthError=PermissionError)
    module("pymodbus", ModbusException=RuntimeError)
    module("pymodbus.client", AsyncModbusTcpClient=object)
    with patch.dict(sys.modules, modules):
        model = import_module("register_test.ecomain.model")
        coordinator = import_module("register_test.ecomain.coordinator")
    return model, coordinator


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.model, self.coordinator = load_runtime()

    def test_optional_quantities_follow_documented_last_channel_addresses(self):
        specs = self.model.build_specs_local([3], ["reactive_energy_forward", "reactive_energy_reverse", "apparent_power", "reactive_power", "voltage", "current", "power_factor", "frequency"])
        actual = {s.key: (s.address, s.regs, s.scale, s.signed) for s in specs}
        expected = {
            "sub3_ch10_reactive_energy_fwd_total": (688, 4, .001, False),
            "sub3_ch10_reactive_energy_rev_total": (848, 4, .001, False),
            "sub3_ch10_apparent_power_rt": (986, 2, .01, True),
            "sub3_ch10_reactive_power_rt": (1186, 2, .01, True),
            "sub3_ch10_voltage_rt": (1326, 1, .01, False),
            "sub3_ch10_current_rt": (1327, 1, .01, False),
            "sub3_ch10_power_factor_rt": (1328, 1, .01, True),
            "main_frequency_rt": (1400, 1, .01, False),
        }
        for key, value in expected.items():
            self.assertEqual(actual[key], value)
        self.assertFalse(any(s.key.startswith(("sub1_", "sub2_")) for s in specs))
        self.assertNotIn("main_all_voltage_rt", actual)

    def test_defaults_preserve_keys_and_cloud_energy_dependencies(self):
        specs = self.model.build_specs_local([])
        self.assertEqual(len(specs), 42)
        self.assertEqual({s.measurement_type for s in specs}, {"power", "energy_forward", "energy_reverse"})
        self.assertEqual(next(s.address for s in specs if s.key == "main_ch10_energy_rev_total"), 228)
        energy = self.model.build_specs_cloud([], ["energy"])
        self.assertEqual(len(energy), 22)
        self.assertEqual({s.kind for s in energy}, {"energy_delta", "energy_accumulated"})
        keys = {s.key for s in energy}
        self.assertTrue(all(s.source_key in keys for s in energy if s.kind == "energy_accumulated"))
        self.assertEqual(self.model.build_specs_local([], []), [])

    def test_descriptions_keep_reactive_energy_out_of_active_energy_class(self):
        specs = self.model.build_specs_local([], ["reactive_energy_forward", "power_factor", "apparent_power"])
        descriptions = {d.key: d for d in self.model.build_sensor_descriptions(specs)}
        self.assertEqual(descriptions["main_l1_reactive_energy_fwd_total"].native_unit_of_measurement, "varh")
        self.assertEqual(descriptions["main_l1_reactive_energy_fwd_total"].device_class, "reactive_energy")
        self.assertEqual(descriptions["main_l1_power_factor_rt"].native_unit_of_measurement, None)
        self.assertEqual(descriptions["main_l1_apparent_power_rt"].device_class, "apparent_power")


class PollingTests(unittest.IsolatedAsyncioTestCase):
    async def test_polling_only_selected_registers_decodes_unsigned_and_signed(self):
        model, coordinator = load_runtime()
        specs = model.build_specs_local([], ["voltage", "power_factor", "frequency"])
        calls = []

        class Client:
            async def async_set_target(self, host, port):
                pass

            async def read_holding_registers(self, start, count):
                if start == 3009:
                    return SimpleNamespace(registers=[139])
                calls.append((start, count))
                values = {1200: 50000, 1202: 0xFFA6, 1400: 5000}
                return SimpleNamespace(registers=[values.get(i, 0) for i in range(start, start + count)])

        poller = coordinator.EcoMainModbusCoordinator(None, SimpleNamespace(data={"ecomain_host": "offline"}), Client(), specs)
        values = await poller._async_update_data()
        self.assertEqual(values["main_l1_voltage_rt"], 500)
        self.assertEqual(values["main_l1_power_factor_rt"], -.9)
        self.assertEqual(values["main_frequency_rt"], 50)
        covered = {i for start, count in calls for i in range(start, start + count)}
        self.assertEqual(covered, {s.address for s in specs})

    async def test_short_read_fails_without_fabricating_energy(self):
        model, coordinator = load_runtime()

        class Client:
            async def async_set_target(self, host, port):
                pass

            async def read_holding_registers(self, start, count):
                if start == 3009:
                    return SimpleNamespace(registers=[139])
                return SimpleNamespace(registers=[1] * (count - 1))

        poller = coordinator.EcoMainModbusCoordinator(None, SimpleNamespace(data={"ecomain_host": "offline"}), Client(), model.build_specs_local([]))
        with self.assertRaisesRegex(RuntimeError, "[Ss]hort|[Ii]ncomplete"):
            await poller._async_update_data()

    async def test_read_blocks_do_not_split_uint64_or_cross_gaps(self):
        model, coordinator = load_runtime()
        specs = model.build_specs_local([1, 2, 3], ["energy_forward", "energy_reverse", "reactive_energy_forward", "reactive_energy_reverse"])
        blocks = coordinator.build_read_blocks(specs)
        self.assertTrue(all(count <= 125 for _, count in blocks))
        self.assertTrue(all(any(start <= s.address and s.address + s.regs <= start + count for start, count in blocks) for s in specs))
        covered = {i for start, count in blocks for i in range(start, start + count)}
        self.assertEqual(covered, set(range(352)) | set(range(500, 852)))

    async def test_firmware_capabilities_filter_reads_and_restore_after_target_change(self):
        model, coordinator = load_runtime()
        self.assertEqual(model.available_local_measurements(None), ("power", "energy_forward", "energy_reverse"))
        for firmware in (135, 136, 138, 139, 140, None, "139", True):
            with self.subTest(firmware=firmware):
                calls = []

                class Client:
                    async def async_set_target(self, host, port):
                        pass

                    async def read_holding_registers(self, start, count):
                        calls.append((start, count))
                        registers = [] if firmware is None else [firmware]
                        return SimpleNamespace(registers=registers if start == 3009 else [0] * count)

                entry = SimpleNamespace(data={"ecomain_host": "offline"})
                requested = model.build_specs_local([], ["power", "energy_forward", "frequency", "voltage"])
                poller = coordinator.EcoMainModbusCoordinator(None, entry, Client(), requested)
                if type(firmware) is int and firmware >= 136:
                    values = await poller._async_update_data()
                    extended = firmware >= 139
                    self.assertEqual(poller.firmware_version, firmware)
                    self.assertIn("main_l1_power_rt", values)
                    self.assertIn("main_l1_energy_fwd_total", values)
                    self.assertEqual("main_frequency_rt" in values, extended)
                    self.assertEqual("main_l1_voltage_rt" in values, extended)
                    if not extended:
                        self.assertTrue(all(start < 1100 for start, _ in calls[1:]))
                    calls.clear()
                    await poller._async_update_data()
                    self.assertNotIn((3009, 1), calls)
                    for version in (138, 139, 136, 140):
                        firmware = version
                        entry.data["ecomain_host"] = f"offline-{version}"
                        calls.clear()
                        values = await poller._async_update_data()
                        self.assertEqual(calls[0], (3009, 1))
                        self.assertEqual("main_frequency_rt" in values, version >= 139)
                        self.assertEqual(poller.firmware_version, version)
                else:
                    with self.assertRaises(RuntimeError):
                        await poller._async_update_data()
                    self.assertEqual(calls, [(3009, 1)])
