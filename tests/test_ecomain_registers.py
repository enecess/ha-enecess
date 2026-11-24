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
    # Storage is exercised with real HA objects by the compatibility suite.
    module("register_test.ecomain.energy", CloudEnergyStore=object)
    classes = "POWER ENERGY REACTIVE_ENERGY APPARENT_POWER REACTIVE_POWER VOLTAGE CURRENT POWER_FACTOR FREQUENCY IRRADIANCE TEMPERATURE".split()
    description = make_dataclass("SensorEntityDescription", [(name, object, None) for name in (
        "key", "name", "native_unit_of_measurement", "device_class", "state_class", "suggested_display_precision", "translation_key"
    )], frozen=True, kw_only=True)
    module("homeassistant.components.sensor", SensorDeviceClass=SimpleNamespace(**{k: k.lower() for k in classes}),
           SensorEntityDescription=description, SensorStateClass=SimpleNamespace(MEASUREMENT="measurement", TOTAL_INCREASING="total_increasing"))
    module("homeassistant.const", UnitOfPower=SimpleNamespace(WATT="W"), UnitOfEnergy=SimpleNamespace(WATT_HOUR="Wh"))
    module("homeassistant.config_entries", ConfigEntry=object)
    module("homeassistant.core", HomeAssistant=object)
    module("homeassistant.exceptions", ConfigEntryAuthFailed=RuntimeError)

    class Coordinator:
        def __init__(self, *args, **kwargs):
            self._shutdown_requested = False

        async def async_shutdown(self):
            self._shutdown_requested = True

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
            "sub3_ch10_reactive_energy_fwd_total": (540, 4, .001, False),
            "sub3_ch10_reactive_energy_rev_total": (700, 4, .001, False),
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

    def test_all_local_meter_descriptions_follow_register_resolution(self):
        expected = {
            "power": 2,
            "energy_forward": 3,
            "energy_reverse": 3,
            "reactive_energy_forward": 3,
            "reactive_energy_reverse": 3,
            "apparent_energy": 3,
            "reactive_power": 2,
            "apparent_power": 2,
            "voltage": 2,
            "current": 2,
            "power_factor": 2,
            "frequency": 2,
        }
        specs = self.model.build_specs_local([1, 2, 3], list(expected))
        descriptions = self.model.build_sensor_descriptions(specs)
        self.assertEqual({desc.spec.measurement_type for desc in descriptions}, set(expected))
        for desc in descriptions:
            with self.subTest(key=desc.key):
                self.assertEqual(desc.suggested_display_precision, expected[desc.spec.measurement_type])

    def test_physical_precision_handles_address_zero_and_integral_scales(self):
        for address, scale, expected in ((0, 1.0, 0), (0, .01, 2), (12, .1, 1),
                                         (12, .001, 3), (12, 10.0, 0), (12, 1000.0, 0)):
            with self.subTest(address=address, scale=scale):
                spec = self.model.RegisterSpec(key="fictional_register", kind="power",
                                               device_index=0, address=address, regs=1, scale=scale)
                description, = self.model.build_sensor_descriptions([spec])
                self.assertEqual(description.suggested_display_precision, expected)

    def test_cloud_descriptions_keep_three_decimal_default(self):
        specs = self.model.build_specs_cloud([1, 2, 3], ["power", "energy"])
        descriptions = self.model.build_sensor_descriptions(specs)
        self.assertEqual({desc.spec.kind for desc in descriptions},
                         {"power", "energy_delta", "energy_accumulated"})
        for desc in descriptions:
            with self.subTest(key=desc.key):
                self.assertEqual(desc.suggested_display_precision, 3)

    def test_descriptions_keep_reactive_energy_out_of_active_energy_class(self):
        specs = self.model.build_specs_local([], ["reactive_energy_forward", "power_factor", "apparent_power"])
        descriptions = {d.key: d for d in self.model.build_sensor_descriptions(specs)}
        self.assertEqual(descriptions["main_l1_reactive_energy_fwd_total"].native_unit_of_measurement, "varh")
        self.assertEqual(descriptions["main_l1_reactive_energy_fwd_total"].device_class, "reactive_energy")
        self.assertEqual(descriptions["main_l1_power_factor_rt"].native_unit_of_measurement, None)
        self.assertEqual(descriptions["main_l1_apparent_power_rt"].device_class, "apparent_power")

    def test_read_blocks_respect_energy_regions_and_merge_selected_neighbors(self):
        for addresses, expected in (
            ((348, 352), [(348, 4), (352, 4)]),
            ((700, 704), [(700, 4), (704, 4)]),
            ((344, 348), [(344, 8)]),
            ((352, 356, 380, 384, 540, 544), [(352, 36), (540, 8)]),
            ((696, 700), [(696, 8)]),
            ((704, 708, 716, 720), [(704, 20)]),
            ((348, 356), [(348, 4), (356, 4)]),
            ((700, 708), [(700, 4), (708, 4)]),
        ):
            with self.subTest(addresses=addresses):
                specs = [
                    self.model.RegisterSpec(key=f"fictional_{address}", kind="energy",
                                            device_index=0, address=address, regs=4)
                    for address in (*reversed(addresses), addresses[-1])
                ]
                self.assertEqual(self.coordinator.build_read_blocks(specs), expected)

    def test_read_blocks_keep_meter_regions_separate(self):
        for pair in (
            ((876, 4), (900, 2)),
            ((986, 2), (1000, 2)),
            ((1086, 2), (1100, 2)),
            ((1186, 2), (1200, 1)),
            ((1328, 1), (1400, 1)),
        ):
            with self.subTest(pair=pair):
                specs = [
                    self.model.RegisterSpec(
                        key=f"fictional_{address}", kind="power", device_index=0,
                        address=address, regs=width,
                    )
                    for address, width in pair
                ]
                self.assertEqual(self.coordinator.build_read_blocks(specs), list(pair))

    def test_default_solar_read_blocks_keep_unselected_gaps(self):
        self.assertEqual(
            self.coordinator.build_read_blocks(self.model.build_specs_local([4], [])),
            [(4000, 1), (4002, 1), (4004, 1), (4006, 4)],
        )


