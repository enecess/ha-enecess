"""Exercise independent solar measurements through displayed wizard forms."""

from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from flow_test_support import load_flow, submit_values


class SolarFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)
        self.data = {
            "device_type": "ecomain",
            "mode": "manual",
            "ecomain_serial": "FICTIONAL-SOLAR-FLOW-001",
            "ecomain_host": "192.0.2.120",
            "ecomain_firmware_version": 140,
            "ecomain_selected_slaves": [4],
        }

    def options(self, *, firmware=140, mode="manual", **options):
        entry = SimpleNamespace(
            entry_id="fictional-solar-flow",
            data={**self.data, "mode": mode, "ecomain_firmware_version": firmware},
            options=options,
        )
        flow = self.module.EnecessOptionsFlow(entry)
        flow._available_slaves = ["1", "2", "4"]
        flow._async_refresh_available_slaves = AsyncMock(return_value=None)
        flow._async_remove_stale_sensor_entries = Mock()
        flow._update_entry_data = Mock()
        return flow

    async def submit(self, flow, result, **values):
        return await getattr(flow, "async_step_" + result["step_id"])(
            submit_values(result, values)
        )

    async def test_local_discovery_offers_solar_and_setup_can_save_only_solar(self):
        flow = self.module.ConfigFlow()
        flow.context = {}
        flow._mode = "manual"
        flow._ecomain_local_config = {
            "ecomain_host": "192.0.2.120",
            "ecomain_serial": self.data["ecomain_serial"],
        }
        client = SimpleNamespace(
            read_holding_registers=AsyncMock(
                side_effect=[
                    SimpleNamespace(registers=[140]),
                    SimpleNamespace(registers=[0, 1, 0, 1]),
                ]
            ),
            async_close=AsyncMock(),
        )
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            result = await flow.async_step_ecomain_local_setup()
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(
            fields["ecomain_selected_slaves"].config["options"], ["2", "4"]
        )
        result = await self.submit(flow, result, ecomain_selected_slaves=["4"])
        fields = list(map(str, result["data_schema"].schema))
        self.assertEqual(fields[:2], ["solar_measurement_types", "measurement_types"])
        self.assertEqual(
            submit_values(result, {})["solar_measurement_types"],
            [
                "solar_irradiance",
                "solar_tilt_angle",
                "solar_module_temperature",
                "solar_actual_power",
                "solar_estimated_power",
            ],
        )
        result = await self.submit(
            flow,
            result,
            measurement_types=[],
            solar_measurement_types=["solar_actual_power"],
        )
        self.assertEqual(result["step_id"], "extra_entities")
        self.assertEqual(flow._options_data()["measurement_types"], [])
        self.assertEqual(
            flow._options_data()["solar_measurement_types"], ["solar_actual_power"]
        )
        result = await self.submit(flow, result, extra_action="finish")
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"]["ecomain_selected_slaves"], [4])
        self.assertEqual(result["options"]["measurement_types"], [])
        self.assertEqual(
            result["options"]["solar_measurement_types"], ["solar_actual_power"]
        )

    async def test_options_local_discovery_offers_new_solar_device(self):
        flow = self.options()
        client = SimpleNamespace(
            read_holding_registers=AsyncMock(
                side_effect=[
                    SimpleNamespace(registers=[140]),
                    SimpleNamespace(registers=[0, 1, 0, 1]),
                ]
            ),
            async_close=AsyncMock(),
        )
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            self.assertIsNone(await flow._async_refresh_local_slaves())
        result = await flow._show_options_menu()
        choices = next(
            value.config["options"]
            for key, value in result["data_schema"].schema.items()
            if str(key) == "ecomain_selected_slaves"
        )
        self.assertEqual(choices, ["2", "4"])

    async def test_explicit_empty_solar_is_not_replaced_by_defaults(self):
        flow = self.options(solar_measurement_types=[], measurement_types=["power"])
        result = await flow.async_step_measurement_types()
        self.assertEqual(submit_values(result, {})["solar_measurement_types"], [])
        result = await self.submit(
            flow, result, measurement_types=[], solar_measurement_types=[]
        )
        self.assertEqual(result["errors"], {"base": "no_measurements_selected"})
        result = await self.submit(
            flow, result, solar_measurement_types=["solar_irradiance"]
        )
        self.assertEqual(result["step_id"], "init")
        self.assertEqual(flow._options["measurement_types"], [])

    async def test_explicit_solar_only_child_removal_is_rejected_before_finish(self):
        flow = self.options(
            measurement_types=[], solar_measurement_types=["solar_actual_power"]
        )
        result = await flow.async_step_init()
        result = await self.submit(
            flow, result, ecomain_selected_slaves=[], extra_action="finish"
        )
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["errors"], {"base": "no_measurements_selected"})
        self.assertEqual(flow._options["ecomain_selected_slaves"], [4])

    async def test_offline_and_downgraded_solar_only_unchanged_save_preserves_preferences(
        self,
    ):
        for firmware in (None, 139, 140):
            with self.subTest(firmware=firmware):
                flow = self.options(
                    firmware=firmware,
                    measurement_types=[],
                    solar_measurement_types=["solar_actual_power"],
                    future_option="keep",
                )
                flow._available_slaves = []
                original = deepcopy(flow._options)
                result = await flow.async_step_init()
                self.assertEqual(
                    submit_values(result, {})["ecomain_selected_slaves"], ["4"]
                )
                result = await self.submit(
                    flow, result, extra_action="measurement_types"
                )
                result = await self.submit(flow, result, flow_action="save")
                self.assertEqual(result["step_id"], "init")
                self.assertFalse(result["errors"])
                result = await self.submit(flow, result, extra_action="finish")
                self.assertEqual(result["data"], original)

    async def test_hidden_preferences_survive_device_removal_with_meter_measurements(
        self,
    ):
        flow = self.options(
            measurement_types=["power"], solar_measurement_types=["solar_tilt_angle"]
        )
        result = await flow.async_step_init()
        result = await self.submit(
            flow, result, ecomain_selected_slaves=[], extra_action="measurement_types"
        )
        self.assertNotIn(
            "solar_measurement_types", list(map(str, result["data_schema"].schema))
        )
        result = await self.submit(flow, result, measurement_types=["voltage"])
        result = await self.submit(flow, result, extra_action="finish")
        self.assertEqual(
            result["data"]["solar_measurement_types"], ["solar_tilt_angle"]
        )

    async def test_solar_dependencies_block_measurement_and_child_deselection(self):
        extra = {
            "key": "extra_solar",
            "name": "Fictional output",
            "operation": "absolute",
            "sources": ["solar_actual_power"],
        }
        flow = self.options(
            measurement_types=["power"],
            solar_measurement_types=["solar_actual_power"],
            extra_entities=[extra],
        )
        result = await flow.async_step_init()
        result = await self.submit(
            flow, result, ecomain_selected_slaves=[], extra_action="finish"
        )
        self.assertEqual(result["errors"], {"base": "slave_in_use"})
        result = await self.submit(flow, result, extra_action="measurement_types")
        result = await self.submit(flow, result, solar_measurement_types=[])
        self.assertEqual(result["errors"], {"base": "measurement_in_use"})

    async def test_new_actions_require_local_140_and_selected_solar(self):
        for firmware, mode, selected, expected in [
            (139, "manual", [4], {"channel_phases"}),
            (140, "manual", [4], {"channel_configuration", "solar_configuration"}),
            (140, "manual", [], {"channel_configuration"}),
            (140, "cloud", [1], set()),
        ]:
            with self.subTest(firmware=firmware, mode=mode, selected=selected):
                flow = self.options(
                    firmware=firmware, mode=mode, ecomain_selected_slaves=selected
                )
                result = await flow._show_options_menu()
                actions = next(
                    value.config["options"]
                    for key, value in result["data_schema"].schema.items()
                    if str(key) == "extra_action"
                )
                self.assertEqual(
                    set(actions)
                    & {
                        "channel_phases",
                        "channel_configuration",
                        "solar_configuration",
                    },
                    expected,
                )
                result = await flow.async_step_measurement_types()
                self.assertEqual(
                    "solar_measurement_types"
                    in list(map(str, result["data_schema"].schema)),
                    firmware >= 140 and mode != "cloud" and 4 in selected,
                )
