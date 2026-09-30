"""Preserve configured measurements and entity identities across capability loss."""

from copy import deepcopy
import importlib
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from flow_test_support import load_flow, submit_values


class OptionsPreservationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)
        self.entry = SimpleNamespace(
            entry_id="fictional-preservation",
            data={"device_type": "ecomain", "mode": "manual",
                  "ecomain_serial": "FICTIONAL-PRESERVATION-001",
                  "ecomain_host": "192.0.2.10", "ecomain_firmware_version": 139},
            options={"measurement_types": ["power", "voltage"],
                     "ecomain_selected_slaves": [], "extra_entities": []},
        )
        self.formula = {
            "key": "extra_formula_voltage", "name": "Voltage copy",
            "operation": "formula", "result_type": "voltage",
            "sources": ["main_l1_voltage_rt"],
            "variables": {"a": "main_l1_voltage_rt"}, "expression": "a",
        }
        self.records = {
            "sensor.my_voltage": SimpleNamespace(
                entity_id="sensor.my_voltage", domain="sensor",
                unique_id="ecomain:FICTIONAL-PRESERVATION-001:key_main_l1_voltage_rt:mode_local",
            )
        }
        registry = SimpleNamespace(
            async_get_entity_id=lambda domain, platform, unique_id: next(
                (item.entity_id for item in self.records.values()
                 if item.unique_id == unique_id), None),
            async_remove=lambda entity_id: self.records.pop(entity_id),
        )
        self.enterContext(patch.object(self.module.er, "async_get", return_value=registry, create=True))
        self.enterContext(patch.object(self.module.er, "async_entries_for_config_entry",
                                     side_effect=lambda registry, entry_id: list(self.records.values()), create=True))
        self.enterContext(patch.object(self.module.dr, "async_get", return_value=object(), create=True))
        self.enterContext(patch.object(self.module.dr, "async_entries_for_config_entry", return_value=[], create=True))

    def flow(self):
        flow = self.module.EnecessOptionsFlow(self.entry)

        def update(entry, **changes):
            entry.__dict__.update(changes)

        flow.hass = SimpleNamespace(config_entries=SimpleNamespace(async_update_entry=update))
        return flow

    def client(self, firmware=None):
        async def read(address, count):
            if firmware is None:
                raise ConnectionError("offline fixture")
            return SimpleNamespace(registers=[firmware] if address == 3009 else [0, 0, 0])

        self.enterContext(patch.object(self.module, "EnecessModbusClient", return_value=SimpleNamespace(
            read_holding_registers=read, async_close=AsyncMock())))

    async def submit(self, flow, result, **values):
        return await getattr(flow, "async_step_" + result["step_id"])(submit_values(result, values))

    async def test_offline_unchanged_save_keeps_measurements_formula_and_custom_entity_id(self):
        self.entry.options["extra_entities"] = [self.formula]
        original = deepcopy(self.entry.options)
        self.client()
        flow = self.flow()
        result = await flow.async_step_init()
        self.assertEqual({"base": "cannot_connect_local"}, result["errors"])
        self.assertIn("voltage", flow._formula_source_groups())
        result = await self.submit(flow, result, extra_action="measurement_types")
        self.assertEqual(["power", "voltage"], submit_values(result, {})["measurement_types"])
        result = await self.submit(flow, result, flow_action="save")
        self.assertFalse(result.get("errors"))
        result = await self.submit(flow, result, extra_action="finish")
        self.assertEqual(original, result["data"])
        self.assertIn("sensor.my_voltage", self.records)

    async def test_confirmed_downgrade_save_keeps_configured_types_but_filters_sources(self):
        self.client(138)
        flow = self.flow()
        result = await flow.async_step_init()
        self.assertNotIn("voltage", flow._formula_source_groups())
        result = await self.submit(flow, result, extra_action="measurement_types")
        self.assertEqual(["power", "voltage"], submit_values(result, {})["measurement_types"])
        result = await self.submit(flow, result, flow_action="save")
        result = await self.submit(flow, result, extra_action="finish")
        self.assertEqual(["power", "voltage"], result["data"]["measurement_types"])
        self.assertEqual(138, self.entry.data["ecomain_firmware_version"])
        self.assertIn("sensor.my_voltage", self.records)

    async def test_failed_refresh_does_not_reuse_capabilities_for_changed_target_or_unknown_firmware(self):
        self.client()
        flow = self.flow()
        self.entry.data = {**self.entry.data, "ecomain_host": "192.0.2.11"}
        await flow.async_step_init()
        self.assertNotIn("voltage", flow._formula_source_groups())
        self.entry.data.pop("ecomain_firmware_version")
        flow = self.flow()
        await flow.async_step_init()
        self.assertNotIn("voltage", flow._formula_source_groups())

    async def test_explicit_deselection_removes_entity_but_formula_dependency_blocks_it(self):
        self.client(138)
        flow = self.flow()
        result = await flow.async_step_init()
        result = await self.submit(flow, result, extra_action="measurement_types")
        result = await self.submit(flow, result, measurement_types=["power"])
        result = await self.submit(flow, result, extra_action="finish")
        self.assertEqual(["power"], result["data"]["measurement_types"])
        self.assertNotIn("sensor.my_voltage", self.records)
        self.entry.options["extra_entities"] = [self.formula]
        flow = self.flow()
        result = await flow.async_step_init()
        result = await self.submit(flow, result, extra_action="measurement_types")
        result = await self.submit(flow, result, measurement_types=["power"])
        self.assertEqual({"base": "measurement_in_use"}, result["errors"])

    async def test_navigation_restore_does_not_assign_old_firmware_to_a_new_target(self):
        flow = self.flow()
        snapshot = flow._navigation_snapshot()
        self.entry.data = {**self.entry.data, "ecomain_host": "192.0.2.11"}
        self.client(138)
        await flow._async_refresh_local_slaves()
        flow._navigation_restore(snapshot)
        self.assertNotIn("voltage", flow._formula_source_groups())

    async def test_missing_saved_host_does_not_confirm_cached_capabilities(self):
        self.entry.data.pop("ecomain_host")
        flow = self.flow()
        result = await flow.async_step_init()
        self.assertEqual({"base": "cannot_connect_local"}, result["errors"])
        self.assertNotIn("voltage", flow._formula_source_groups())

    async def test_registry_cleanup_preserves_configured_unsupported_entities(self):
        self.entry.data["ecomain_firmware_version"] = 138
        registry_module = importlib.import_module("custom_components.enecess.registry")
        registry_module.async_remove_unconfigured_registry_entries(SimpleNamespace(), self.entry)
        self.assertIn("sensor.my_voltage", self.records)

    async def test_unsupported_extra_keeps_its_ecosub_unique_id(self):
        self.entry.options["ecomain_selected_slaves"] = [1]
        self.entry.options["extra_entities"] = [{
            "key": "extra_voltage_average", "operation": "average",
            "sources": ["sub1_ch1_voltage_rt", "sub1_ch2_voltage_rt"],
        }]
        self.entry.data["ecomain_firmware_version"] = 138
        unique_ids = self.module.build_entry_sensor_unique_ids(self.entry.data, self.entry.options)
        self.assertIn(
            "ecomain:FICTIONAL-PRESERVATION-001:sub_1:key_extra_voltage_average:mode_local",
            unique_ids,
        )
