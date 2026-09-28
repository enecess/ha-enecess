"""Follow complete options journeys through their displayed form schemas."""

import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from flow_test_support import load_flow, submit_values


class OptionsJourneyTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    def options_flow(self, *, selected=(1,), mode="manual"):
        entry = types.SimpleNamespace(
            data={"device_type": "ecomain", "mode": mode,
                  "ecomain_serial": "TEST-OPTIONS-JOURNEY", "ecomain_firmware_version": 139},
            options={"ecomain_selected_slaves": list(selected),
                     "measurement_types": ["power", "energy_forward"]}, entry_id="offline-options")
        flow = self.module.EnecessOptionsFlow(entry)
        flow._available_slaves = ["1", "2"]
        flow._async_refresh_available_slaves = AsyncMock(return_value=None)
        flow._async_remove_stale_sensor_entries = Mock()
        flow._update_entry_data = Mock()
        return flow

    async def submit(self, flow, result, **values):
        return await getattr(flow, "async_step_" + result["step_id"])(submit_values(result, values))

    async def test_ecoplug_options_save_and_cancel_from_actual_init(self):
        devices = [{"hardware_number": "TEST-PLUG-A", "name": "Plug A"},
                   {"hardware_number": "TEST-PLUG-B", "name": "Plug B"}]
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                entry = types.SimpleNamespace(data={"device_type": "ecoplug",
                    "username": "test@example.invalid", "password": "fake-password",
                    "ecoplug_devices": devices[:1]}, options={}, entry_id="offline-plug")
                flow = self.module.EnecessOptionsFlow(entry)
                update = Mock()
                flow.hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(async_update_entry=update))
                api = types.SimpleNamespace(generate_token=AsyncMock(return_value="fake-new-token"),
                                            get_hardware_list=AsyncMock(return_value=devices))
                with patch.object(self.module, "EnecessApi", return_value=api), patch.object(
                    self.module, "async_remove_unconfigured_registry_entries"
                ) as cleanup:
                    result = await flow.async_step_init()
                    self.assertEqual("ecoplug_select", result["step_id"])
                    self.assertEqual(["TEST-PLUG-A"], result["data_schema"]({})["ecoplug_selected"])
                    api.generate_token.assert_awaited_once_with("test@example.invalid", "fake-password")
                    api.get_hardware_list.assert_awaited_once_with("fake-new-token", hardware_type=2)
                    result = await self.submit(flow, result, ecoplug_selected=["TEST-PLUG-B"],
                                               flow_action="cancel" if cancel else "save")
                    if cancel:
                        self.assertEqual("abort", result["type"])
                        self.assertEqual("user_cancelled", result["reason"])
                        cleanup.assert_not_called()
                        update.assert_not_called()
                        self.assertEqual(devices[:1], entry.data["ecoplug_devices"])
                    else:
                        self.assertEqual("create_entry", result["type"])
                        self.assertEqual({}, result["data"])
                        update.assert_called_once()
                        cleanup.assert_called_once()
                        persisted = update.call_args.kwargs["data"]
                        self.assertEqual(devices[1:], persisted["ecoplug_devices"])
                        self.assertEqual("fake-new-token", persisted[self.module.CONST_CLOUD_TOKEN])
                        self.assertEqual(persisted, cleanup.call_args.kwargs["data"])

    async def test_phase_read_failure_retry_save_and_cancel_journey(self):
        from test_ecomain_phase import Transport

        transport = Transport()
        transport.values[3009] = 139
        transport.fail_reads.add(2000)
        client = self.module.EnecessModbusClient("example.invalid", 502)
        client._client = transport
        flow = self.options_flow()
        flow.hass = types.SimpleNamespace(data={"enecess": {"offline-options": {"modbus_client": client}}})
        result = await flow.async_step_init()
        result = await self.submit(flow, result, extra_action="channel_phases")
        result = await self.submit(flow, result, phase_device="0")
        self.assertEqual("phase_read_failed", result["errors"]["base"])
        commands = list(transport.commands)
        result = await self.submit(flow, result, flow_action="cancel")
        self.assertEqual("init", result["step_id"])
        self.assertEqual(commands, transport.commands)

        result = await self.submit(flow, result, extra_action="channel_phases")
        result = await self.submit(flow, result, phase_device="0")
        self.assertEqual("phase_read_failed", result["errors"]["base"])
        transport.fail_reads.clear()
        result = await self.submit(flow, result)
        self.assertEqual("channel_phases", result["step_id"])
        self.assertEqual({}, result["errors"])
        self.assertEqual("L1", result["data_schema"]({})["channel_10"])
        self.assertFalse(any(command[0] == "write" for command in transport.commands))

        result = await self.submit(flow, result, channel_10="L3", flow_action="save")
        self.assertEqual("init", result["step_id"])
        self.assertEqual(2, transport.values[2009])
        writes = [command for command in transport.commands if command[0] == "write"]
        self.assertEqual([("write", 2009, 2, 255)], writes)
        commands = list(transport.commands)
        result = await self.submit(flow, result, flow_action="cancel")
        self.assertEqual("abort", result["type"])
        self.assertEqual("user_cancelled", result["reason"])
        self.assertEqual(commands, transport.commands)
        self.assertEqual(2, transport.values[2009])
        flow._async_remove_stale_sensor_entries.assert_not_called()
        flow._update_entry_data.assert_not_called()

    async def test_phase_switch_read_failure_retries_and_writes_only_selected_slave(self):
        from test_ecomain_phase import Transport

        transport = Transport()
        transport.values[3009] = 139
        transport.fail_reads.add(2010)
        client = self.module.EnecessModbusClient("example.invalid", 502)
        client._client = transport
        flow = self.options_flow()
        flow.hass = types.SimpleNamespace(data={"enecess": {"offline-options": {"modbus_client": client}}})
        result = await flow.async_step_init()
        result = await self.submit(flow, result, extra_action="channel_phases")
        result = await self.submit(flow, result, phase_device="0")
        self.assertEqual({}, result["errors"])
        commands = list(transport.commands)
        result = await self.submit(flow, result, flow_action="back", channel_1="L2")
        self.assertEqual(commands, transport.commands)
        result = await self.submit(flow, result, phase_device="1")
        self.assertEqual("channel_phases", result["step_id"])
        self.assertEqual("phase_read_failed", result["errors"]["base"])
        self.assertEqual(1, flow._phase_device)
        transport.fail_reads.clear()
        result = await self.submit(flow, result)
        self.assertEqual({}, result["errors"])
        self.assertEqual("L1", result["data_schema"]({})["channel_1"])
        self.assertEqual(1, flow._phase_device)
        result = await self.submit(flow, result, channel_1="L3", flow_action="save")
        self.assertEqual("init", result["step_id"])
        writes = [command for command in transport.commands if command[0] == "write"]
        self.assertEqual([("write", 2010, 2, 255)], writes)
        self.assertEqual(0, transport.values[2000])
        self.assertEqual(2, transport.values[2010])

    async def test_options_reject_removing_slave_used_by_each_extra_entity(self):
        for mode in ("manual", "cloud"):
            for operation in ("add_formula", "add_transform", "add_aggregate"):
                with self.subTest(mode=mode, operation=operation):
                    flow = self.options_flow(mode=mode)
                    source = "sub1_ch1_power_avg_1m" if mode == "cloud" else "sub1_ch1_power_rt"
                    source2 = "sub1_ch2_power_avg_1m" if mode == "cloud" else "sub1_ch2_power_rt"
                    result = await flow.async_step_init()
                    result = await self.submit(flow, result, extra_action=operation)
                    if operation == "add_formula":
                        result = await self.submit(flow, result, extra_entity_name="Sub formula",
                            extra_formula_result_type="power", extra_entity_sources=[source])
                        result = await self.submit(flow, result, extra_formula_expression="a")
                    elif operation == "add_transform":
                        result = await self.submit(flow, result, extra_entity_name="Sub absolute",
                            extra_entity_operation="absolute", extra_entity_source=source)
                    else:
                        result = await self.submit(flow, result, extra_entity_source_kind="power")
                        result = await self.submit(flow, result, extra_entity_name="Sub sum",
                            extra_entity_operation="sum", extra_entity_sources=[source, source2])
                    result = await self.submit(flow, result, extra_action="finish", ecomain_selected_slaves=[])
                    self.assertEqual("form", result["type"])
                    self.assertEqual("slave_in_use", result["errors"]["base"])
                    self.assertEqual([1], flow._options["ecomain_selected_slaves"])
                    flow._async_remove_stale_sensor_entries.assert_not_called()
                    flow._update_entry_data.assert_not_called()
                    result = await self.submit(flow, result, extra_action="remove", ecomain_selected_slaves=["1"])
                    result = await self.submit(flow, result, extra_entity_remove=flow._extra_entities[0]["key"])
                    result = await self.submit(flow, result, extra_action="finish", ecomain_selected_slaves=[])
                    self.assertEqual("create_entry", result["type"])
                    self.assertEqual([], result["data"]["ecomain_selected_slaves"])

    async def test_unrelated_options_save_keeps_offline_selected_slaves(self):
        for available in (["1"], []):
            with self.subTest(available=available):
                flow = self.options_flow(selected=(1, 2))
                flow._available_slaves = available
                result = await flow.async_step_init()
                result = await self.submit(flow, result, extra_action="measurement_types")
                result = await self.submit(flow, result, measurement_types=["power"])
                result = await self.submit(flow, result, extra_action="finish")
                self.assertEqual([1, 2], result["data"]["ecomain_selected_slaves"])

    async def test_offline_slave_can_be_explicitly_removed(self):
        flow = self.options_flow(selected=(1, 2))
        flow._available_slaves = ["1"]
        result = await flow.async_step_init()
        result = await self.submit(flow, result, extra_action="finish", ecomain_selected_slaves=["1"])
        self.assertEqual([1], result["data"]["ecomain_selected_slaves"])

    async def test_new_firmware_measurement_source_also_prevents_slave_removal(self):
        flow = self.options_flow()
        flow._entry.data["ecomain_firmware_version"] = 138
        result = await flow.async_step_init()
        result = await self.submit(flow, result, extra_action="measurement_types")
        result = await self.submit(flow, result, measurement_types=["power", "voltage"])
        result = await self.submit(flow, result, extra_action="add_formula")
        result = await self.submit(flow, result, extra_entity_name="Sub voltage",
            extra_formula_result_type="voltage", extra_entity_sources=["sub1_ch1_voltage_rt"])
        result = await self.submit(flow, result, extra_formula_expression="a")
        self.assertEqual("init", result["step_id"])
        result = await self.submit(flow, result, extra_action="finish", ecomain_selected_slaves=[])
        self.assertEqual("form", result["type"])
        self.assertEqual("slave_in_use", result["errors"]["base"])
        flow._async_remove_stale_sensor_entries.assert_not_called()

    async def test_cloud_refresh_keeps_mapping_for_selected_missing_slave(self):
        flow = self.options_flow(selected=(1, 2), mode="cloud")
        flow._entry.data.update(username="test@example.invalid", password="fake-password",
            ecomain_cloud_slave_map={1: "TEST-OPTIONS-JOURNEY_1", 2: "TEST-OPTIONS-JOURNEY_2"})
        flow._cloud_slave_map = dict(flow._entry.data["ecomain_cloud_slave_map"])
        update = Mock()
        flow.hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(async_update_entry=update))
        del flow._async_refresh_available_slaves
        del flow._update_entry_data
        api = types.SimpleNamespace(generate_token=AsyncMock(return_value="fake-new-token"),
            get_hardware_list=AsyncMock(side_effect=[
                [{"id": 17, "hardware_number": "TEST-OPTIONS-JOURNEY"}],
                [{"hardware_number": "TEST-OPTIONS-JOURNEY_1"}]]))
        with patch.object(self.module, "EnecessApi", return_value=api):
            result = await flow.async_step_init()
        self.assertEqual(["1"], flow._available_slaves)
        result = await self.submit(flow, result, extra_action="finish")
        self.assertEqual([1, 2], result["data"]["ecomain_selected_slaves"])
        self.assertEqual({1: "TEST-OPTIONS-JOURNEY_1", 2: "TEST-OPTIONS-JOURNEY_2"},
                         update.call_args.kwargs["data"]["ecomain_cloud_slave_map"])

    async def test_aggregate_final_kind_is_locked_and_back_can_reselect(self):
        for options in (False, True):
            with self.subTest(options=options):
                if options:
                    flow = self.options_flow()
                    result = await flow.async_step_init()
                else:
                    flow = self.module.ConfigFlow()
                    flow._entry_data = {"device_type": "ecomain", "mode": "manual",
                        "ecomain_serial": "TEST-AGGREGATE", "ecomain_firmware_version": 139}
                    result = await flow.async_step_measurement_types()
                    result = await self.submit(flow, result, measurement_types=["power", "energy_forward"])
                result = await self.submit(flow, result, extra_action="add_aggregate")
                result = await self.submit(flow, result, extra_entity_source_kind="power")
                fields = {str(key): value for key, value in result["data_schema"].schema.items()}
                self.assertEqual(["power"], fields["extra_entity_source_kind"].config["options"])
                result = await self.submit(flow, result, flow_action="back")
                result = await self.submit(flow, result, extra_entity_source_kind="energy")
                fields = {str(key): value for key, value in result["data_schema"].schema.items()}
                self.assertEqual(["energy"], fields["extra_entity_source_kind"].config["options"])
                choices = fields["extra_entity_sources"].config["options"]
                sources = [choice["value"] for choice in choices[:2]]
                self.assertTrue(all("energy" in source for source in sources))
                result = await self.submit(flow, result, extra_entity_name="Energy sum",
                    extra_entity_operation="sum", extra_entity_sources=sources)
                self.assertEqual("init" if options else "extra_entities", result["step_id"])
                self.assertEqual("energy", flow._extra_entities[0]["source_kind"])
                self.assertEqual(sources, flow._extra_entities[0]["sources"])