class MeterPollClient:
    """Serve synthetic firmware, online status, and meter data while recording reads."""

    def __init__(self, firmware=140, *, online=(0, 0, 0, 0), registers=None):
        self.firmware = firmware
        self.online = online
        self.registers = registers or {}
        self.calls = []

    async def async_set_target(self, host, port):
        pass

    async def read_holding_registers(self, start, count):
        self.calls.append((start, count))
        if start == 3009:
            return SimpleNamespace(registers=[self.firmware])
        if start == 3101:
            return SimpleNamespace(registers=list(self.online[:count]))
        return SimpleNamespace(
            registers=[self.registers.get(i, 0) for i in range(start, start + count)],
        )


class PollingTests(unittest.IsolatedAsyncioTestCase):
    async def test_steady_meter_poll_request_counts(self):
        model, coordinator = load_runtime()
        slave_combinations = ((), (1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3))
        entry = SimpleNamespace(data={"ecomain_host": "offline"})
        for measurements, expected_counts in (
            (None, [3, 4, 5, 5, 5, 5, 5, 5]),
            (model.LOCAL_MEASUREMENTS, [10, 11, 14, 15, 14, 15, 15, 15]),
        ):
            plans = {}
            for slaves in slave_combinations:
                specs = model.build_specs_local(list(slaves), measurements)
                client = MeterPollClient(online=tuple(int(i in slaves) for i in range(1, 5)))
                poller = coordinator.EcoMainModbusCoordinator(None, entry, client, specs)
                await poller._async_update_data()
                client.calls.clear()
                await poller._async_update_data()
                plans[slaves] = client.calls
            with self.subTest(measurements=measurements):
                self.assertEqual([len(plans[slaves]) for slaves in slave_combinations], expected_counts)
            if measurements is None:
                with self.subTest(default_slaves=(2,)):
                    self.assertEqual(
                        plans[(2,)],
                        [(3101, 4), (0, 72), (112, 120), (272, 40), (1000, 68)],
                    )
                with self.subTest(default_slaves=(1, 2, 3)):
                    self.assertEqual(
                        plans[(1, 2, 3)],
                        [(3101, 4), (0, 124), (124, 124), (248, 104), (1000, 88)],
                    )

    async def test_polling_selected_measurements_decodes_unsigned_and_signed(self):
        model, coordinator = load_runtime()
        specs = model.build_specs_local([], ["voltage", "power_factor", "frequency"])
        client = MeterPollClient(139, registers={1200: 50000, 1202: 0xFFA6, 1400: 5000})
        entry = SimpleNamespace(data={"ecomain_host": "offline"})
        poller = coordinator.EcoMainModbusCoordinator(None, entry, client, specs)
        values = await poller._async_update_data()
        self.assertEqual(values["main_l1_voltage_rt"], 500)
        self.assertEqual(values["main_l1_power_factor_rt"], -.9)
        self.assertEqual(values["main_frequency_rt"], 50)
        self.assertEqual(set(values), {spec.key for spec in specs})
        self.assertEqual(client.calls, [(3009, 1), (1200, 39), (1400, 1)])

    async def test_partial_meter_selections_plan_only_needed_reads(self):
        model, coordinator = load_runtime()
        entry = SimpleNamespace(data={"ecomain_host": "offline"})
        for slaves, measurements, online, expected in (
            ([3], ["voltage"], (0, 0, 1, 0), [(3101, 4), (1200, 37), (1299, 28)]),
            ([1, 2, 3], ["frequency"], (1, 1, 1, 0), [(1400, 1)]),
            ([1, 2, 3], [], (1, 1, 1, 0), []),
        ):
            with self.subTest(slaves=slaves, measurements=measurements):
                specs = model.build_specs_local(slaves, measurements)
                client = MeterPollClient(online=online)
                poller = coordinator.EcoMainModbusCoordinator(None, entry, client, specs)
                await poller._async_update_data()
                client.calls.clear()
                values = await poller._async_update_data()
                self.assertEqual(set(values), {spec.key for spec in specs})
                self.assertEqual(client.calls, expected)

    async def test_older_firmware_reads_default_meter_registers_for_selected_sub(self):
        model, coordinator = load_runtime()
        entry = SimpleNamespace(data={"ecomain_host": "offline"})
        specs = model.build_specs_local([2], model.LOCAL_MEASUREMENTS)
        default_keys = {spec.key for spec in model.build_specs_local([2])}
        for firmware in (136, 138):
            with self.subTest(firmware=firmware):
                client = MeterPollClient(firmware, online=(0, 1, 0))
                poller = coordinator.EcoMainModbusCoordinator(None, entry, client, specs)
                await poller._async_update_data()
                client.calls.clear()
                values = await poller._async_update_data()
                self.assertEqual(set(values), default_keys)
                self.assertEqual(
                    client.calls,
                    [(3101, 3), (0, 72), (112, 120), (272, 40), (1000, 68)],
                )

    async def test_read_blocks_do_not_split_uint64_or_cross_gaps(self):
        model, coordinator = load_runtime()
        specs = model.build_specs_local([1, 2, 3], ["energy_forward", "energy_reverse", "reactive_energy_forward", "reactive_energy_reverse", "apparent_energy"])
        blocks = coordinator.build_read_blocks(specs)
        self.assertTrue(all(1 <= count <= 125 for _, count in blocks))
        self.assertTrue(all(any(start <= s.address and s.address + s.regs <= start + count for start, count in blocks) for s in specs))
        covered = {i for start, count in blocks for i in range(start, start + count)}
        self.assertEqual(covered, set(range(880)))
        for boundary in (352, 704):
            with self.subTest(boundary=boundary):
                self.assertFalse(any(start < boundary < start + count for start, count in blocks))

    async def test_all_energy_polling_stays_within_device_regions(self):
        model, coordinator = load_runtime()
        specs = model.build_specs_local([1, 2, 3], ["energy_forward", "energy_reverse", "reactive_energy_forward", "reactive_energy_reverse", "apparent_energy"])
        wire_values = {
            348: [0xE240, 0x0001, 0, 0],
            352: [0xFBF1, 0x0009, 0, 0],
            700: [0xD687, 0x0012, 0, 0],
            704: [0xCBB1, 0x0074, 0, 0],
        }
        registers = {address + offset: value for address, words in wire_values.items()
                     for offset, value in enumerate(words)}

        class Client:
            async def async_set_target(self, host, port):
                pass

            async def read_holding_registers(self, start, count):
                if start == 3009:
                    return SimpleNamespace(registers=[139])
                if start == 3101:
                    return SimpleNamespace(registers=[1, 1, 1])
                if any(start < boundary < start + count for boundary in (352, 704)):
                    raise OSError(f"Read crosses energy region: ({start}, {count})")
                return SimpleNamespace(registers=[registers.get(i, 0) for i in range(start, start + count)])

        poller = coordinator.EcoMainModbusCoordinator(None, SimpleNamespace(data={"ecomain_host": "offline"}), Client(), specs)
        values = await poller._async_update_data()
        self.assertEqual(set(values), {spec.key for spec in specs})
        for key, expected in (
            ("sub3_ch10_energy_rev_total", 123.456),
            ("main_l1_reactive_energy_fwd_total", 654.321),
            ("sub3_ch10_reactive_energy_rev_total", 1234.567),
            ("main_l1_apparent_energy_total", 7654.321),
        ):
            with self.subTest(key=key):
                self.assertAlmostEqual(values[key], expected)

    async def test_firmware_capabilities_filter_reads_and_restore_after_target_change(self):
        model, coordinator = load_runtime()
        self.assertEqual(model.available_local_measurements(None), ("power", "energy_forward", "energy_reverse"))
        for firmware in (135, 136, 138, 139, 140):
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
