"""Exercise formula creation and editing through both configuration flows."""
import types
import unittest

from flow_test_support import load_flow


class FormulaFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)
        self.data = {"device_type": "ecomain", "mode": "manual", "ecomain_serial": "TEST-MAIN-01", "ecomain_firmware_version": 139}
        self.sources = ["main_l1_power_rt", "main_l2_power_rt"]

    def flow(self, options=False, extras=None):
        if options:
            return self.module.EnecessOptionsFlow(types.SimpleNamespace(
                data=self.data, options={"extra_entities": extras or []}, entry_id="test"))
        flow = self.module.ConfigFlow()
        flow._entry_data = dict(self.data)
        flow._extra_entities = extras or []
        return flow

    async def create(self, flow, expression="max(a - b, 0)"):
        self.assertTrue(hasattr(flow, "async_step_extra_formula"))
        result = await flow.async_step_extra_formula({"extra_entity_name": "Net power",
            "extra_formula_result_type": "power", "extra_entity_sources": self.sources})
        self.assertEqual("extra_formula_expression", result["step_id"])
        self.assertIn("a", result["description_placeholders"]["variables"])
        return await flow.async_step_extra_formula_expression({"extra_formula_expression": expression})

    async def test_add_in_initial_and_options_flow(self):
        for options in (False, True):
            with self.subTest(options=options):
                flow = self.flow(options)
                result = await self.create(flow)
                self.assertEqual("init" if options else "extra_entities", result["step_id"])
                extra = flow._extra_entities[0]
                self.assertEqual("formula", extra["operation"])
                self.assertEqual("max(a - b, 0)", extra["expression"])
                self.assertEqual({"a": self.sources[0], "b": self.sources[1]}, extra["variables"])
                self.assertEqual("power", extra["result_type"])
                self.assertEqual(0, extra["device_index"])

    async def test_entry_menu_routes_formula_action(self):
        flow = self.flow()
        result = await flow.async_step_extra_entities({"extra_action": "add_formula"})
        self.assertEqual("extra_formula", result["step_id"])

    async def test_options_menu_routes_formula_action(self):
        flow = self.flow(True)
        result = await flow.async_step_init({"extra_action": "add_formula"})
        self.assertEqual("extra_formula", result["step_id"])

    async def test_invalid_inputs_do_not_create_entity(self):
        flow = self.flow()
        self.assertTrue(hasattr(flow, "async_step_extra_formula"))
        result = await flow.async_step_extra_formula({"extra_entity_name": "Bad", "extra_formula_result_type": "power",
                                                    "extra_entity_sources": ["missing_source"]})
        self.assertEqual("formula_sources_invalid", result["errors"]["base"])
        result = await self.create(flow, "__import__('os')")
        self.assertEqual("formula_invalid", result["errors"]["base"])
        self.assertEqual([], flow._extra_entities)

    async def test_unused_sources_are_not_dependencies(self):
        flow = self.flow()
        await self.create(flow, "abs(b)")
        self.assertEqual([self.sources[1]], flow._extra_entities[0]["sources"])
        self.assertEqual({"b": self.sources[1]}, flow._extra_entities[0]["variables"])

    async def test_edit_preserves_identity_and_variable_names(self):
        flow = self.flow(True)
        await self.create(flow, "abs(b)")
        key = flow._extra_entities[0]["key"]
        result = await flow.async_step_extra_formula_edit({"extra_formula_entity": key})
        self.assertEqual("extra_formula", result["step_id"])
        result = await flow.async_step_extra_formula({"extra_entity_name": "Updated power", "extra_formula_result_type": "power",
                                                    "extra_entity_sources": [self.sources[1]]})
        self.assertIn("b", result["description_placeholders"]["variables"])
        await flow.async_step_extra_formula_expression({"extra_formula_expression": "b / 2"})
        self.assertEqual(1, len(flow._extra_entities))
        self.assertEqual(key, flow._extra_entities[0]["key"])
        self.assertEqual("b / 2", flow._extra_entities[0]["expression"])

    async def test_edit_cannot_change_result_type(self):
        flow = self.flow(True)
        await self.create(flow)
        key = flow._extra_entities[0]["key"]
        await flow.async_step_extra_formula_edit({"extra_formula_entity": key})
        result = await flow.async_step_extra_formula({"extra_entity_name": "Changed", "extra_formula_result_type": "energy",
                                                    "extra_entity_sources": self.sources})
        self.assertEqual("formula_result_type_locked", result["errors"]["base"])
        self.assertEqual("power", flow._extra_entities[0]["result_type"])

    async def test_formula_source_is_protected_from_measurement_removal(self):
        flow = self.flow(True)
        await self.create(flow)
        result = await flow.async_step_measurement_types({"measurement_types": ["energy_forward"]})
        self.assertEqual("measurement_in_use", result["errors"]["base"])

    async def test_reordering_edited_sources_does_not_rebind_variables(self):
        flow = self.flow(True)
        await self.create(flow, "a - b")
        original = dict(flow._extra_entities[0])
        await flow.async_step_extra_formula_edit({"extra_formula_entity": original["key"]})
        await flow.async_step_extra_formula({"extra_entity_name": "Net power", "extra_formula_result_type": "power",
                                            "extra_entity_sources": list(reversed(self.sources))})
        await flow.async_step_extra_formula_expression({"extra_formula_expression": "a - b"})
        self.assertEqual(original["variables"], flow._extra_entities[0]["variables"])
        self.assertEqual(original["key"], flow._extra_entities[0]["key"])

    async def test_sources_are_revalidated_before_saving_expression(self):
        flow = self.flow()
        self.assertTrue(hasattr(flow, "async_step_extra_formula"))
        await flow.async_step_extra_formula({"extra_entity_name": "Net power", "extra_formula_result_type": "power",
                                            "extra_entity_sources": self.sources})
        flow._measurement_types = ["energy_forward"]
        result = await flow.async_step_extra_formula_expression({"extra_formula_expression": "a-b"})
        self.assertEqual("formula_sources_invalid", result["errors"]["base"])
        self.assertEqual([], flow._extra_entities)

    async def test_duplicate_sources_formulas_get_distinct_ids_and_remove_independently(self):
        flow = self.flow(True)
        await self.create(flow, "a+b")
        first = flow._extra_entities[0]["key"]
        await flow.async_step_init({"extra_action": "add_formula"})
        await self.create(flow, "a-b")
        second = flow._extra_entities[1]["key"]
        self.assertNotEqual(first, second)
        await flow.async_step_extra_remove({"extra_entity_remove": first})
        self.assertEqual([second], [extra["key"] for extra in flow._extra_entities])

    async def test_cloud_sources_and_extended_local_sources_can_be_used(self):
        cloud = self.flow(True)
        cloud._entry.data["mode"] = "cloud"
        cloud._options["measurement_types"] = ["power", "energy"]
        result = await cloud.async_step_extra_formula({"extra_entity_name": "Cloud net power", "extra_formula_result_type": "power",
            "extra_entity_sources": ["main_all_power_avg_1m", "main_ch1_power_avg_1m"]})
        self.assertEqual("extra_formula_expression", result["step_id"])
        await cloud.async_step_extra_formula_expression({"extra_formula_expression": "a-b"})
        self.assertEqual(1, len(cloud._extra_entities))
        self.data["mode"] = "manual"
        local = self.flow()
        local._measurement_types = ["voltage"]
        result = await local.async_step_extra_formula({"extra_entity_name": "Mean voltage", "extra_formula_result_type": "voltage",
            "extra_entity_sources": ["main_l1_voltage_rt", "main_l2_voltage_rt"]})
        self.assertEqual("extra_formula_expression", result["step_id"])
        await local.async_step_extra_formula_expression({"extra_formula_expression": "(a+b)/2"})
        self.assertEqual("voltage", local._extra_entities[0]["result_type"])
