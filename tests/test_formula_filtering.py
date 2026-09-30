"""Exercise firmware-filtered measurement groups through rendered formula steps."""

from types import SimpleNamespace
import unittest

from flow_test_support import formula_source_values, load_flow, submit_values


class FormulaFilteringTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    def flow(self, *, options=False, cloud=False, firmware=139, measurements=None):
        data = {
            "device_type": "ecomain",
            "mode": "cloud" if cloud else "manual",
            "ecomain_serial": "TEST-FILTER-001",
            "ecomain_firmware_version": firmware,
        }
        from custom_components.enecess.ecomain.model import available_local_measurements

        if measurements is None:
            measurements = (
                ["power", "energy"]
                if cloud
                else list(available_local_measurements(firmware))
            )
        if options:
            return self.module.EnecessOptionsFlow(
                SimpleNamespace(
                    data=data,
                    options={"measurement_types": measurements},
                    entry_id="filter-test",
                )
            )
        flow = self.module.ConfigFlow()
        flow._entry_data = data
        flow._measurement_types = measurements
        return flow

    async def submit(self, flow, result, **values):
        return await getattr(flow, "async_step_" + result["step_id"])(
            submit_values(result, values)
        )

    def field(self, result, name):
        return next(
            value
            for key, value in result["data_schema"].schema.items()
            if str(key) == name
        )

    async def sources_page(self, flow, result_type):
        result = await flow.async_step_extra_formula()
        result = await self.submit(
            flow,
            result,
            extra_entity_name="Filtered formula",
            extra_formula_result_type=result_type,
        )
        self.assertEqual(result["step_id"], "extra_formula_sources")
        return result

    async def test_each_group_contains_its_measurement_type_in_both_flows(self):
        prefixes = {
            "power": ("main_l1_power_rt", "main_l2_power_rt"),
            "energy": ("main_l1_energy_fwd_total", "main_l1_energy_rev_total"),
            "voltage": ("main_l1_voltage_rt", "main_l2_voltage_rt"),
        }
        from custom_components.enecess.extra import build_entry_descriptions
        from custom_components.enecess.formula import FORMULA_RESULT_TYPES

        for options in (False, True):
            for result_type in (
                kind for kind in FORMULA_RESULT_TYPES if kind != "number"
            ):
                with self.subTest(options=options, result_type=result_type):
                    flow = self.flow(options=options)
                    result = await self.sources_page(flow, result_type)
                    offered = self.field(
                        result, "extra_formula_sources_" + result_type
                    ).config["options"]
                    keys = {item["value"] for item in offered}
                    self.assertTrue(keys)
                    descriptions = {
                        desc.key: desc
                        for desc in build_entry_descriptions(*flow._formula_context)
                    }
                    self.assertTrue(
                        all(
                            (
                                descriptions[key].spec.kind == "apparent_energy"
                                and descriptions[key].device_class is None
                                if result_type == "apparent_energy"
                                else descriptions[key].device_class == result_type
                            )
                            for key in keys
                        )
                    )
                    for expected in prefixes.get(result_type, ()):
                        self.assertIn(expected, keys)

    async def test_sources_are_dropdowns_and_submit_multiple_values_together(self):
        for options in (False, True):
            flow = self.flow(options=options)
            result = await self.sources_page(flow, "power")
            control = self.field(result, "extra_formula_sources_power")
            self.assertEqual(control.config["mode"], "dropdown")
            self.assertTrue(control.config["multiple"])
            result = await self.submit(
                flow,
                result,
                extra_formula_sources_power=["main_l1_power_rt", "main_l2_power_rt"],
            )
            self.assertEqual(result["step_id"], "extra_formula_expression")
            result = await self.submit(flow, result, extra_formula_expression="a-b")
            self.assertEqual(
                flow._extra_entities[0]["variables"],
                {"a": "main_l1_power_rt", "b": "main_l2_power_rt"},
            )

    async def test_cloud_cumulative_active_energy_group_excludes_per_minute_deltas(
        self,
    ):
        result = await self.sources_page(self.flow(cloud=True), "energy")
        keys = {
            item["value"]
            for item in self.field(result, "extra_formula_sources_energy").config[
                "options"
            ]
        }
        self.assertIn("main_all_energy_accumulated", keys)
        self.assertTrue(all(key.endswith("_energy_accumulated") for key in keys))

    async def test_type_page_includes_number_and_defers_sources_to_next_page(self):
        result = await self.flow().async_step_extra_formula()
        self.assertIn(
            "number", self.field(result, "extra_formula_result_type").config["options"]
        )
        self.assertNotIn(
            "extra_entity_sources", {str(key) for key in result["data_schema"].schema}
        )

    async def test_changing_type_on_back_clears_sources_and_expression(self):
        flow = self.flow()
        result = await self.sources_page(flow, "power")
        result = await self.submit(
            flow, result, extra_formula_sources_power=["main_l1_power_rt"]
        )
        result = await self.submit(
            flow, result, flow_action="back", extra_formula_expression="a * 2"
        )
        self.assertEqual(result["step_id"], "extra_formula_sources")
        result = await self.submit(flow, result, flow_action="back")
        self.assertEqual(result["step_id"], "extra_formula")
        result = await self.submit(flow, result, extra_formula_result_type="voltage")
        self.assertEqual(result["data_schema"]({})["extra_formula_sources_power"], [])
        result = await self.submit(
            flow, result, extra_formula_sources_voltage=["main_l1_voltage_rt"]
        )
        self.assertEqual(result["data_schema"]({})["extra_formula_expression"], "")
        self.assertEqual(flow._formula_draft["variables"], {"a": "main_l1_voltage_rt"})

    async def test_empty_selection_stays_on_sources_page(self):
        flow = self.flow()
        result = await self.sources_page(flow, "power")
        result = await self.submit(flow, result, extra_formula_sources_power=[])
        self.assertEqual(result["step_id"], "extra_formula_sources")
        self.assertEqual(result["errors"]["base"], "formula_sources_invalid")
        self.assertFalse(flow._extra_entities)

    async def test_result_choices_follow_firmware_mode_and_enabled_measurements(self):
        cases = (
            (136, False, None, ["power", "energy"]),
            (138, False, None, ["power", "energy"]),
            (None, False, None, ["power", "energy"]),
            (139, False, ["voltage"], ["voltage"]),
            (139, False, ["energy_forward"], ["energy"]),
            (139, False, ["reactive_energy_reverse"], ["reactive_energy"]),
            (136, False, ["power", "voltage"], ["power"]),
            (139, True, None, ["power", "energy"]),
            (139, True, ["energy"], ["energy"]),
        )
        for options in (False, True):
            for firmware, cloud, measurements, expected in cases:
                with self.subTest(
                    options=options,
                    firmware=firmware,
                    cloud=cloud,
                    measurements=measurements,
                ):
                    flow = self.flow(
                        options=options,
                        cloud=cloud,
                        firmware=firmware,
                        measurements=measurements,
                    )
                    result = await flow.async_step_extra_formula()
                    self.assertEqual(
                        self.field(result, "extra_formula_result_type").config[
                            "options"
                        ],
                        [*expected, "number"],
                    )
                    self.assertEqual(
                        result["data_schema"]({})["extra_formula_result_type"],
                        expected[0],
                    )
                    for kind in [*expected, "number"]:
                        result = await self.sources_page(flow, kind)
                        source_kind = expected[0] if kind == "number" else kind
                        choices = self.field(
                            result, "extra_formula_sources_" + source_kind
                        ).config["options"]
                        self.assertTrue(choices)
                        result = await self.submit(
                            flow,
                            result,
                            **formula_source_values(result, [choices[0]["value"]]),
                        )
                        result = await self.submit(
                            flow, result, extra_formula_expression="a"
                        )
                        self.assertFalse(result.get("errors"))
                        self.assertEqual(flow._extra_entities[-1]["result_type"], kind)

    async def test_measurement_changes_refresh_formula_choices_without_stale_default(
        self,
    ):
        for options in (False, True):
            flow = self.flow(options=options)
            result = await flow.async_step_measurement_types()
            result = await self.submit(flow, result, measurement_types=["voltage"])
            result = await self.submit(flow, result, extra_action="add_formula")
            self.assertEqual(
                self.field(result, "extra_formula_result_type").config["options"],
                ["voltage", "number"],
            )
            self.assertEqual(
                result["data_schema"]({})["extra_formula_result_type"], "voltage"
            )
            result = await self.submit(flow, result, extra_entity_name="Voltage only")
            self.assertEqual(result["step_id"], "extra_formula_sources")
            self.assertFalse(result.get("errors"))

    async def test_no_supported_sources_does_not_invent_a_default_type(self):
        flow = self.flow(options=True, firmware=136, measurements=["voltage"])
        result = await flow.async_step_extra_formula()
        self.assertEqual(
            self.field(result, "extra_formula_result_type").config["options"], []
        )
        self.assertNotIn("extra_formula_result_type", result["data_schema"]({}))
        self.assertEqual(result["errors"]["base"], "formula_sources_invalid")
        result = await self.submit(flow, result, flow_action="cancel")
        self.assertEqual(result["type"], "abort")

    async def test_extra_creation_actions_follow_enabled_sources(self):
        cases = (
            (False, ["voltage"], False, []),
            (False, ["frequency"], False, []),
            (False, ["power"], True, ["power"]),
            (False, ["energy_reverse"], False, ["energy"]),
            (True, ["energy"], False, ["energy"]),
            (True, ["power"], True, ["power"]),
            (True, ["power", "energy"], True, ["power", "energy"]),
        )
        for options in (False, True):
            for cloud, measurements, transform, aggregate_kinds in cases:
                with self.subTest(
                    options=options, cloud=cloud, measurements=measurements
                ):
                    flow = self.flow(
                        options=options, cloud=cloud, measurements=measurements
                    )
                    result = (
                        await flow._show_options_menu()
                        if options
                        else await flow.async_step_extra_entities()
                    )
                    actions = self.field(result, "extra_action").config["options"]
                    self.assertEqual("add_transform" in actions, transform)
                    self.assertEqual("add_aggregate" in actions, bool(aggregate_kinds))
                    self.assertIn("add_formula", actions)
                    if aggregate_kinds:
                        result = await self.submit(
                            flow, result, extra_action="add_aggregate"
                        )
                        self.assertEqual(
                            self.field(result, "extra_entity_source_kind").config[
                                "options"
                            ],
                            aggregate_kinds,
                        )
                        for kind in aggregate_kinds:
                            result = await flow.async_step_extra_aggregate_kind()
                            result = await self.submit(
                                flow, result, extra_entity_source_kind=kind
                            )
                            sources = [
                                item["value"]
                                for item in self.field(
                                    result, "extra_entity_sources"
                                ).config["options"][:2]
                            ]
                            self.assertEqual(len(sources), 2)
                            result = await self.submit(
                                flow,
                                result,
                                extra_entity_name="Supported aggregate",
                                extra_entity_operation="sum",
                                extra_entity_sources=sources,
                            )
                            self.assertFalse(result.get("errors"))
                            self.assertEqual(
                                flow._extra_entities[-1]["sources"], sources
                            )
