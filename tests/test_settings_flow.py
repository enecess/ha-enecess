"""Commission hardware with actual schemas and an in-memory Modbus transport."""

from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from flow_test_support import load_flow, submit_values
from test_ecomain_settings import Transport


class SettingsFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)
        self.transport = Transport()
        self.transport.values[3009] = 140
        client = self.module.EnecessModbusClient("fictional.invalid", 502)
        client._client = self.transport
        entry = SimpleNamespace(
            entry_id="fictional-settings-flow",
            data={
                "device_type": "ecomain",
                "mode": "manual",
                "ecomain_firmware_version": 140,
                "ecomain_serial": "FICTIONAL-SETTINGS-001",
                "ecomain_selected_slaves": [1, 4],
            },
            options={},
            runtime_data=SimpleNamespace(modbus_client=client),
        )
        self.flow = self.module.EnecessOptionsFlow(entry)
        self.flow._available_slaves = ["1", "2", "4"]
        self.flow._async_refresh_available_slaves = AsyncMock(return_value=None)

    async def submit(self, result, **values):
        return await getattr(self.flow, "async_step_" + result["step_id"])(
            submit_values(result, values)
        )

    async def open(self, action):
        result = await self.flow.async_step_init()
        offered = next(
            value.config["options"]
            for key, value in result["data_schema"].schema.items()
            if str(key) == "extra_action"
        )
        self.assertIn(action, offered)
        return await self.submit(result, extra_action=action)

    def assert_visible_errors(self, result):
        self.assertTrue(
            set(result["errors"]) <= {"base", *map(str, result["data_schema"].schema)}
        )

    async def test_channel_device_choices_and_ten_native_sections(self):
        result = await self.open("channel_configuration")
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(fields["channel_device"].config["options"], ["0", "1"])
        result = await self.submit(result, channel_device="0")
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(
            list(fields),
            [
                *[f"channel_{n}" for n in range(1, 11)],
                "main_transformers",
                "flow_action",
            ],
        )
        for n in range(1, 11):
            section = fields[f"channel_{n}"]
            self.assertTrue(section.options["collapsed"])
            controls = {str(key): value for key, value in section.schema.schema.items()}
            self.assertEqual(controls["phase"].config["options"], ["L1", "L2", "L3"])
            self.assertEqual(controls["transformer"].config["options"], ["30", "100"])
            self.assertEqual(controls["phase"].config["mode"], "dropdown")
        self.assertEqual(
            [
                value.config["options"]
                for value in fields["main_transformers"].schema.schema.values()
            ],
            [["100"], ["100"], ["100"]],
        )
        result = await self.submit(result, flow_action="back")
        result = await self.submit(result, channel_device="1")
        self.assertNotIn(
            "main_transformers", list(map(str, result["data_schema"].schema))
        )

    async def test_channel_unknown_choices_require_explicit_valid_selection(self):
        self.transport.values.update({2000: 3, 2043: 0, 2040: 0})
        result = await self.open("channel_configuration")
        result = await self.submit(result, channel_device="0")
        values = submit_values(result, {})
        self.assertNotIn("phase", values["channel_1"])
        self.assertNotIn("transformer", values["channel_1"])
        self.transport.commands.clear()
        result = await self.submit(
            result, main_transformers={"l1": "100", "l2": "100", "l3": "100"}
        )
        self.assertEqual(result["errors"], {"channel_1": "invalid_input"})
        self.assertEqual(self.transport.commands, [])
        values.update(
            channel_1={"phase": "L3", "transformer": "100"},
            main_transformers={"l1": "100", "l2": "100", "l3": "100"},
        )
        result = await self.submit(result, **values)
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(
            [self.transport.values[a] for a in (2000, 2043, 2040)], [2, 100, 100]
        )

    async def test_channel_partial_retry_retains_targets_and_reports_visible_groups(
        self,
    ):
        result = await self.open("channel_configuration")
        result = await self.submit(result, channel_device="0")
        self.transport.fail_writes.add(2000)
        self.transport.ignore_writes.add(2052)
        result = await self.submit(
            result,
            channel_1={"phase": "L2", "transformer": "100"},
            channel_10={"phase": "L3", "transformer": "100"},
        )
        self.assertEqual(
            result["errors"],
            {
                "channel_1": "settings_phase_write_failed",
                "channel_10": "settings_transformer_verify_failed",
            },
        )
        self.assert_visible_errors(result)
        self.assertEqual(
            submit_values(result, {})["channel_1"],
            {"phase": "L2", "transformer": "100"},
        )
        self.transport.fail_writes.clear()
        self.transport.ignore_writes.clear()
        self.transport.commands.clear()
        result = await self.submit(result)
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(
            [c[1] for c in self.transport.commands if c[0] == "write"], [2000, 2052]
        )

    async def test_channel_back_keeps_nested_values_and_changed_device_discards_them(
        self,
    ):
        result = await self.open("channel_configuration")
        result = await self.submit(result, channel_device="0")
        self.transport.commands.clear()
        result = await self.submit(
            result, channel_1={"phase": "L3", "transformer": "100"}, flow_action="back"
        )
        self.assertEqual(self.transport.commands, [])
        result = await self.submit(result, channel_device="0")
        self.assertEqual(
            submit_values(result, {})["channel_1"],
            {"phase": "L3", "transformer": "100"},
        )
        result = await self.submit(result, flow_action="back")
        result = await self.submit(result, channel_device="1")
        self.assertEqual(
            submit_values(result, {})["channel_1"], {"phase": "L1", "transformer": "30"}
        )

    async def test_initial_channel_read_retry_reads_without_writing(self):
        self.transport.fail_reads.add(2043)
        result = await self.open("channel_configuration")
        result = await self.submit(result, channel_device="0")
        self.assertEqual(result["errors"], {"base": "settings_read_failed"})
        self.assertEqual(list(map(str, result["data_schema"].schema)), ["flow_action"])
        self.transport.fail_reads.clear()
        result = await self.submit(result)
        self.assertFalse(result["errors"])
        self.assertTrue(all(c[0] == "read" for c in self.transport.commands))

    async def test_solar_uses_master_and_includes_online_unselected_sub_groups(self):
        self.flow._phase_device = 1
        self.flow._available_slaves = ["2"]
        result = await self.open("solar_configuration")
        self.assertEqual(result["step_id"], "solar_configuration")
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(
            list(fields),
            [
                "capacity",
                "temperature_coefficient",
                "inverter_channels_0",
                "inverter_channels_2",
                "flow_action",
            ],
        )
        self.assertEqual(
            fields["capacity"].config,
            {
                "min": 0,
                "max": 2147483647,
                "step": 1,
                "mode": "box",
                "unit_of_measurement": "W",
            },
        )
        self.assertEqual(
            fields["temperature_coefficient"].config["unit_of_measurement"], "%/°C"
        )
        self.transport.values.update({2110: 1, 2130: 1})
        result = await self.submit(
            result,
            capacity=123456.0,
            temperature_coefficient=-0.4,
            inverter_channels_0=["1", "10"],
            inverter_channels_2=["3"],
        )
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(
            [
                self.transport.values[a]
                for a in (5000, 5001, 5002, 2100, 2109, 2122, 2110, 2130)
            ],
            [57920, 1, 0xFE70, 1, 1, 1, 1, 1],
        )
        self.assertFalse(any(2130 <= c[1] <= 2139 for c in self.transport.commands))
        self.assertFalse(any(2110 <= c[1] <= 2119 for c in self.transport.commands))

    async def test_numeric_boundary_rejects_fraction_and_precision_without_io(self):
        result = await self.open("solar_configuration")
        for field, value in [
            ("capacity", 1.5),
            ("capacity", float("nan")),
            ("temperature_coefficient", -0.4001),
            ("temperature_coefficient", float("nan")),
        ]:
            with self.subTest(field=field, value=value):
                self.transport.commands.clear()
                result = await self.submit(
                    result,
                    **{"capacity": 0, "temperature_coefficient": 0, field: value},
                )
                self.assertEqual(result["errors"], {field: "invalid_input"})
                self.assertEqual(self.transport.commands, [])
                self.assert_visible_errors(result)

    async def test_solar_partial_retry_uses_retained_targets_and_fresh_current_values(
        self,
    ):
        result = await self.open("solar_configuration")
        self.transport.fail_writes.add(5000)
        self.transport.ignore_writes.add(2120)
        result = await self.submit(
            result,
            capacity=100,
            temperature_coefficient=-0.4,
            inverter_channels_2=["1", "10"],
        )
        self.assertEqual(
            result["errors"],
            {
                "capacity": "settings_write_failed",
                "inverter_channels_2": "settings_verify_failed",
            },
        )
        self.assert_visible_errors(result)
        self.assertEqual(submit_values(result, {})["capacity"], 100)
        self.transport.fail_writes.clear()
        self.transport.ignore_writes.clear()
        self.transport.commands.clear()
        result = await self.submit(result)
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(
            [c[1] for c in self.transport.commands if c[0] != "read"], [5000, 2120]
        )

    async def test_solar_read_failure_retry_only_reads_and_cancel_has_no_io(self):
        self.transport.fail_reads.add(2120)
        result = await self.open("solar_configuration")
        self.assertEqual(result["errors"], {"base": "settings_read_failed"})
        self.assertEqual(list(map(str, result["data_schema"].schema)), ["flow_action"])
        self.transport.fail_reads.clear()
        result = await self.submit(result)
        self.assertFalse(result["errors"])
        self.assertTrue(all(c[0] == "read" for c in self.transport.commands))
        for action in ("back", "cancel"):
            self.transport.commands.clear()
            result = await self.submit(result, capacity=123, flow_action=action)
            self.assertEqual(result["step_id"], "init")
            self.assertEqual(self.transport.commands, [])
            result = await self.submit(result, extra_action="solar_configuration")

    async def test_fresh_firmware_and_cloud_gates_prevent_new_settings_io(self):
        result = await self.open("solar_configuration")
        self.transport.values[3009] = 139
        self.transport.commands.clear()
        result = await self.submit(result, capacity=123)
        self.assertEqual(result["errors"], {"base": "settings_firmware_too_old"})
        self.assertEqual(self.transport.commands, [("read", 3009, 1, 255)])
        self.flow._entry.data["mode"] = "cloud"
        self.transport.commands.clear()
        self.assertTrue(
            callable(getattr(self.flow, "async_step_channel_configuration", None))
        )
        result = await self.flow.async_step_channel_configuration()
        self.assertEqual(result["reason"], "settings_unavailable")
        self.assertEqual(self.transport.commands, [])
