"""Validate the formula wizard with real Home Assistant selectors."""

from types import SimpleNamespace

from homeassistant.helpers.selector import SelectSelectorMode
import voluptuous as vol

from custom_components.enecess.config_flow import ConfigFlow
from test_runtime import RealHARuntimeFixture


class FormulaSelectionTests(RealHARuntimeFixture):
    async def test_detected_firmware_flows_through_measurements_to_formula_choices(
        self,
    ):
        for firmware in (136, 138, 139):

            async def read(address, count, version=firmware):
                return SimpleNamespace(
                    registers=[version] if address == 3009 else [0] * count
                )

            self.mocks["read_holding_registers"].side_effect = read
            flow = ConfigFlow()
            flow.hass = self.hass
            flow.context = {}
            flow._mode = "manual"
            flow._ecomain_local_config = {
                "ecomain_host": "192.0.2.1",
                "ecomain_serial": "FICTIONAL-CAPABILITIES-001",
            }
            result = await flow.async_step_ecomain_local_setup()
            self.assertEqual(result["step_id"], "measurement_types")
            fields = {
                str(key): value for key, value in result["data_schema"].schema.items()
            }
            choices = fields["measurement_types"].config["options"]
            self.assertEqual("voltage" in choices, firmware >= 139)
            selected = ["voltage"] if firmware >= 139 else ["power", "energy_forward"]
            result = await flow.async_step_measurement_types(
                result["data_schema"]({"measurement_types": selected})
            )
            result = await flow.async_step_extra_entities(
                result["data_schema"]({"extra_action": "add_formula"})
            )
            fields = {
                str(key): value for key, value in result["data_schema"].schema.items()
            }
            expected = ["voltage"] if firmware >= 139 else ["power", "energy"]
            self.assertEqual(
                fields["extra_formula_result_type"].config["options"],
                [*expected, "number"],
            )
            result = await flow.async_step_extra_formula(
                result["data_schema"]({"extra_entity_name": "Detected capabilities"})
            )
            self.assertEqual(result["step_id"], "extra_formula_sources")
            self.assertFalse(result.get("errors"))

    async def test_extra_actions_and_aggregate_choices_follow_enabled_measurements(
        self,
    ):
        cases = (
            ("local", ["voltage"], False, []),
            ("local", ["power"], True, ["power"]),
            ("main", ["energy"], False, ["energy"]),
        )
        for kind, measurements, transform, aggregate in cases:
            for options in (False, True):
                entry = self.make_entry(kind)
                self.hass.config_entries.async_update_entry(
                    entry, options={"measurement_types": measurements}
                )
                if options:
                    flow = ConfigFlow.async_get_options_flow(entry)
                    flow.handler = entry.entry_id
                else:
                    flow = ConfigFlow()
                    flow._entry_data = dict(entry.data)
                    flow._measurement_types = measurements
                flow.hass = self.hass
                flow.context = {}
                result = (
                    await flow._show_options_menu()
                    if options
                    else await flow.async_step_extra_entities()
                )
                fields = {
                    str(key): value
                    for key, value in result["data_schema"].schema.items()
                }
                actions = fields["extra_action"].config["options"]
                self.assertEqual("add_transform" in actions, transform)
                self.assertEqual("add_aggregate" in actions, bool(aggregate))
                if aggregate:
                    handler = (
                        flow.async_step_init
                        if options
                        else flow.async_step_extra_entities
                    )
                    result = await handler(
                        result["data_schema"]({"extra_action": "add_aggregate"})
                    )
                    fields = {
                        str(key): value
                        for key, value in result["data_schema"].schema.items()
                    }
                    self.assertEqual(
                        fields["extra_entity_source_kind"].config["options"], aggregate
                    )
                    result = await flow.async_step_extra_aggregate_kind(
                        result["data_schema"](
                            {"extra_entity_source_kind": aggregate[0]}
                        )
                    )
                    self.assertFalse(result.get("errors"))

    async def test_setup_connection_failure_does_not_claim_firmware_is_old(self):
        self.mocks["read_holding_registers"].side_effect = TimeoutError
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {}
        flow._mode = "manual"
        flow._ecomain_local_config = {
            "ecomain_host": "192.0.2.1",
            "ecomain_serial": "FICTIONAL-VALIDATION-001",
        }
        result = await flow.async_step_ecomain_local_setup()
        self.assertEqual(result["errors"]["base"], "cannot_connect_local")

    async def test_firmware_136_and_cloud_offer_only_usable_formula_types(self):
        for kind in ("local", "main"):
            for options in (False, True):
                entry = self.make_entry(kind)
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, "ecomain_firmware_version": 136}
                )
                if options:
                    flow = ConfigFlow.async_get_options_flow(entry)
                    flow.handler = entry.entry_id
                else:
                    flow = ConfigFlow()
                    flow._entry_data = dict(entry.data)
                flow.hass = self.hass
                flow.context = {}
                for result_type in ("power", "energy", "number"):
                    result = await flow.async_step_extra_formula()
                    fields = {
                        str(key): value
                        for key, value in result["data_schema"].schema.items()
                    }
                    self.assertEqual(
                        fields["extra_formula_result_type"].config["options"],
                        ["power", "energy", "number"],
                    )
                    result = await flow.async_step_extra_formula(
                        result["data_schema"](
                            {
                                "extra_entity_name": "Fictional supported",
                                "extra_formula_result_type": result_type,
                            }
                        )
                    )
                    fields = {
                        str(key): value
                        for key, value in result["data_schema"].schema.items()
                    }
                    sources = [
                        option["value"]
                        for option in fields["extra_formula_sources_power"].config[
                            "options"
                        ][:2]
                    ]
                    self.assertEqual(len(sources), 2)
                    result = await flow.async_step_extra_formula_sources(
                        result["data_schema"]({"extra_formula_sources_power": sources})
                    )
                    result = await flow.async_step_extra_formula_expression(
                        result["data_schema"]({"extra_formula_expression": "a+b"})
                    )
                    self.assertFalse(result.get("errors"))
                    self.assertEqual(
                        flow._extra_entities[-1]["result_type"], result_type
                    )

    async def test_type_then_multi_source_selection_in_setup_and_options(self):
        for options in (False, True):
            entry = self.make_entry("local")
            if options:
                flow = ConfigFlow.async_get_options_flow(entry)
                flow.handler = entry.entry_id
            else:
                flow = ConfigFlow()
                flow._entry_data = dict(entry.data)
            flow.hass = self.hass
            flow.context = {}
            result = await flow.async_step_extra_formula()
            fields = {
                str(key): value for key, value in result["data_schema"].schema.items()
            }
            self.assertIn(
                "number", fields["extra_formula_result_type"].config["options"]
            )
            self.assertNotIn("extra_entity_sources", fields)
            result = await flow.async_step_extra_formula(
                result["data_schema"](
                    {
                        "extra_entity_name": "Fictional active energy",
                        "extra_formula_result_type": "energy",
                    }
                )
            )
            self.assertEqual(result["step_id"], "extra_formula_sources")
            fields = {
                str(key): value for key, value in result["data_schema"].schema.items()
            }
            control = fields["extra_formula_sources_energy"]
            self.assertEqual(control.config["mode"], SelectSelectorMode.DROPDOWN)
            self.assertTrue(control.config["multiple"])
            self.assertIn("extra_formula_sources_power", fields)
            for key in result["data_schema"].schema:
                if str(key).startswith("extra_formula_sources_"):
                    self.assertIsInstance(key, vol.Optional)
                    self.assertNotIsInstance(key, vol.Required)
            self.assertTrue(
                all("_energy_" in item["value"] for item in control.config["options"])
            )
            sources = ["main_l1_energy_fwd_total", "main_l1_energy_rev_total"]
            result = await flow.async_step_extra_formula_sources(
                result["data_schema"]({"extra_formula_sources_energy": sources})
            )
            self.assertEqual(result["step_id"], "extra_formula_expression")
            result = await flow.async_step_extra_formula_expression(
                result["data_schema"]({"extra_formula_expression": "a-b"})
            )
            self.assertFalse(result["errors"])
            self.assertEqual(flow._extra_entities[0]["sources"], sources)

    async def test_cancel_from_source_page_leaves_no_formula(self):
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {}
        flow._entry_data = dict(self.make_entry("local").data)
        await flow.async_step_extra_entities()
        result = await flow.async_step_extra_formula()
        result = await flow.async_step_extra_formula(
            result["data_schema"](
                {
                    "extra_entity_name": "Fictional cancelled",
                    "extra_formula_result_type": "power",
                }
            )
        )
        result = await flow.async_step_extra_formula_sources(
            result["data_schema"]({"flow_action": "cancel"})
        )
        self.assertEqual(result["step_id"], "extra_entities")
        self.assertFalse(flow._extra_entities)

    async def test_grouped_selectors_reject_wrong_group_and_empty_selection(self):
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {}
        flow._entry_data = dict(self.make_entry("local").data)
        flow._measurement_types = ["power", "voltage"]
        result = await flow.async_step_extra_formula()
        result = await flow.async_step_extra_formula(
            result["data_schema"](
                {
                    "extra_entity_name": "Fictional mixed measurements",
                    "extra_formula_result_type": "number",
                }
            )
        )
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(
            [name for name in fields if name.startswith("extra_formula_sources_")],
            ["extra_formula_sources_power", "extra_formula_sources_voltage"],
        )
        voltage = fields["extra_formula_sources_voltage"].config["options"][0]["value"]
        with self.assertRaises(vol.Invalid):
            result["data_schema"]({"extra_formula_sources_power": [voltage]})
        with self.assertRaises(vol.Invalid):
            result["data_schema"]({"extra_formula_sources_voltage": voltage})
        result = await flow.async_step_extra_formula_sources(result["data_schema"]({}))
        self.assertEqual(result["errors"]["base"], "formula_sources_invalid")
        self.assertFalse(flow._extra_entities)

    async def test_no_supported_enabled_sources_do_not_offer_number(self):
        for options in (False, True):
            entry = self.make_entry("local")
            self.hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, "ecomain_firmware_version": 136},
                options={"measurement_types": ["voltage"]},
            )
            if options:
                flow = ConfigFlow.async_get_options_flow(entry)
                flow.handler = entry.entry_id
            else:
                flow = ConfigFlow()
                flow._entry_data = dict(entry.data)
                flow._measurement_types = ["voltage"]
            flow.hass = self.hass
            flow.context = {}
            result = await flow.async_step_extra_formula()
            fields = {
                str(key): value for key, value in result["data_schema"].schema.items()
            }
            self.assertEqual(fields["extra_formula_result_type"].config["options"], [])
            self.assertEqual(result["errors"]["base"], "formula_sources_invalid")

    async def test_cloud_accumulated_and_minute_energy_have_separate_dropdowns(self):
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {}
        flow._entry_data = dict(self.make_entry("main").data)
        flow._measurement_types = ["energy"]
        result = await flow.async_step_extra_formula()
        result = await flow.async_step_extra_formula(
            result["data_schema"](
                {
                    "extra_entity_name": "Fictional cloud energy",
                    "extra_formula_result_type": "number",
                }
            )
        )
        fields = {
            str(key): value for key, value in result["data_schema"].schema.items()
        }
        self.assertEqual(
            [name for name in fields if name.startswith("extra_formula_sources_")],
            ["extra_formula_sources_energy", "extra_formula_sources_energy_delta"],
        )
        selections = {}
        for name in (
            "extra_formula_sources_energy",
            "extra_formula_sources_energy_delta",
        ):
            self.assertEqual(fields[name].config["mode"], SelectSelectorMode.DROPDOWN)
            self.assertTrue(fields[name].config["multiple"])
            selections[name] = [fields[name].config["options"][0]["value"]]
        self.assertNotEqual(*selections.values())
        result = await flow.async_step_extra_formula_sources(
            result["data_schema"](selections)
        )
        self.assertEqual(result["step_id"], "extra_formula_expression")

    async def test_mixed_number_edit_and_back_rebind_and_clear_expression(self):
        for options in (False, True):
            with self.subTest(options=options):
                entry = self.make_entry("local")
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, "ecomain_firmware_version": 139},
                    options={"measurement_types": ["power", "voltage"]},
                )
                if options:
                    flow = ConfigFlow.async_get_options_flow(entry)
                    flow.handler = entry.entry_id
                else:
                    flow = ConfigFlow()
                    flow._entry_data = dict(entry.data)
                    flow._measurement_types = ["power", "voltage"]
                flow.hass = self.hass
                flow.context = {}
                result = (
                    await flow._show_options_menu()
                    if options
                    else await flow.async_step_extra_entities()
                )
                menu_handler = (
                    flow.async_step_init if options else flow.async_step_extra_entities
                )
                result = await menu_handler(
                    result["data_schema"]({"extra_action": "add_formula"})
                )
                result = await flow.async_step_extra_formula(
                    result["data_schema"](
                        {
                            "extra_entity_name": "Fictional mixed number",
                            "extra_formula_result_type": "number",
                        }
                    )
                )
                fields = {
                    str(key): value
                    for key, value in result["data_schema"].schema.items()
                }
                powers = [
                    item["value"]
                    for item in fields["extra_formula_sources_power"].config["options"][
                        :2
                    ]
                ][::-1]
                voltage = fields["extra_formula_sources_voltage"].config["options"][0][
                    "value"
                ]
                # Submit voltage first to verify that groups determine alias order.
                result = await flow.async_step_extra_formula_sources(
                    result["data_schema"](
                        {
                            "extra_formula_sources_voltage": [voltage],
                            "extra_formula_sources_power": powers,
                        }
                    )
                )
                self.assertEqual(
                    flow._formula_draft["variables"],
                    {"a": powers[0], "b": powers[1], "c": voltage},
                )
                result = await flow.async_step_extra_formula_expression(
                    result["data_schema"]({"extra_formula_expression": "b+c"})
                )
                original = dict(flow._extra_entities[0])
                self.assertEqual(original["result_type"], "number")
                result = await menu_handler(
                    result["data_schema"]({"extra_action": "edit_formula"})
                )
                result = await flow.async_step_extra_formula_edit(
                    result["data_schema"]({"extra_formula_entity": original["key"]})
                )
                result = await flow.async_step_extra_formula(result["data_schema"]({}))
                result = await flow.async_step_extra_formula_sources(
                    result["data_schema"]({})
                )
                self.assertEqual(
                    flow._formula_draft["variables"], {"a": powers[1], "b": voltage}
                )
                self.assertEqual(
                    result["data_schema"]({})["extra_formula_expression"], ""
                )
                result = await flow.async_step_extra_formula_expression(
                    result["data_schema"](
                        {"extra_formula_expression": "a/b", "flow_action": "back"}
                    )
                )
                self.assertEqual(result["step_id"], "extra_formula_sources")
                result = await flow.async_step_extra_formula_sources(
                    result["data_schema"]({})
                )
                self.assertEqual(
                    result["data_schema"]({})["extra_formula_expression"], ""
                )
                result = await flow.async_step_extra_formula_expression(
                    result["data_schema"]({"extra_formula_expression": "a/b"})
                )
                self.assertFalse(result.get("errors"))
                self.assertEqual(len(flow._extra_entities), 1)
                self.assertEqual(flow._extra_entities[0]["key"], original["key"])
                self.assertEqual(flow._extra_entities[0]["expression"], "a/b")
                self.assertEqual(
                    flow._extra_entities[0]["variables"], {"a": powers[1], "b": voltage}
                )
