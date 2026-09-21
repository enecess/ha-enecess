"""Offline configuration regression tests."""

import types
import unittest
from unittest.mock import AsyncMock, patch
from flow_test_support import load_flow

class MeasurementFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    def entry(self, mode='manual', options=None):
        return types.SimpleNamespace(data={'device_type': 'ecomain', 'mode': mode,
                                          'ecomain_serial': 'test', 'ecomain_selected_slaves': [1], 'ecomain_firmware_version': 139},
                                     options=options or {}, entry_id='test')

    async def test_local_setup_routes_through_measurements(self):
        flow = self.module.ConfigFlow()
        flow._mode = 'manual'
        flow._ecomain_local_config = {'ecomain_host': 'example.invalid',
                                     'ecomain_serial': 'test', 'ecomain_online_slaves': []}
        result = await flow.async_step_ecomain_local_setup({})
        self.assertEqual('measurement_types', result['step_id'])

    async def test_new_flow_defaults_and_persists_selection(self):
        flow = self.module.ConfigFlow()
        flow._entry_data = self.entry().data
        self.assertTrue(hasattr(flow, 'async_step_measurement_types'))
        result = await flow.async_step_measurement_types()
        self.assertEqual(['power', 'energy_forward', 'energy_reverse'],
                         result['data_schema']({})['measurement_types'])
        result = await flow.async_step_measurement_types({'measurement_types': ['voltage', 'frequency']})
        self.assertEqual('extra_entities', result['step_id'])
        self.assertEqual(['voltage', 'frequency'], flow._options_data()['measurement_types'])

    async def test_measurement_choices_follow_detected_firmware(self):
        for version in (None, 136, 138, 139, 140):
            with self.subTest(version=version):
                flow = self.module.ConfigFlow()
                flow._entry_data = {**self.entry().data, "ecomain_firmware_version": version}
                result = await flow.async_step_measurement_types()
                choices = next(iter(result["data_schema"].schema.values())).config["options"]
                self.assertEqual(version is not None and version >= 139, "voltage" in choices)
                self.assertTrue({"power", "energy_forward", "energy_reverse"}.issubset(choices))
                result = await flow.async_step_measurement_types({"measurement_types": ["voltage"]})
                if version is None or version < 139:
                    self.assertEqual("invalid_measurements", result["errors"]["base"])
                else:
                    self.assertEqual("extra_entities", result["step_id"])

    async def test_local_detection_carries_firmware_into_creation(self):
        for version in (136, 139):
            flow = self.module.ConfigFlow()
            flow._mode = "manual"
            flow._ecomain_local_config = {"ecomain_host": "offline", "ecomain_serial": "test"}
            client = types.SimpleNamespace(read_holding_registers=AsyncMock(side_effect=[
                types.SimpleNamespace(registers=[version]), types.SimpleNamespace(registers=[0, 0, 0])]),
                async_close=AsyncMock())
            with patch.object(self.module, "EnecessModbusClient", return_value=client):
                result = await flow.async_step_ecomain_local_setup()
            self.assertEqual("measurement_types", result["step_id"])
            choices = next(iter(result["data_schema"].schema.values())).config["options"]
            self.assertEqual(version == 139, "voltage" in choices)
            self.assertEqual(version, flow._entry_data["ecomain_firmware_version"])

    async def test_options_refresh_uses_actual_not_saved_firmware(self):
        entry = self.entry()
        entry.data["ecomain_host"] = "offline"
        entry.data["ecomain_firmware_version"] = 136
        flow = self.module.EnecessOptionsFlow(entry)
        client = types.SimpleNamespace(read_holding_registers=AsyncMock(side_effect=[
            types.SimpleNamespace(registers=[139]), types.SimpleNamespace(registers=[0, 0, 0])]),
            async_close=AsyncMock())
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            self.assertIsNone(await flow._async_refresh_local_slaves())
        result = await flow.async_step_measurement_types()
        choices = next(iter(result["data_schema"].schema.values())).config["options"]
        self.assertIn("voltage", choices)

    async def test_failed_firmware_refresh_does_not_remove_existing_entities(self):
        entry = self.entry(options={"measurement_types": ["power", "voltage"]})
        flow = self.module.EnecessOptionsFlow(entry)
        flow._firmware_version = None
        removed = []
        registry = types.SimpleNamespace(async_get_entity_id=lambda *args: args[-1], async_remove=removed.append)
        flow.hass = object()
        with patch.object(self.module.er, "async_get", return_value=registry, create=True):
            flow._async_remove_stale_sensor_entries()
        self.assertEqual([], removed)

    async def test_options_on_old_firmware_hide_new_types_and_phase_action(self):
        entry = self.entry()
        entry.data["ecomain_firmware_version"] = 136
        flow = self.module.EnecessOptionsFlow(entry)
        result = await flow.async_step_measurement_types()
        choices = next(iter(result["data_schema"].schema.values())).config["options"]
        self.assertEqual(["power", "energy_forward", "energy_reverse"], choices)
        result = await flow._show_options_menu()
        actions = next(value.config["options"] for key, value in result["data_schema"].schema.items() if str(key) == "extra_action")
        self.assertNotIn("channel_phases", actions)

    async def test_entry_specs_filter_unsupported_saved_selections(self):
        data = {**self.entry().data, "ecomain_firmware_version": 138}
        specs = self.module.build_entry_specs(data, {"measurement_types": ["power", "voltage"]})
        self.assertEqual({"power"}, {s.measurement_type for s in specs})
        data["ecomain_firmware_version"] = 139
        specs = self.module.build_entry_specs(data, {"measurement_types": ["power", "voltage"]})
        self.assertEqual({"power", "voltage"}, {s.measurement_type for s in specs})

    async def test_empty_and_cloud_unsupported_selection_rejected(self):
        flow = self.module.ConfigFlow()
        flow._entry_data = self.entry('cloud').data
        self.assertTrue(hasattr(flow, 'async_step_measurement_types'))
        result = await flow.async_step_measurement_types({'measurement_types': []})
        self.assertEqual('no_measurements_selected', result['errors']['base'])
        result = await flow.async_step_measurement_types({'measurement_types': ['voltage']})
        self.assertEqual('invalid_measurements', result['errors']['base'])

    async def test_options_retain_legacy_default_and_unknown_options(self):
        flow = self.module.EnecessOptionsFlow(self.entry(options={'future_option': 1}))
        self.assertEqual(['power', 'energy_forward', 'energy_reverse'], flow._options.get('measurement_types'))
        self.assertEqual(1, flow._options.get('future_option'))

    async def test_options_prevent_removing_derived_source(self):
        flow = self.module.EnecessOptionsFlow(self.entry(options={'extra_entities': [
            {'key': 'absolute', 'sources': ['main_l1_power_rt'], 'operation': 'absolute'}]}))
        self.assertTrue(hasattr(flow, 'async_step_measurement_types'))
        result = await flow.async_step_measurement_types({'measurement_types': ['voltage']})
        self.assertEqual('measurement_in_use', result['errors']['base'])
        self.assertIn('power', flow._options['measurement_types'])

    async def test_options_dispatch_measurements_without_finishing(self):
        flow = self.module.EnecessOptionsFlow(self.entry())
        result = await flow.async_step_init({'extra_action': 'measurement_types'})
        self.assertEqual('measurement_types', result['step_id'])





