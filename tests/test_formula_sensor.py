"""Offline formula entity behavior at the coordinator boundary."""
import importlib
import sys
from types import ModuleType, SimpleNamespace
import unittest

from flow_test_support import load_flow


class FormulaSensorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        load_flow(self)

        class CoordinatorEntity:
            def __init__(self, coordinator):
                self.coordinator = coordinator

        sensor = sys.modules["homeassistant.components.sensor"]
        sensor.SensorEntity = type("SensorEntity", (), {})
        sensor.RestoreSensor = type("RestoreSensor", (), {})
        sensor.SensorStateClass.TOTAL = "total"
        sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = dict
        for name, attributes in {
            "homeassistant.helpers.update_coordinator": {"CoordinatorEntity": CoordinatorEntity},
            "homeassistant.helpers.entity_platform": {"AddEntitiesCallback": object},
        }.items():
            module = ModuleType(name)
            module.__dict__.update(attributes)
            sys.modules[name] = module
        self.runtime = importlib.import_module("custom_components.enecess.ecomain.sensor")
        self.extra = importlib.import_module("custom_components.enecess.extra")
        self.coordinator = SimpleNamespace(data={"main_ch1_power_rt": 12, "sub1_ch1_power_rt": 3}, last_update_success=True)
        self.config = {"key": "formula_stable", "name": "Net", "operation": "formula",
                       "sources": ["main_ch1_power_rt", "sub1_ch1_power_rt"],
                       "variables": {"a": "main_ch1_power_rt", "b": "sub1_ch1_power_rt"},
                       "expression": "a - b", "result_type": "power"}
        self.source = sensor.SensorEntityDescription(key="main_ch1_power_rt", native_unit_of_measurement="W", device_class="power", state_class="measurement")

    def entity(self, **changes):
        return self.runtime.EcoMainExtraSensor(self.coordinator, "local", "TEST_FORMULA_001", {**self.config, **changes}, self.source, 0)

    def test_formula_updates_and_recovers_from_invalid_source(self):
        entity = self.entity()
        self.assertEqual(entity.native_value, 9)
        self.assertTrue(entity.available)
        for invalid in (None, "unknown", True, float("inf")):
            self.coordinator.data["sub1_ch1_power_rt"] = invalid
            self.assertIsNone(entity.native_value)
            self.assertFalse(entity.available)
        self.coordinator.data["sub1_ch1_power_rt"] = 15
        self.assertEqual(entity.native_value, -3)
        self.assertTrue(entity.available)

    def test_zero_division_and_invalid_saved_formula_are_unavailable(self):
        self.coordinator.data["sub1_ch1_power_rt"] = 0
        for changes in ({"expression": "a / b"}, {"expression": "a.__class__"},
                        {"variables": []}, {"result_type": "unsupported"}, {"expression": None}):
            entity = self.entity(**changes)
            self.assertFalse(entity.available)
            self.assertIsNone(entity.native_value)

    def test_result_metadata_uses_explicit_type_and_signed_energy_totals(self):
        for result_type, unit, device_class, state_class in [
            ("power", "W", "power", "measurement"), ("energy", "Wh", "energy", "total"),
            ("reactive_energy", "varh", "reactive_energy", "total"),
            ("apparent_power", "VA", "apparent_power", "measurement"),
            ("reactive_power", "var", "reactive_power", "measurement"),
            ("voltage", "V", "voltage", "measurement"), ("current", "A", "current", "measurement"),
            ("power_factor", None, "power_factor", "measurement"),
            ("frequency", "Hz", "frequency", "measurement"), ("number", None, None, "measurement"),
        ]:
            with self.subTest(result_type=result_type):
                description = self.entity(result_type=result_type).entity_description
                self.assertEqual((description.native_unit_of_measurement, description.device_class, description.state_class), (unit, device_class, state_class))

    def test_formula_device_identity_does_not_follow_edited_sources(self):
        descriptions = self.extra.build_entry_descriptions({"add_mode": "local", "ecomain_selected_slaves": [1]}, {})
        self.assertEqual(self.extra.extra_entity_device_index(descriptions, {**self.config, "sources": ["sub1_ch1_power_rt"]}), 0)

    async def test_setup_keeps_formula_with_currently_unselected_source(self):
        from custom_components.enecess.const import CONST_ADD_MODE, CONST_DEVICE_TYPE, CONST_DEVICE_ECOMAIN, CONST_ECOMAIN_SERIAL, CONST_ENTRY_COORDINATOR, CONST_EXTRA_ENTITIES, DOMAIN
        entry = SimpleNamespace(entry_id="offline", data={CONST_ADD_MODE: "local", CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN, CONST_ECOMAIN_SERIAL: "TEST_FORMULA_001"}, options={CONST_EXTRA_ENTITIES: [None, {**self.config, "sources": ["missing"], "variables": {"a": "missing"}, "expression": "a"}]})
        self.coordinator.specs = []
        hass = SimpleNamespace(data={DOMAIN: {entry.entry_id: {CONST_ENTRY_COORDINATOR: self.coordinator}}})
        entities = []
        await self.runtime.async_setup_entry(hass, entry, entities.extend)
        self.assertEqual(len(entities), 1)
        self.assertFalse(entities[0].available)
        self.assertIsNone(entities[0].native_value)

    def test_legacy_operations_keep_existing_arithmetic(self):
        for operation, expected in [("invert", -12), ("absolute", 12), ("sum", 15), ("average", 7.5)]:
            self.assertEqual(self.entity(operation=operation).native_value, expected)
