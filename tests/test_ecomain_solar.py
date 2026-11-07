"""Offline solar protocol and formula-source boundary regressions."""

from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from flow_test_support import load_flow
from test_ecomain_registers import load_runtime


# Literal, hand-checked protocol expectations, independent of production layouts.
SOLAR = {
    "solar_irradiance": (4000, 1, .1, True, "irradiance", "W/m²", "irradiance", "Irradiance", "measurement"),
    "solar_tilt_angle": (4004, 1, .1, True, "tilt_angle", "°", None, "Tilt Angle", "measurement"),
    "solar_module_temperature": (4002, 1, .1, True, "temperature", "°C", "temperature", "Module Temperature", "measurement"),
    "solar_actual_power": (4008, 2, .01, True, "power", "W", "power", "Actual Power", "measurement"),
    "solar_estimated_power": (4006, 2, .01, True, "power", "W", "power", "Estimated Power", "measurement"),
    "solar_performance_ratio": (4005, 1, .1, True, "performance_ratio", "%", None, "Performance Ratio", "measurement"),
    "solar_actual_energy": (4014, 4, .001, False, "energy", "Wh", "energy", "Cumulative Actual Energy", "total_increasing"),
    "solar_estimated_energy": (4010, 4, .001, False, "energy", "Wh", "energy", "Cumulative Estimated Energy", "total_increasing"),
    "solar_yesterday_performance_ratio": (4018, 1, .1, True, "performance_ratio", "%", None, "Yesterday Performance Ratio", None),
    "solar_yesterday_estimated_energy": (4019, 4, .001, False, "energy", "Wh", "energy", "Yesterday Estimated Energy", None),
    "solar_yesterday_actual_energy": (4023, 4, .001, False, "energy", "Wh", "energy", "Yesterday Actual Energy", None),
    "solar_today_performance_ratio": (4027, 1, .1, True, "performance_ratio", "%", None, "Today Performance Ratio", None),
    "solar_today_estimated_energy": (4028, 4, .001, False, "energy", "Wh", "energy", "Today Estimated Energy", "total_increasing"),
    "solar_today_actual_energy": (4032, 4, .001, False, "energy", "Wh", "energy", "Today Actual Energy", "total_increasing"),
}


def local_data(version=140):
    return {"device_type": "ecomain", "mode": "local", "ecomain_serial": "FICTIONAL-SOLAR-001",
            "ecomain_host": "192.0.2.44", "ecomain_firmware_version": version,
            "ecomain_selected_slaves": [1, 4]}