class FirmwareTests(unittest.IsolatedAsyncioTestCase):
    async def test_firmware_boundary_and_closed_connections(self):
        module = load_flow(self)
        for version, expected in ((135, 'firmware_too_old'), (136, None), (138, None), (139, None), (140, None)):
            with self.subTest(version=version):
                client = types.SimpleNamespace(
                    read_holding_registers=AsyncMock(side_effect=[types.SimpleNamespace(registers=[version]),
                                                                 types.SimpleNamespace(registers=[1, 0, 0])]),
                    async_close=AsyncMock())
                result = await module.async_validate_local_device(
                    client, firmware_register=3009, minimum_firmware=module.CONF_ECOMAIN_MIN_FIRMWARE_VERSION,
                    slave_register_start=3101, slave_register_count=3, allowed_slaves={'1', '2', '3'}, firmware_timeout=5)
                self.assertEqual(expected, result.error)
                if expected is None:
                    self.assertEqual(version, result.firmware_version)
                client.async_close.assert_awaited_once()


class BrandMigrationTests(unittest.TestCase):
    def setUp(self):
        load_flow(self)
        import importlib
        self.registry = importlib.import_module("custom_components.enecess.registry")

    def test_default_entry_titles_updated_but_custom_titles_preserved(self):
        self.assertTrue(hasattr(self.registry, "normalize_entry_title"))
        data = {"device_type": "ecomain", "mode": "manual", "ecomain_serial": "123"}
        self.assertEqual("ecoMain 123 (Local)", self.registry.normalize_entry_title(data, "EcoMain 123 (Local)"))
        self.assertEqual("My EcoMain", self.registry.normalize_entry_title(data, "My EcoMain"))
        data = {"device_type": "ecoplug", "username": "test@example.invalid"}
        self.assertEqual("ecoPlug (test@example.invalid)", self.registry.normalize_entry_title(data, "EcoPlug (test@example.invalid)"))


class RuntimeFirmwareReloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_verified_firmware_change_reloads_without_options_change(self):
        load_flow(self)
        import importlib.util
        import sys
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "custom_components/enecess/__init__.py"
        spec = importlib.util.spec_from_file_location("custom_components.enecess", path)
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        class Coordinator:
            def __init__(self, **kwargs):
                self.firmware_version = 139
            async def async_config_entry_first_refresh(self):
                pass
        fake_module = types.ModuleType("custom_components.enecess.ecomain.coordinator")
        fake_module.EcoMainModbusCoordinator = Coordinator
        entry = types.SimpleNamespace(data={"device_type": "ecomain", "mode": "manual", "ecomain_host": "offline",
                                            "ecomain_serial": "test", "ecomain_firmware_version": 136},
                                      options={"measurement_types": ["power", "voltage"]}, title="ecoMain test (Local)", entry_id="test")
        listeners = []
        entry.add_update_listener = lambda listener: listeners.append(listener)
        entry.async_on_unload = lambda callback: None
        def update(target, **kwargs):
            for key, value in kwargs.items():
                setattr(target, key, value)
        manager = types.SimpleNamespace(async_update_entry=update, async_reload=AsyncMock(), async_forward_entry_setups=AsyncMock())
        hass = types.SimpleNamespace(data={}, config_entries=manager)
        with patch.dict(sys.modules, {fake_module.__name__: fake_module}), patch.object(runtime, "_async_remove_unconfigured_registry_entries"):
            await runtime.async_setup_entry(hass, entry)
        self.assertEqual(139, entry.data["ecomain_firmware_version"])
        await listeners[0](hass, entry)
        manager.async_reload.assert_not_awaited()
        entry.data = {**entry.data, "ecomain_firmware_version": 138}
        await listeners[0](hass, entry)
        manager.async_reload.assert_awaited_once_with("test")
