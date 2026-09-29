"""Follow grouped source selection with fictional supported measurements."""

from types import SimpleNamespace
import unittest

from flow_test_support import load_flow, submit_values


class GroupedFormulaTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    def flow(self, *, options=False, firmware=139, cloud=False, measurements=None):
        data = {
            "device_type": "ecomain",
            "mode": "cloud" if cloud else "manual",
            "ecomain_serial": "FICTIONAL-GROUPS-001",
            "ecomain_firmware_version": firmware,
        }
        if measurements is None:
            measurements = (
                ["power", "energy"]
                if cloud
                else ["power", "energy_forward", "voltage", "current"]
            )
        if options:
            return self.module.EnecessOptionsFlow(
                SimpleNamespace(
                    data=data,
                    options={"measurement_types": measurements},
                    entry_id="groups",
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

    def fields(self, result):
        return {str(key): value for key, value in result["data_schema"].schema.items()}

    async def choose_result(self, flow, result_type):
        result = await flow.async_step_extra_formula()
        self.assertIn(
            result_type,
            self.fields(result)["extra_formula_result_type"].config["options"],
        )
        return await self.submit(
            flow,
            result,
            extra_entity_name="Mixed formula",
            extra_formula_result_type=result_type,
        )

    async def test_different_result_types_offer_the_same_enabled_source_groups(self):
        for options in (False, True):
            for result_type in ("power", "energy", "voltage", "number"):
                with self.subTest(options=options, result_type=result_type):
                    result = await self.choose_result(
                        self.flow(options=options), result_type
                    )
                    fields = self.fields(result)
                    self.assertEqual(
                        set(fields) - {"flow_action"},
                        {
                            "extra_formula_sources_power",
                            "extra_formula_sources_energy",
                            "extra_formula_sources_voltage",
                            "extra_formula_sources_current",
                        },
                    )
                    for name, control in fields.items():
                        if name != "flow_action":
                            self.assertEqual(control.config["mode"], "dropdown")
                            self.assertTrue(control.config["multiple"])

    async def test_number_formula_combines_groups_and_keeps_metadata(self):
        for options in (False, True):
            flow = self.flow(options=options)
            result = await self.choose_result(flow, "number")
            result = await self.submit(
                flow,
                result,
                extra_formula_sources_power=["main_l1_power_rt", "main_l2_power_rt"],
                extra_formula_sources_voltage=["main_l1_voltage_rt"],
            )
            self.assertEqual(result["step_id"], "extra_formula_expression")
            self.assertEqual(
                flow._formula_draft["variables"],
                {
                    "a": "main_l1_power_rt",
                    "b": "main_l2_power_rt",
                    "c": "main_l1_voltage_rt",
                },
            )
            result = await self.submit(flow, result, extra_formula_expression="(a+b)/c")
            self.assertFalse(result.get("errors"))
            self.assertEqual(flow._extra_entities[0]["result_type"], "number")
            self.assertEqual(len(flow._extra_entities[0]["sources"]), 3)

    async def test_groups_follow_firmware_and_selection_including_cloud_delta(self):
        cases = (
            (136, False, ["power", "voltage", "energy_forward"], {"power", "energy"}),
            (138, False, ["power", "current"], {"power"}),
            (139, False, ["voltage"], {"voltage"}),
            (139, False, ["reactive_energy_forward"], {"reactive_energy"}),
            (139, True, ["energy"], {"energy", "energy_delta"}),
            (139, True, ["power"], {"power"}),
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
                        firmware=firmware,
                        cloud=cloud,
                        measurements=measurements,
                    )
                    result = await self.choose_result(flow, "number")
                    groups = {
                        name.removeprefix("extra_formula_sources_"): field
                        for name, field in self.fields(result).items()
                        if name != "flow_action"
                    }
                    self.assertEqual(set(groups), expected)
                    for kind, field in groups.items():
                        self.assertTrue(field.config["options"])
                        if kind == "energy_delta":
                            self.assertTrue(
                                all(
                                    item["value"].endswith("_energy_total_1m")
                                    for item in field.config["options"]
                                )
                            )
                        elif kind == "energy" and cloud:
                            self.assertTrue(
                                all(
                                    item["value"].endswith("_energy_accumulated")
                                    for item in field.config["options"]
                                )
                            )

    async def test_empty_all_groups_stays_on_source_page_and_cancel_discards(self):
        flow = self.flow()
        await flow.async_step_extra_entities()
        result = await self.choose_result(flow, "number")
        result = await self.submit(flow, result)
        self.assertEqual(result["step_id"], "extra_formula_sources")
        self.assertEqual(result["errors"]["base"], "formula_sources_invalid")
        result = await self.submit(flow, result, flow_action="cancel")
        self.assertEqual(result["step_id"], "extra_entities")
        self.assertFalse(flow._extra_entities)

    async def test_cross_type_formula_stays_editable_when_result_measurement_is_disabled(
        self,
    ):
        flow = self.flow(options=True)
        result = await self.choose_result(flow, "power")
        result = await self.submit(
            flow,
            result,
            extra_formula_sources_voltage=["main_l1_voltage_rt"],
            extra_formula_sources_current=["main_l1_current_rt"],
        )
        await self.submit(flow, result, extra_formula_expression="a*b")
        original = dict(flow._extra_entities[0])
        result = await flow.async_step_measurement_types()
        result = await self.submit(
            flow, result, measurement_types=["voltage", "current"]
        )
        self.assertFalse(result.get("errors"))
        result = await flow.async_step_extra_formula_edit()
        result = await self.submit(flow, result, extra_formula_entity=original["key"])
        self.assertIn(
            "power", self.fields(result)["extra_formula_result_type"].config["options"]
        )
        self.assertEqual(
            result["data_schema"]({})["extra_formula_result_type"], "power"
        )
        result = await self.submit(flow, result)
        self.assertEqual(result["step_id"], "extra_formula_sources")
        self.assertNotIn("extra_formula_sources_power", self.fields(result))
        result = await self.submit(flow, result)
        await self.submit(flow, result, extra_formula_expression="a*b*0.9")
        self.assertEqual(flow._extra_entities[0]["key"], original["key"])
        self.assertEqual(flow._extra_entities[0]["result_type"], "power")

    async def test_edit_restores_groups_then_rebinds_and_clears_expression(self):
        flow = self.flow(options=True)
        result = await self.choose_result(flow, "number")
        result = await self.submit(
            flow,
            result,
            extra_formula_sources_power=["main_l1_power_rt"],
            extra_formula_sources_voltage=["main_l1_voltage_rt"],
        )
        await self.submit(flow, result, extra_formula_expression="a/b")
        saved = dict(flow._extra_entities[0])
        result = await flow.async_step_extra_formula_edit()
        result = await self.submit(flow, result, extra_formula_entity=saved["key"])
        result = await self.submit(flow, result)
        defaults = result["data_schema"]({})
        self.assertEqual(defaults["extra_formula_sources_power"], ["main_l1_power_rt"])
        self.assertEqual(
            defaults["extra_formula_sources_voltage"], ["main_l1_voltage_rt"]
        )
        result = await self.submit(
            flow,
            result,
            extra_formula_sources_power=[],
            extra_formula_sources_current=["main_l1_current_rt"],
        )
        self.assertEqual(
            flow._formula_draft["variables"],
            {"a": "main_l1_voltage_rt", "b": "main_l1_current_rt"},
        )
        self.assertEqual(result["data_schema"]({})["extra_formula_expression"], "")
        result = await self.submit(flow, result)
        self.assertEqual(result["errors"]["base"], "formula_invalid")
        self.assertEqual(flow._extra_entities[0], saved)
        await self.submit(flow, result, extra_formula_expression="a/b")
        self.assertEqual(flow._extra_entities[0]["key"], saved["key"])