class SolarModelTests(unittest.TestCase):
    def setUp(self):
        load_flow(self)
        self.extra = import_module("custom_components.enecess.extra")
        self.model = import_module("custom_components.enecess.ecomain.model")

    def test_solar_only_selection_keeps_key_names_and_human_measurement_labels(self):
        descriptions = self.extra.build_entry_descriptions(local_data(), {
            "measurement_types": [], "solar_measurement_types": list(SOLAR)})
        self.assertEqual([desc.key for desc in descriptions], list(SOLAR))
        strings = json.loads((Path(__file__).resolve().parents[1] /
                              "custom_components/enecess/strings.json").read_text())
        for desc in descriptions:
            with self.subTest(key=desc.key):
                address, width, scale, signed, kind, unit, device_class, name, state_class = SOLAR[desc.key]
                self.assertEqual((desc.spec.address, desc.spec.regs, desc.spec.scale,
                                  desc.spec.signed, desc.spec.kind, desc.spec.device_index,
                                  desc.spec.measurement_type),
                                 (address, width, scale, signed, kind, 4, desc.key))
                self.assertEqual((desc.native_unit_of_measurement, desc.device_class), (unit, device_class))
                self.assertEqual(desc.state_class, state_class)
                self.assertEqual(desc.name, desc.key)
                self.assertIsNone(desc.translation_key)
                self.assertEqual(strings["selector"]["solar_measurement_types"]["options"][desc.key], name)

    def test_all_solar_descriptions_follow_register_resolution(self):
        expected = {
            "solar_irradiance": 1,
            "solar_tilt_angle": 1,
            "solar_module_temperature": 1,
            "solar_actual_power": 2,
            "solar_estimated_power": 2,
            "solar_performance_ratio": 1,
            "solar_actual_energy": 3,
            "solar_estimated_energy": 3,
            "solar_yesterday_performance_ratio": 1,
            "solar_yesterday_estimated_energy": 3,
            "solar_yesterday_actual_energy": 3,
            "solar_today_performance_ratio": 1,
            "solar_today_estimated_energy": 3,
            "solar_today_actual_energy": 3,
        }
        specs = self.model.build_specs_local([4], [], list(expected))
        descriptions = self.model.build_sensor_descriptions(specs)
        self.assertEqual({desc.key for desc in descriptions}, set(expected))
        for desc in descriptions:
            with self.subTest(key=desc.key):
                self.assertEqual(desc.suggested_display_precision, expected[desc.key])

    def test_index_four_never_expands_into_meter_channels(self):
        specs = self.model.build_specs_local([1, 4], ["power"])
        self.assertFalse(any(spec.key.startswith("sub4_") for spec in specs))
        self.assertTrue(any(spec.key == "sub1_ch10_power_rt" for spec in specs))
        self.assertEqual({spec.key for spec in specs if spec.device_index == 4}, set(list(SOLAR)[:5]))

    def test_solar_defaults_explicit_empty_and_deselection_are_distinct(self):
        defaults = self.extra.build_entry_specs(local_data(), {"measurement_types": []})
        self.assertEqual([spec.key for spec in defaults], list(SOLAR)[:5])
        self.assertEqual(self.extra.build_entry_specs(local_data(), {
            "measurement_types": [], "solar_measurement_types": []}), [])
        deselected = self.extra.build_entry_specs(local_data(), {
            "ecomain_selected_slaves": [1], "measurement_types": [],
            "solar_measurement_types": list(SOLAR)})
        self.assertEqual(deselected, [])

    def test_firmware_capabilities_preserve_configured_solar_identities(self):
        options = {"measurement_types": [], "solar_measurement_types": ["solar_actual_power", "solar_today_actual_energy"]}
        expected = {"ecomain:FICTIONAL-SOLAR-001:sub_4:key_solar_actual_power:mode_local",
                    "ecomain:FICTIONAL-SOLAR-001:sub_4:key_solar_today_actual_energy:mode_local"}
        for version in (136, 138, 139, None, 140, 145):
            with self.subTest(version=version):
                data = local_data(version)
                specs = self.extra.build_entry_specs(data, options)
                self.assertEqual({spec.key for spec in specs},
                                 {"solar_actual_power", "solar_today_actual_energy"} if version is not None and version >= 140 else set())
                self.assertEqual(self.extra.build_entry_sensor_unique_ids(data, options), expected)
                self.assertIn(("enecess", "ecomain:FICTIONAL-SOLAR-001:sub_4:mode_local"),
                              self.extra.build_entry_device_identifiers(data, options))
        self.assertEqual(self.extra.build_entry_sensor_unique_ids(local_data(), {
            **options, "ecomain_selected_slaves": []}), set())

    def test_cloud_and_old_meter_identities_stay_unchanged(self):
        data = {**local_data(), "ecomain_selected_slaves": [1]}
        options = {"measurement_types": ["power"], "solar_measurement_types": list(SOLAR)}
        self.assertIn("ecomain:FICTIONAL-SOLAR-001:sub_1:key_sub1_ch1_power_rt:mode_local",
                      self.extra.build_entry_sensor_unique_ids(data, options))
        data.update(mode="cloud", ecomain_selected_slaves=[1])
        ids = self.extra.build_entry_sensor_unique_ids(data, options)
        self.assertIn("ecomain:FICTIONAL-SOLAR-001:sub_1:key_sub1_ch1_power_avg_1m:mode_cloud", ids)
        self.assertFalse(any("solar" in key for key in ids))

    def test_solar_input_groups_allow_number_without_adding_result_types(self):
        mixin = import_module("custom_components.enecess.formula_flow").FormulaFlowMixin

        class Flow(mixin):
            _formula_context = (local_data(), {"measurement_types": [], "solar_measurement_types": list(SOLAR)})

        flow = Flow()
        self.assertEqual({kind: set(sources) for kind, sources in flow._formula_source_groups().items()}, {
            "irradiance": {"solar_irradiance"}, "tilt_angle": {"solar_tilt_angle"},
            "temperature": {"solar_module_temperature"},
            "power": {"solar_actual_power", "solar_estimated_power"},
            "performance_ratio": {"solar_performance_ratio", "solar_yesterday_performance_ratio", "solar_today_performance_ratio"},
            "energy": {"solar_actual_energy", "solar_estimated_energy", "solar_yesterday_actual_energy", "solar_yesterday_estimated_energy", "solar_today_actual_energy", "solar_today_estimated_energy"}})
        self.assertEqual(flow._formula_result_types(), ["power", "energy", "number"])
        flow._formula_context = (local_data(), {"measurement_types": [], "solar_measurement_types": ["solar_tilt_angle"]})
        self.assertEqual(flow._formula_result_types(), ["number"])
        self.assertEqual({kind: set(sources) for kind, sources in flow._formula_source_groups().items()},
                         {"tilt_angle": {"solar_tilt_angle"}})


