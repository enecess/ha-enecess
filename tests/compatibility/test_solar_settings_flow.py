"""Validate commissioning schemas, numeric boundaries and navigation with real HA."""

from types import MethodType, SimpleNamespace
import json

from homeassistant.data_entry_flow import FlowResultType, section
from homeassistant.helpers.data_entry_flow import FlowManagerResourceView
from homeassistant.helpers.selector import NumberSelector, SelectSelectorMode

from custom_components.enecess.client_modbus import EnecessModbusClient
from custom_components.enecess.config_flow import ConfigFlow
from tests.test_ecomain_settings import Transport
import test_runtime as runtime_fixture

READ_REGISTERS = EnecessModbusClient.read_holding_registers


class SolarSettingsFlowTests(runtime_fixture.RealHARuntimeFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.entry = self.make_entry("local")
        self.hass.config_entries.async_update_entry(
            self.entry,
            data={**self.entry.data, "ecomain_firmware_version": 140},
            options={
                "ecomain_selected_slaves": [1, 4],
                "measurement_types": [],
                "solar_measurement_types": ["solar_actual_power"],
            },
        )
        self.transport = Transport()
        self.transport.values[3009] = 140
        client = EnecessModbusClient("fictional.invalid", 502)
        client._client = self.transport
        # The shared fixture patches class reads; this transport owns the real boundary.
        client.read_holding_registers = MethodType(READ_REGISTERS, client)
        self.entry.runtime_data = SimpleNamespace(modbus_client=client)
        self.flow = ConfigFlow.async_get_options_flow(self.entry)
        self.flow.hass = self.hass
        self.flow.handler = self.entry.entry_id
        self.flow.context = {}
        self.flow._available_slaves = ["1", "2", "4"]

    def serialize(self, result):
        # Use the same schema conversion as HA's flow HTTP API in each release.
        return FlowManagerResourceView(None)._prepare_result_json(
            {**result, "type": FlowResultType.FORM}
        )["data_schema"]

    async def submit(self, result, **values):
        return await getattr(self.flow, "async_step_" + result["step_id"])(
            result["data_schema"](values)
        )

    async def test_native_channel_sections_serialize_validate_and_keep_back_drafts(
        self,
    ):
        result = await self.flow._show_options_menu()
        result = await self.submit(result, extra_action="channel_configuration")
        result = await self.submit(result, channel_device="0")
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(
            sum(isinstance(value, section) for value in fields.values()), 10
        )
        serialized = self.serialize(result)
        channels = [item for item in serialized if item["name"].startswith("channel_")]
        self.assertEqual(len(channels), 10)
        for item in channels:
            self.assertEqual(item["type"], "expandable")
            self.assertFalse(item["expanded"])
            self.assertTrue(all(not control["required"] for control in item["schema"]))
            self.assertEqual(
                [control["name"] for control in item["schema"]],
                ["phase", "transformer"],
            )
            self.assertEqual(
                item["schema"][0]["selector"]["select"]["mode"],
                SelectSelectorMode.DROPDOWN,
            )
        self.transport.commands.clear()
        result = await self.submit(
            result, channel_1={"phase": "L3", "transformer": "100"}, flow_action="back"
        )
        self.assertEqual(self.transport.commands, [])
        result = await self.submit(result, channel_device="0")
        self.assertEqual(
            result["data_schema"]({})["channel_1"],
            {"phase": "L3", "transformer": "100"},
        )
        result = await self.submit(result, flow_action="back")
        result = await self.submit(result, channel_device="1")
        serialized = self.serialize(result)
        self.assertEqual(
            sum(item.get("type") == "expandable" for item in serialized), 10
        )
        self.assertEqual(
            result["data_schema"]({})["channel_1"], {"phase": "L1", "transformer": "30"}
        )

    async def test_real_numeric_selectors_convert_integral_capacity_and_validate_precision_before_io(
        self,
    ):
        result = await self.flow._show_options_menu()
        result = await self.submit(result, extra_action="solar_configuration")
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertIsInstance(fields["capacity"], NumberSelector)
        self.assertIsInstance(fields["temperature_coefficient"], NumberSelector)
        serialized = self.serialize(result)
        self.assertEqual(
            serialized[0]["selector"]["number"]["unit_of_measurement"], "W"
        )
        self.assertEqual(
            serialized[1]["selector"]["number"]["unit_of_measurement"], "%/°C"
        )
        self.assertIsInstance(
            result["data_schema"]({"capacity": 123})["capacity"], float
        )
        for field, value in [
            ("capacity", 0.5),
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
                json.dumps(
                    self.serialize(result),
                    allow_nan=False,
                )
        result = await self.submit(
            result,
            capacity=4294967295,
            temperature_coefficient=-32.768,
            inverter_channels_0=["1"],
            inverter_channels_2=["10"],
        )
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(
            [
                self.transport.values[address]
                for address in (5000, 5001, 5002, 2200, 2229)
            ],
            [65535, 65535, 32768, 1, 1],
        )
        self.assertFalse(any(2100 <= c[1] <= 2139 for c in self.transport.commands))
        self.assertEqual(
            [c for c in self.transport.commands if 2200 <= c[1] <= 2239],
            [
                ("read", 2200, 10, 255),
                ("read", 2220, 10, 255),
                ("read", 2210, 10, 255),
                ("write", 2200, 1, 255),
                ("read", 2200, 1, 255),
                ("write", 2229, 1, 255),
                ("read", 2229, 1, 255),
            ],
        )

    async def test_unsigned_capacity_round_trips_through_native_form_and_readback(self):
        for capacity, words in [
            (2147483648, [0, 0x8000]),
            (4294967295, [0xFFFF, 0xFFFF]),
            (0, [0, 0]),
        ]:
            with self.subTest(capacity=capacity):
                result = await self.flow._show_options_menu()
                result = await self.submit(result, extra_action="solar_configuration")
                result = await self.flow.async_step_solar_configuration(
                    {"capacity": capacity, "temperature_coefficient": 0}
                )
                self.assertEqual(result["step_id"], "init")
                self.assertEqual(
                    [self.transport.values[5000], self.transport.values[5001]], words
                )
                result = await self.submit(result, extra_action="solar_configuration")
                self.assertEqual(result["data_schema"]({})["capacity"], capacity)
                result = await self.submit(result, flow_action="cancel")

    async def test_invalid_capacity_is_rejected_before_io_by_native_form(self):
        result = await self.flow._show_options_menu()
        result = await self.submit(result, extra_action="solar_configuration")
        for capacity in [-1, 0.5, True, 4294967296]:
            with self.subTest(capacity=capacity):
                self.transport.commands.clear()
                result = await self.flow.async_step_solar_configuration(
                    {"capacity": capacity, "temperature_coefficient": 0}
                )
                self.assertEqual(result["errors"], {"capacity": "invalid_input"})
                self.assertEqual(self.transport.commands, [])

    async def test_native_section_error_addresses_visible_parent_and_save_requires_unknown_choice(
        self,
    ):
        self.transport.values[2043] = 0
        result = await self.flow._show_options_menu()
        result = await self.submit(result, extra_action="channel_configuration")
        result = await self.submit(result, channel_device="0")
        self.transport.commands.clear()
        result = await self.submit(result)
        self.assertEqual(result["errors"], {"channel_1": "invalid_input"})
        self.assertEqual(self.transport.commands, [])
        self.transport.ignore_writes.add(2043)
        result = await self.submit(
            result, channel_1={"phase": "L1", "transformer": "100"}
        )
        self.assertEqual(
            result["errors"], {"channel_1": "settings_transformer_verify_failed"}
        )
        serialized = self.serialize(result)
        self.assertTrue(set(result["errors"]) <= {item["name"] for item in serialized})
        self.transport.commands.clear()
        result = await self.submit(result, flow_action="cancel")
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(self.transport.commands, [])

    async def test_incomplete_nested_choices_can_back_and_cancel_without_io(self):
        self.transport.values.update({2000: 3, 2043: 0})
        result = await self.flow._show_options_menu()
        result = await self.submit(result, extra_action="channel_configuration")
        result = await self.submit(result, channel_device="0")
        for action in ("back", "cancel"):
            self.assertEqual(result["data_schema"]({})["channel_1"], {})
            self.transport.commands.clear()
            result = await self.submit(result, channel_1={}, flow_action=action)
            self.assertEqual(self.transport.commands, [])
            if action == "cancel":
                self.assertEqual(result["step_id"], "init")
            else:
                self.assertEqual(result["step_id"], "channel_device")
                result = await self.submit(result, channel_device="0")
