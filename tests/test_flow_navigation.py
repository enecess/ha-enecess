"""Exercise navigation through real flow handlers with offline HA boundaries."""

from copy import deepcopy
import types
import unittest
from unittest.mock import AsyncMock

from flow_test_support import load_flow, submit_values


class FlowNavigationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)
        self.data = {"device_type": "ecomain", "mode": "manual", "ecomain_serial": "TEST-NAV-01",
                     "ecomain_firmware_version": 139}
        self.formula = {"extra_entity_name": "Difference", "extra_formula_result_type": "power",
                        "extra_entity_sources": ["main_l1_power_rt", "main_l2_power_rt"]}

    def flow(self, options=False):
        if options:
            return self.module.EnecessOptionsFlow(types.SimpleNamespace(data=dict(self.data), options={}, entry_id="test"))
        flow = self.module.ConfigFlow()
        flow._entry_data = dict(self.data)
        flow.context = {}
        return flow

    def navigation_input(self, result, action, **values):
        return submit_values(result, {**values, "flow_action": action})

    async def menu(self, flow, options=False):
        return await flow._show_options_menu() if options else await flow.async_step_extra_entities()

    async def choose(self, flow, action, options=False):
        handler = flow.async_step_init if options else flow.async_step_extra_entities
        return await handler({"extra_action": action})

    async def test_menus_have_one_action_selector_with_navigation(self):
        for options in (False, True):
            with self.subTest(options=options):
                flow = self.flow(options)
                if not options:
                    await flow.async_step_measurement_types()
                result = await self.menu(flow, options)
                fields = {str(key): value for key, value in result["data_schema"].schema.items()}
                self.assertNotIn("flow_action", fields)
                actions = fields["extra_action"].config["options"]
                self.assertIn("finish", actions)
                self.assertIn("add_formula", actions)
                self.assertIn("cancel", actions)
                self.assertEqual(not options, "back" in actions)
                self.assertNotIn("continue", actions)

    async def test_menu_cancel_does_not_finish_or_save_options(self):
        for options in (False, True):
            with self.subTest(options=options):
                flow = self.flow(options)
                result = await self.menu(flow, options)
                handler = flow.async_step_init if options else flow.async_step_extra_entities
                result = await handler(result["data_schema"]({"extra_action": "cancel"}))
                self.assertEqual({"type": "abort", "reason": "user_cancelled"}, result)
                if options:
                    self.assertEqual({}, flow._entry.options)

    async def test_menu_back_preserves_saved_extra_entities(self):
        flow = self.flow()
        await flow.async_step_measurement_types()
        result = await flow.async_step_measurement_types({"measurement_types": ["power"]})
        await self.choose(flow, "add_formula")
        await flow.async_step_extra_formula(self.formula)
        result = await flow.async_step_extra_formula_expression({"extra_formula_expression": "a-b"})
        original = deepcopy(flow._extra_entities)
        result = await flow.async_step_extra_entities(result["data_schema"]({"extra_action": "back"}))
        self.assertEqual("measurement_types", result["step_id"])
        self.assertEqual(original, flow._extra_entities)

    async def test_formula_selectors_offer_dropdown_and_multiple_sources(self):
        for options in (False, True):
            flow = self.flow(options)
            result = await flow.async_step_extra_formula()
            fields = {str(key): value for key, value in result["data_schema"].schema.items()}
            self.assertEqual("dropdown", fields["extra_formula_result_type"].config["mode"])
            self.assertEqual("dropdown", fields["extra_entity_sources"].config["mode"])
            self.assertTrue(fields["extra_entity_sources"].config["multiple"])

    async def test_back_from_expression_keeps_formula_and_unsaved_expression(self):
        for options in (False, True):
            with self.subTest(options=options):
                flow = self.flow(options)
                await self.menu(flow, options)
                await self.choose(flow, "add_formula", options)
                result = await flow.async_step_extra_formula(self.formula)
                result = await flow.async_step_extra_formula_expression(self.navigation_input(
                    result, "back", extra_formula_expression="a +"))
                self.assertEqual("extra_formula", result["step_id"])
                values = result["data_schema"]({})
                self.assertEqual("Difference", values["extra_entity_name"])
                self.assertEqual(self.formula["extra_entity_sources"], values["extra_entity_sources"])
                result = await flow.async_step_extra_formula(values)
                self.assertEqual("a +", result["data_schema"]({})["extra_formula_expression"])
                self.assertEqual([], flow._extra_entities)
                result = await flow.async_step_extra_formula_expression(self.navigation_input(result, "cancel"))
                self.assertEqual("init" if options else "extra_entities", result["step_id"])
                result = await self.choose(flow, "add_formula", options)
                self.assertEqual("", result["data_schema"]({})["extra_entity_name"])

    async def test_cancel_edit_preserves_original_and_other_saved_entities(self):
        for options in (False, True):
            flow = self.flow(options)
            await self.menu(flow, options)
            await self.choose(flow, "add_formula", options)
            await flow.async_step_extra_formula(self.formula)
            await flow.async_step_extra_formula_expression({"extra_formula_expression": "a-b"})
            original = deepcopy(flow._extra_entities)
            await self.choose(flow, "edit_formula", options)
            await flow.async_step_extra_formula_edit({"extra_formula_entity": original[0]["key"]})
            result = await flow.async_step_extra_formula({**self.formula, "extra_entity_name": "Changed"})
            result = await flow.async_step_extra_formula_expression(self.navigation_input(result, "cancel"))
            self.assertEqual("init" if options else "extra_entities", result["step_id"])
            self.assertEqual(original, flow._extra_entities)

    async def test_back_from_menu_keeps_saved_extras_and_protects_their_sources(self):
        flow = self.flow()
        await flow.async_step_measurement_types()
        await flow.async_step_measurement_types({"measurement_types": ["power", "energy_forward"]})
        await self.choose(flow, "add_formula")
        await flow.async_step_extra_formula(self.formula)
        result = await flow.async_step_extra_formula_expression({"extra_formula_expression": "a-b"})
        original = deepcopy(flow._extra_entities)
        result = await flow.async_step_extra_entities(self.navigation_input(result, "back"))
        self.assertEqual("measurement_types", result["step_id"])
        self.assertEqual(original, flow._extra_entities)
        result = await flow.async_step_measurement_types({"measurement_types": ["energy_forward"]})
        self.assertEqual("measurement_in_use", result["errors"]["base"])
        result = await flow.async_step_measurement_types({"measurement_types": ["power", "energy_forward"]})
        self.assertEqual("extra_entities", result["step_id"])
        self.assertEqual(original, flow._extra_entities)

    async def test_back_then_reorder_sources_keeps_variable_meaning(self):
        for options in (False, True):
            flow = self.flow(options)
            await self.menu(flow, options)
            await self.choose(flow, "add_formula", options)
            result = await flow.async_step_extra_formula(self.formula)
            original = result["description_placeholders"]["variables"]
            await flow.async_step_extra_formula_expression(self.navigation_input(result, "back", extra_formula_expression="a-b"))
            result = await flow.async_step_extra_formula({**self.formula,
                "extra_entity_sources": list(reversed(self.formula["extra_entity_sources"]))})
            self.assertEqual(original, result["description_placeholders"]["variables"])

    async def test_ecoplug_options_can_render_and_cancel_without_changes(self):
        devices = [{"hardware_number": "TEST-PLUG-01", "name": "Test plug"}]
        entry = types.SimpleNamespace(data={"device_type": "ecoplug", "ecoplug_devices": devices}, options={}, entry_id="test")
        flow = self.module.EnecessOptionsFlow(entry)
        flow._ecoplug_devices = devices
        result = flow._show_ecoplug_select_form()
        result = await flow.async_step_ecoplug_select(self.navigation_input(result, "cancel", ecoplug_selected=[]))
        self.assertEqual("abort", result["type"])
        self.assertEqual(devices, entry.data["ecoplug_devices"])

    async def test_empty_extra_forms_allow_back_and_cancel_without_saving(self):
        for options in (False, True):
            for action, step in (("add_transform", "extra_transform"), ("add_aggregate", "extra_aggregate_kind"),
                                 ("add_formula", "extra_formula"), ("edit_formula", "extra_formula_edit"),
                                 ("remove", "extra_remove")):
                for navigation in ("back", "cancel"):
                    with self.subTest(options=options, step=step, navigation=navigation):
                        flow = self.flow(options)
                        await self.menu(flow, options)
                        if action in ("edit_formula", "remove"):
                            await self.choose(flow, "add_formula", options)
                            await flow.async_step_extra_formula(self.formula)
                            await flow.async_step_extra_formula_expression({"extra_formula_expression": "a-b"})
                        original = deepcopy(flow._extra_entities)
                        result = await self.choose(flow, action, options)
                        self.assertEqual(step, result["step_id"])
                        result = await getattr(flow, "async_step_" + step)(self.navigation_input(result, navigation))
                        self.assertEqual("init" if options else "extra_entities", result["step_id"])
                        self.assertEqual(original, flow._extra_entities)

    async def test_aggregate_back_preserves_draft_and_cancel_does_not_add(self):
        for options in (False, True):
            flow = self.flow(options)
            await self.menu(flow, options)
            await self.choose(flow, "add_aggregate", options)
            result = await flow.async_step_extra_aggregate_kind({"extra_entity_source_kind": "power"})
            values = self.navigation_input(result, "back", extra_entity_name="Sum",
                                           extra_entity_operation="sum", extra_entity_sources=self.formula["extra_entity_sources"])
            result = await flow.async_step_extra_aggregate(values)
            self.assertEqual("extra_aggregate_kind", result["step_id"])
            result = await flow.async_step_extra_aggregate_kind(result["data_schema"]({}))
            self.assertEqual("Sum", result["data_schema"]({})["extra_entity_name"])
            result = await flow.async_step_extra_aggregate(self.navigation_input(result, "cancel"))
            self.assertEqual("init" if options else "extra_entities", result["step_id"])
            self.assertEqual([], flow._extra_entities)

    async def test_measurement_cancel_keeps_saved_selection(self):
        flow = self.flow(True)
        original = deepcopy(flow._options)
        await self.menu(flow, True)
        result = await self.choose(flow, "measurement_types", True)
        result = await flow.async_step_measurement_types(self.navigation_input(result, "cancel", measurement_types=[]))
        self.assertEqual("init", result["step_id"])
        self.assertEqual(original, flow._options)

    async def test_manual_back_restores_inputs_and_cancel_aborts(self):
        flow = self.flow()
        await flow.async_step_user()
        await flow.async_step_user({"device_type": "ecomain"})
        await flow.async_step_ecomain_mode({"mode": "manual"})
        result = await flow.async_step_ecomain_manual({"ecomain_host": "example.invalid", "ecomain_serial": "TEST-NEW-01"})
        result = await flow.async_step_ecomain_local_confirm(self.navigation_input(result, "back"))
        self.assertEqual("ecomain_manual", result["step_id"])
        self.assertEqual("example.invalid", result["data_schema"]({})["ecomain_host"])
        result = await flow.async_step_ecomain_manual(self.navigation_input(result, "cancel"))
        self.assertEqual({"type": "abort", "reason": "user_cancelled"}, result)

    async def test_discovered_entry_confirmation_has_no_navigation_actions(self):
        flow = self.module.ConfigFlow()
        flow.context = {"source": "zeroconf"}
        discovery = self.module.DEVICE_CONFIGS["ecomain"].discovery
        result = await flow.async_step_zeroconf(types.SimpleNamespace(
            type=discovery.mdns_type,
            name=f"{discovery.mdns_prefix}TEST-DISCOVERED-01.{discovery.mdns_type}",
            hostname="test-device.local.", host="192.0.2.10"))
        self.assertEqual("ecomain_local_confirm", result["step_id"])
        self.assertEqual({}, result["data_schema"].schema)
        self.assertFalse(flow.context.get("confirm_only", False))

        flow._ecomain_local_config.update(ecomain_online_slaves=[], ecomain_firmware_version=139)
        result = await flow.async_step_ecomain_local_confirm(result["data_schema"]({}))
        self.assertEqual("ecomain_local_setup", result["step_id"])
        self.assertFalse(flow.context.get("confirm_only", False))
        actions = next(value.config["options"] for key, value in result["data_schema"].schema.items()
                       if str(key) == "flow_action")
        self.assertIn("back", actions)
        result = await flow.async_step_ecomain_local_setup(self.navigation_input(result, "back"))
        self.assertEqual("ecomain_local_confirm", result["step_id"])
        self.assertEqual({}, result["data_schema"].schema)
        self.assertFalse(flow.context.get("confirm_only", False))

    async def test_user_started_local_confirmation_keeps_back_action(self):
        for mode in ("manual", "auto"):
            with self.subTest(mode=mode):
                flow = self.flow()
                flow._async_mdns_scan = AsyncMock(return_value=[self.module.DiscoveredDevice(
                    serial="TEST-SCAN-01", hostname="test-device.local", service_name="test-service", ip="192.0.2.10")])
                await flow.async_step_user()
                await flow.async_step_user({"device_type": "ecomain"})
                await flow.async_step_ecomain_mode({"mode": mode})
                if mode == "manual":
                    result = await flow.async_step_ecomain_manual({"ecomain_host": "192.0.2.10", "ecomain_serial": "TEST-SCAN-01"})
                else:
                    result = await flow.async_step_ecomain_auto_scan({"ecomain_serial": "TEST-SCAN-01"})
                self.assertEqual("ecomain_local_confirm", result["step_id"])
                actions = next(value.config["options"] for key, value in result["data_schema"].schema.items()
                               if str(key) == "flow_action")
                self.assertIn("back", actions)
                result = await flow.async_step_ecomain_local_confirm(self.navigation_input(result, "back"))
                self.assertEqual("ecomain_manual" if mode == "manual" else "ecomain_auto_scan", result["step_id"])

    async def test_all_initial_intermediate_forms_offer_navigation(self):
        steps = ("ecomain_mode", "ecomain_auto_scan", "ecomain_manual", "ecomain_local_confirm",
                 "ecomain_local_setup", "ecomain_cloud_login", "ecoplug_cloud_login", "ecoplug_select",
                 "ecomain_cloud_master", "ecomain_cloud_confirm", "measurement_types")
        for step in steps:
            with self.subTest(step=step):
                flow = self.flow()
                flow._async_mdns_scan = AsyncMock(return_value=[])
                flow._ecomain_local_config = {"ecomain_serial": "TEST-NAV-01", "ecomain_host": "example.invalid",
                                               "ecomain_online_slaves": ["1"], "ecomain_firmware_version": 139}
                flow._cloud_token = "fake-token"
                flow._cloud_username = "test@example.invalid"
                flow._cloud_password = "fake-password"
                flow._cloud_api = types.SimpleNamespace()
                flow._ecomain_cloud_config = {"ecomain_cloud_slaves": [], "ecomain_masters": []}
                result = await getattr(flow, "async_step_" + step)()
                result = await getattr(flow, "async_step_" + step)(self.navigation_input(result, "cancel"))
                self.assertEqual({"type": "abort", "reason": "user_cancelled"}, result)
                self.assertEqual({}, flow._entry_data)
                self.assertIsNone(flow._cloud_token)

    async def test_navigation_forms_are_not_marked_confirmation_only(self):
        flow = self.flow()
        await flow.async_step_ecomain_local_confirm()
        self.assertFalse(flow.context.get("confirm_only", False))

    async def test_options_root_cancel_exits_without_saving(self):
        flow = self.flow(True)
        result = await self.menu(flow, True)
        result = await flow.async_step_init(self.navigation_input(result, "cancel"))
        self.assertEqual("abort", result["type"])
        self.assertEqual("user_cancelled", result["reason"])
        self.assertEqual({}, flow._entry.options)

    async def test_empty_login_forms_allow_back_without_authentication(self):
        for device, step, previous in (("ecomain", "ecomain_cloud_login", "ecomain_mode"),
                                       ("ecoplug", "ecoplug_cloud_login", "user")):
            flow = self.flow()
            await flow.async_step_user()
            result = await flow.async_step_user({"device_type": device})
            if device == "ecomain":
                result = await flow.async_step_ecomain_mode({"mode": "cloud"})
            result = await getattr(flow, "async_step_" + step)(self.navigation_input(result, "back"))
            self.assertEqual(previous, result["step_id"])
            self.assertIsNone(flow._cloud_token)

    async def test_continue_still_requires_manual_fields(self):
        flow = self.flow()
        result = await flow.async_step_ecomain_manual()
        result = await flow.async_step_ecomain_manual(self.navigation_input(result, "continue"))
        self.assertEqual("ecomain_manual", result["step_id"])
        self.assertTrue(result["errors"])

    async def test_phase_navigation_never_reads_or_writes_and_preserves_draft(self):
        from test_ecomain_phase import Transport
        transport = Transport()
        transport.values[3009] = 139
        client = self.module.EnecessModbusClient("example.invalid", 502)
        client._client = transport
        flow = self.flow(True)
        flow._entry.runtime_data = types.SimpleNamespace(modbus_client=client)
        await self.menu(flow, True)
        await self.choose(flow, "channel_phases", True)
        result = await flow.async_step_phase_device({"phase_device": "0"})
        previous_commands = list(transport.commands)
        result = await flow.async_step_channel_phases(self.navigation_input(result, "back", channel_1="L2"))
        self.assertEqual("phase_device", result["step_id"])
        self.assertEqual(previous_commands, transport.commands)
        result = await flow.async_step_phase_device(result["data_schema"]({}))
        self.assertEqual("L2", result["data_schema"]({})["channel_1"])
        previous_commands = list(transport.commands)
        result = await flow.async_step_channel_phases(self.navigation_input(result, "cancel"))
        self.assertEqual("init", result["step_id"])
        self.assertEqual(previous_commands, transport.commands)
        self.assertFalse(any(command[0] == "write" for command in transport.commands))

    async def test_changing_phase_device_does_not_reuse_another_devices_draft(self):
        from test_ecomain_phase import Transport
        transport = Transport()
        transport.values[3009] = 139
        client = self.module.EnecessModbusClient("example.invalid", 502)
        client._client = transport
        flow = self.flow(True)
        flow._options["ecomain_selected_slaves"] = [1]
        flow._available_slaves = ["1"]
        flow._entry.runtime_data = types.SimpleNamespace(modbus_client=client)
        await flow.async_step_phase_device()
        result = await flow.async_step_phase_device({"phase_device": "0"})
        await flow.async_step_channel_phases(self.navigation_input(result, "back", channel_1="L2"))
        result = await flow.async_step_phase_device({"phase_device": "1"})
        self.assertEqual("L1", result["data_schema"]({})["channel_1"])
        self.assertFalse(any(command[0] == "write" for command in transport.commands))

    async def test_changing_phase_device_while_going_back_discards_old_phase_draft(self):
        from test_ecomain_phase import Transport
        transport = Transport()
        transport.values[3009] = 139
        client = self.module.EnecessModbusClient("example.invalid", 502)
        client._client = transport
        flow = self.flow(True)
        flow._options["ecomain_selected_slaves"] = [1]
        flow._available_slaves = ["1"]
        flow._entry.runtime_data = types.SimpleNamespace(modbus_client=client)
        await self.menu(flow, True)
        await self.choose(flow, "channel_phases", True)
        result = await flow.async_step_phase_device({"phase_device": "0"})
        result = await flow.async_step_channel_phases(self.navigation_input(result, "back", channel_1="L2"))
        await flow.async_step_phase_device(self.navigation_input(result, "back", phase_device="1"))
        result = await self.choose(flow, "channel_phases", True)
        self.assertEqual("1", result["data_schema"]({})["phase_device"])
        result = await flow.async_step_phase_device(result["data_schema"]({}))
        self.assertEqual("L1", result["data_schema"]({})["channel_1"])
        self.assertFalse(any(command[0] == "write" for command in transport.commands))

    async def test_back_to_slave_selection_cannot_remove_formula_sources(self):
        for cloud in (False, True):
            with self.subTest(cloud=cloud):
                flow = self.flow()
                flow._mode = "cloud" if cloud else "manual"
                flow._ecomain_local_config = {"ecomain_serial": "TEST-NAV-01", "ecomain_host": "example.invalid",
                                               "ecomain_online_slaves": ["1"], "ecomain_firmware_version": 139}
                flow._cloud_username = "test@example.invalid"
                flow._cloud_password = "fake-password"
                flow._cloud_token = "fake-token"
                flow._ecomain_cloud_config = {"ecomain_cloud_master": {"hardware_number": "TEST-NAV-01"},
                    "ecomain_cloud_slaves": [{"hardware_number": "TEST-NAV-01_1", "index": 1}]}
                step = "ecomain_cloud_confirm" if cloud else "ecomain_local_setup"
                select_slaves = getattr(flow, "async_step_" + step)
                await select_slaves()
                await select_slaves({"ecomain_selected_slaves": ["1"]})
                await flow.async_step_measurement_types({"measurement_types": ["power"]})
                await self.choose(flow, "add_formula")
                source = "sub1_ch1_power_avg_1m" if cloud else "sub1_ch1_power_rt"
                await flow.async_step_extra_formula({**self.formula, "extra_entity_sources": [source]})
                result = await flow.async_step_extra_formula_expression({"extra_formula_expression": "a"})
                original = deepcopy(flow._extra_entities)
                result = await flow.async_step_extra_entities(self.navigation_input(result, "back"))
                result = await flow.async_step_measurement_types(self.navigation_input(result, "back"))
                self.assertEqual(step, result["step_id"])
                result = await select_slaves({"ecomain_selected_slaves": []})
                self.assertEqual(step, result["step_id"])
                self.assertEqual("slave_in_use", result["errors"]["base"])
                self.assertEqual(original, flow._extra_entities)