class SolarPollingTests(unittest.IsolatedAsyncioTestCase):
    async def test_validation_rejects_malformed_firmware_at_client_boundary(self):
        module = load_flow(self)
        validate = import_module("custom_components.enecess.local_validation").async_validate_local_device

        class Transport:
            connected = True

            async def read_holding_registers(self, *, address, count, device_id):
                self.calls.append((address, count))
                return SimpleNamespace(registers=self.firmware, isError=lambda: False)

            def close(self):
                self.connected = False

        for firmware in (["140"], [140, 140], [140.5], [65676], [True], [None], []):
            with self.subTest(firmware=firmware):
                transport = Transport()
                transport.firmware = firmware
                transport.calls = []
                client = module.EnecessModbusClient("192.0.2.1", 502)
                client._client = transport
                result = await validate(client, firmware_register=3009, minimum_firmware=136,
                                        slave_register_start=3101, slave_register_count=3,
                                        allowed_slaves={"1", "2", "3", "4"}, firmware_timeout=5)
                self.assertEqual(result.error, "cannot_connect_local")
                self.assertEqual(transport.calls, [(3009, 1)])
                self.assertFalse(transport.connected)

    async def test_firmware_gate_and_online_recovery(self):
        model, runtime = load_runtime()
        specs = model.build_specs_local([1, 4], ["power"], list(SOLAR))

        class Client:
            version = 140
            online = [1, 0, 0, 1]
            calls = []
            performance_ratio = 987
            today_performance_ratio = 876
            yesterday_estimated = 123456
            yesterday_actual = 234567
            today_estimated = 345678
            today_actual = 456789

            async def async_set_target(self, host, port):
                pass

            async def read_holding_registers(self, start, count):
                self.calls.append((start, count))
                if start == 3009:
                    return SimpleNamespace(registers=[self.version] if self.version is not None else [])
                if start == 3101:
                    return SimpleNamespace(registers=self.online[:count])
                values = {1000: 12300, 4000: 0, 4002: 0xFF85, 4004: 150,
                          4005: self.performance_ratio, 4006: 45678, 4007: 0,
                          4008: 0xFF9C, 4009: 0xFFFF, 4010: 0, 4011: 0,
                          4012: 0, 4013: 0x8000, 4014: 1001, 4015: 0,
                          4016: 0, 4017: 0, 4018: 0xFF85,
                          4027: self.today_performance_ratio}
                values.update({address + word: (value >> (word * 16)) & 0xFFFF
                               for address, value in ((4019, self.yesterday_estimated),
                                                      (4023, self.yesterday_actual),
                                                      (4028, self.today_estimated),
                                                      (4032, self.today_actual))
                               for word in range(4)})
                return SimpleNamespace(registers=[values.get(i, 0) for i in range(start, start + count)])

        client = Client()
        client.calls = []
        entry = SimpleNamespace(data=local_data())
        coordinator = runtime.EcoMainModbusCoordinator(None, entry, client, specs)
        values = await coordinator._async_update_data()
        self.assertTrue(set(SOLAR).issubset(values))
        self.assertIn("solar_module_temperature", values)
        self.assertEqual(values["solar_irradiance"], 0)
        self.assertEqual(values["solar_tilt_angle"], 15)
        self.assertAlmostEqual(values["solar_performance_ratio"], 98.7)
        self.assertEqual(values["solar_module_temperature"], -12.3)
        self.assertEqual(values["solar_actual_power"], -1)
        self.assertAlmostEqual(values["solar_estimated_power"], 456.78)
        self.assertAlmostEqual(values["solar_actual_energy"], 1.001)
        self.assertEqual(values["solar_estimated_energy"], 9223372036854776.0)
        self.assertEqual(values["solar_yesterday_performance_ratio"], -12.3)
        self.assertAlmostEqual(values["solar_yesterday_estimated_energy"], 123.456)
        self.assertAlmostEqual(values["solar_yesterday_actual_energy"], 234.567)
        self.assertAlmostEqual(values["solar_today_performance_ratio"], 87.6)
        self.assertAlmostEqual(values["solar_today_estimated_energy"], 345.678)
        self.assertAlmostEqual(values["solar_today_actual_energy"], 456.789)
        self.assertEqual([call for call in client.calls if call[0] >= 4000],
                         [(4000, 1), (4002, 1), (4004, 32)])
        self.assertIn((3101, 4), client.calls)
        covered = {index for start, count in client.calls for index in range(start, start + count)}
        self.assertTrue({4001, 4003}.isdisjoint(covered))
        self.assertTrue(all(count <= 125 for _, count in client.calls))
        self.assertTrue(all(any(start <= spec.address and spec.address + spec.regs <= start + count
                                for start, count in client.calls) for spec in specs))
        for yesterday_estimated, yesterday_actual, today_estimated, today_actual in (
            (123000, 235000, 0, 0), (124000, 230000, 1100, 2200)
        ):
            client.yesterday_estimated = yesterday_estimated
            client.yesterday_actual = yesterday_actual
            client.today_estimated = today_estimated
            client.today_actual = today_actual
            values = await coordinator._async_update_data()
            self.assertEqual(values["solar_yesterday_estimated_energy"], yesterday_estimated * .001)
            self.assertEqual(values["solar_yesterday_actual_energy"], yesterday_actual * .001)
            self.assertEqual(values["solar_today_estimated_energy"], today_estimated * .001)
            self.assertEqual(values["solar_today_actual_energy"], today_actual * .001)
        client.online = [1, 0, 0, 0]
        client.calls.clear()
        values = await coordinator._async_update_data()
        self.assertNotIn("solar_actual_power", values)
        self.assertEqual(values["main_l1_power_rt"], 123)
        self.assertTrue(all(start < 4000 for start, _ in client.calls))
        client.online[-1] = 1
        client.performance_ratio = 0xFF85
        client.today_performance_ratio = 0xFF9C
        client.today_actual = 3500
        client.yesterday_actual = 229000
        values = await coordinator._async_update_data()
        self.assertIn("solar_actual_power", values)
        self.assertEqual(values["solar_performance_ratio"], -12.3)
        self.assertEqual(values["solar_today_performance_ratio"], -10)
        self.assertEqual(values["solar_today_actual_energy"], 3.5)
        self.assertEqual(values["solar_yesterday_actual_energy"], 229)
        self.assertEqual(len(coordinator.specs), len(specs))
        for version in (139, 138):
            with self.subTest(version=version):
                client.version = version
                entry.data["ecomain_host"] = f"offline-{version}"
                client.calls.clear()
                values = await coordinator._async_update_data()
                self.assertNotIn("solar_actual_power", values)
                self.assertIn((3101, 3), client.calls)
                self.assertTrue(all(start < 4000 for start, _ in client.calls))

    async def test_partial_daily_selection_reads_complete_values_without_reserved_words(self):
        model, runtime = load_runtime()

        class Client:
            async def async_set_target(self, host, port):
                pass

            async def read_holding_registers(self, start, count):
                self.calls.append((start, count))
                if start == 3009:
                    return SimpleNamespace(registers=[140])
                if start == 3101:
                    return SimpleNamespace(registers=[0, 0, 0, 1])
                values = {4000: 123, 4018: 0xFF9C, 4023: 1001, 4026: 0x8000,
                          4027: 321, 4032: 7654}
                return SimpleNamespace(registers=[values.get(i, 0) for i in range(start, start + count)])

        for selected, blocks, expected in (
            (["solar_irradiance", "solar_yesterday_performance_ratio", "solar_yesterday_actual_energy"],
             [(4000, 1), (4018, 1), (4023, 4)],
             {"solar_irradiance": 12.3, "solar_yesterday_performance_ratio": -10,
              "solar_yesterday_actual_energy": 9223372036854776.0}),
            (["solar_today_performance_ratio", "solar_today_actual_energy"],
             [(4027, 1), (4032, 4)],
             {"solar_today_performance_ratio": 32.1, "solar_today_actual_energy": 7.654}),
        ):
            with self.subTest(selected=selected):
                client = Client()
                client.calls = []
                coordinator = runtime.EcoMainModbusCoordinator(
                    None, SimpleNamespace(data=local_data()), client,
                    model.build_specs_local([4], [], selected))
                self.assertEqual(await coordinator._async_update_data(), expected)
                self.assertEqual([call for call in client.calls if call[0] >= 4000], blocks)

    async def test_validation_reads_four_statuses_only_after_confirmed_firmware_140(self):
        load_flow(self)
        validate = import_module("custom_components.enecess.local_validation").async_validate_local_device

        class Client:
            calls = []
            closed = False

            async def read_holding_registers(self, start, count):
                self.calls.append((start, count))
                return SimpleNamespace(registers=[self.version] if start == 3009 else [1, 0, 0, 1][:count])

            async def async_close(self):
                self.closed = True

        for version in (139, 140, 145):
            for allowed in ({"1", "2", "3"}, {"1", "2", "3", "4"}):
                with self.subTest(version=version, allowed=allowed):
                    client = Client()
                    client.version = version
                    client.calls = []
                    result = await validate(client, firmware_register=3009, minimum_firmware=136,
                                            slave_register_start=3101, slave_register_count=3,
                                            allowed_slaves=allowed, firmware_timeout=5)
                    self.assertEqual(client.calls, [(3009, 1), (3101, 4 if version >= 140 else 3)])
                    self.assertEqual(result.online_slaves, ["1", "4"] if version >= 140 and "4" in allowed else ["1"])
                    self.assertTrue(client.closed)

    async def test_validation_rejects_incomplete_or_invalid_fourth_status(self):
        module = load_flow(self)
        validate = import_module("custom_components.enecess.local_validation").async_validate_local_device

        class Transport:
            connected = True

            async def read_holding_registers(self, *, address, count, device_id):
                return SimpleNamespace(registers=[140] if address == 3009 else self.status, isError=lambda: False)

            def close(self):
                self.connected = False

        for status in ([1, 0, 0], [1, 0, 0, True], [1, 0, 0, 2], [1, 0, 0, None]):
            with self.subTest(status=status):
                transport = Transport()
                transport.status = status
                client = module.EnecessModbusClient("192.0.2.1", 502)
                client._client = transport
                result = await validate(client, firmware_register=3009, minimum_firmware=136,
                                        slave_register_start=3101, slave_register_count=3,
                                        allowed_slaves={"1", "2", "3", "4"}, firmware_timeout=5)
                self.assertEqual(result.error, "cannot_connect_local")
                self.assertEqual(result.firmware_version, 140)
                self.assertFalse(transport.connected)
