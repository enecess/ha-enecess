"""Validate the formula wizard with real Home Assistant selectors."""

from types import SimpleNamespace

from homeassistant.helpers.selector import SelectSelectorMode

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
                fields["extra_formula_result_type"].config["options"], expected
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
                for result_type in ("power", "energy"):
                    result = await flow.async_step_extra_formula()
                    fields = {
                        str(key): value
                        for key, value in result["data_schema"].schema.items()
                    }
                    self.assertEqual(
                        fields["extra_formula_result_type"].config["options"],
                        ["power", "energy"],
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
                        for option in fields["extra_entity_sources"].config["options"][
                            :2
                        ]
                    ]
                    self.assertEqual(len(sources), 2)
                    result = await flow.async_step_extra_formula_sources(
                        result["data_schema"]({"extra_entity_sources": sources})
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
            self.assertNotIn(
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
            control = fields["extra_entity_sources"]
            self.assertEqual(control.config["mode"], SelectSelectorMode.LIST)
            self.assertTrue(control.config["multiple"])
            self.assertTrue(
                all("_energy_" in item["value"] for item in control.config["options"])
            )
            sources = ["main_l1_energy_fwd_total", "main_l1_energy_rev_total"]
            result = await flow.async_step_extra_formula_sources(
                result["data_schema"]({"extra_entity_sources": sources})
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
