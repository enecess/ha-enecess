"""Regression tests for credentials and extra-entity input validation."""

from copy import deepcopy
import types
import unittest
from unittest.mock import AsyncMock

from flow_test_support import load_flow, submit_values


class FlowInputValidationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    def extra_flow(self, options):
        data = {"device_type": "ecomain", "mode": "manual",
                "ecomain_serial": "TEST-VALIDATION-01", "ecomain_firmware_version": 139}
        if options:
            return self.module.EnecessOptionsFlow(types.SimpleNamespace(
                data=data, options={}, entry_id="test-validation"))
        flow = self.module.ConfigFlow()
        flow.context = {}
        flow._entry_data = data
        return flow

    async def submit(self, flow, result, **values):
        return await getattr(flow, "async_step_" + result["step_id"])(submit_values(result, values))

    async def extra_form(self, flow, options, aggregate):
        result = await flow._show_options_menu() if options else await flow.async_step_extra_entities()
        result = await self.submit(flow, result, extra_action="add_aggregate" if aggregate else "add_transform")
        if aggregate:
            result = await self.submit(flow, result, extra_entity_source_kind="power")
        return result

    async def test_cloud_password_whitespace_survives_login_and_entry_creation(self):
        for device in ("ecomain", "ecoplug"):
            with self.subTest(device=device):
                flow = self.module.ConfigFlow()
                flow.context = {}
                password = " fake-secret\t "

                async def authenticate(username, supplied_password):
                    if username != "test@example.invalid" or supplied_password != password:
                        raise self.module.EnecessAuthError("Invalid test credentials")
                    return "fake-token"

                flow._cloud_api = types.SimpleNamespace(
                    generate_token=AsyncMock(side_effect=authenticate),
                    get_hardware_list=AsyncMock(side_effect=lambda token, hardware_type, parent_id=None:
                        [{"id": 1, "hardware_number": "TEST-VALIDATION-01"}]
                        if hardware_type in (0, 2) else []))
                result = await flow.async_step_user()
                result = await self.submit(flow, result, device_type=device)
                if device == "ecomain":
                    result = await self.submit(flow, result, mode="cloud")
                username = " test@example.invalid " if device == "ecomain" else "test@example.invalid"
                result = await self.submit(flow, result, username=username, password=password)
                self.assertEqual("ecomain_cloud_master" if device == "ecomain" else "ecoplug_select",
                                 result["step_id"])
                if device == "ecomain":
                    result = await self.submit(flow, result, ecomain_cloud_master_id="1")
                    result = await self.submit(flow, result)
                    result = await self.submit(flow, result, measurement_types=["power"])
                    result = await self.submit(flow, result, extra_action="finish")
                else:
                    result = await self.submit(flow, result, ecoplug_selected=["TEST-VALIDATION-01"])
                self.assertEqual("create_entry", result["type"])
                self.assertEqual(password, result["data"]["password"])
                self.assertEqual("test@example.invalid", result["data"]["username"])

    async def test_blank_extra_names_are_rejected_then_corrected_in_place(self):
        for options in (False, True):
            for operation in ("invert", "absolute", "sum", "average"):
                for name in ("", " \t "):
                    with self.subTest(options=options, operation=operation, name=name):
                        flow = self.extra_flow(options)
                        aggregate = operation in ("sum", "average")
                        result = await self.extra_form(flow, options, aggregate)
                        values = {"extra_entity_name": name, "extra_entity_operation": operation}
                        values.update({"extra_entity_sources": ["main_l1_power_rt", "main_l2_power_rt"]}
                                      if aggregate else {"extra_entity_source": "main_l1_power_rt"})
                        result = await self.submit(flow, result, **values)
                        self.assertEqual("extra_aggregate" if aggregate else "extra_transform", result["step_id"])
                        self.assertEqual("extra_name_required", result["errors"].get("extra_entity_name"))
                        self.assertEqual([], flow._extra_entities)
                        defaults = result["data_schema"]({})
                        for key, value in values.items():
                            self.assertEqual(value, defaults[key])
                        result = await self.submit(flow, result, extra_entity_name="  Corrected name  ")
                        self.assertEqual("init" if options else "extra_entities", result["step_id"])
                        self.assertEqual(1, len(flow._extra_entities))
                        self.assertEqual("Corrected name", flow._extra_entities[0]["name"])

    async def test_aggregate_requires_two_sources_and_keeps_draft(self):
        for options in (False, True):
            for selected in ([], ["main_l1_power_rt"]):
                with self.subTest(options=options, selected=selected):
                    flow = self.extra_flow(options)
                    result = await self.extra_form(flow, options, True)
                    result = await self.submit(flow, result, extra_entity_name="Test aggregate",
                                               extra_entity_operation="average", extra_entity_sources=selected)
                    self.assertEqual("extra_aggregate", result["step_id"])
                    self.assertEqual("aggregate_sources_required", result["errors"].get("extra_entity_sources"))
                    self.assertEqual([], flow._extra_entities)
                    defaults = result["data_schema"]({})
                    self.assertEqual("Test aggregate", defaults["extra_entity_name"])
                    self.assertEqual("average", defaults["extra_entity_operation"])
                    self.assertEqual(selected, defaults["extra_entity_sources"])
                    result = await self.submit(flow, result,
                        extra_entity_sources=["main_l1_power_rt", "main_l2_power_rt"])
                    self.assertEqual("init" if options else "extra_entities", result["step_id"])
                    self.assertEqual(1, len(flow._extra_entities))
                    self.assertEqual("average", flow._extra_entities[0]["operation"])

    async def test_invalid_extra_draft_can_go_back_or_cancel_without_saving(self):
        for options in (False, True):
            for aggregate in (False, True):
                for action in ("back", "cancel"):
                    with self.subTest(options=options, aggregate=aggregate, action=action):
                        flow = self.extra_flow(options)
                        result = await self.extra_form(flow, options, aggregate)
                        saved = deepcopy(flow._extra_entities)
                        values = {"extra_entity_name": "  ",
                                  "extra_entity_operation": "sum" if aggregate else "invert"}
                        values.update({"extra_entity_sources": []} if aggregate
                                      else {"extra_entity_source": "main_l1_power_rt"})
                        result = await self.submit(flow, result, **values)
                        self.assertTrue(result.get("errors"))
                        result = await self.submit(flow, result, flow_action=action)
                        expected = "extra_aggregate_kind" if aggregate and action == "back" else (
                            "init" if options else "extra_entities")
                        self.assertEqual(expected, result["step_id"])
                        self.assertEqual(saved, flow._extra_entities)
