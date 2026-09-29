"""Exercise persisted measurement selections and phase UI without networking."""

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
                if "voltage" in choices:
                    result = await flow.async_step_measurement_types(
                        result["data_schema"]({"measurement_types": ["voltage"]}))
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

    async def test_firmware_136_hides_new_measurements_and_phase_action(self):
        entry = self.entry()
        entry.data["ecomain_firmware_version"] = 136
        flow = self.module.EnecessOptionsFlow(entry)
        result = await flow.async_step_measurement_types()
        choices = next(iter(result["data_schema"].schema.values())).config["options"]
        self.assertEqual(["power", "energy_forward", "energy_reverse"], choices)
        result = await flow._show_options_menu()
        actions = next(value.config["options"] for key, value in result["data_schema"].schema.items() if str(key) == "extra_action")
        self.assertNotIn("channel_phases", actions)

    async def test_phase_action_requires_firmware_139_or_later(self):
        for version in (None, 135, 136, 138, 139, 140):
            with self.subTest(version=version):
                entry = self.entry()
                entry.data["ecomain_firmware_version"] = version
                flow = self.module.EnecessOptionsFlow(entry)
                result = await flow._show_options_menu()
                actions = next(value.config["options"] for key, value in result["data_schema"].schema.items()
                               if str(key) == "extra_action")
                self.assertEqual(version is not None and version >= 139, "channel_phases" in actions)

    async def test_entry_specs_filter_unsupported_saved_selections(self):
        data = {**self.entry().data, "ecomain_firmware_version": 138}
        specs = self.module.build_entry_specs(data, {"measurement_types": ["power", "voltage"]})
        self.assertEqual({"power"}, {s.measurement_type for s in specs})
        data["ecomain_firmware_version"] = 139
        specs = self.module.build_entry_specs(data, {"measurement_types": ["power", "voltage"]})
        self.assertEqual({"power", "voltage"}, {s.measurement_type for s in specs})

    async def test_empty_cloud_selection_can_be_corrected(self):
        flow = self.module.ConfigFlow()
        flow._entry_data = self.entry('cloud').data
        result = await flow.async_step_measurement_types()
        choices = next(iter(result['data_schema'].schema.values())).config['options']
        self.assertNotIn('voltage', choices)
        result = await flow.async_step_measurement_types(result['data_schema']({'measurement_types': []}))
        self.assertEqual('no_measurements_selected', result['errors']['base'])
        result = await flow.async_step_measurement_types(result['data_schema']({'measurement_types': ['power']}))
        self.assertEqual('extra_entities', result['step_id'])

    async def test_options_retain_legacy_default_and_unknown_options(self):
        flow = self.module.EnecessOptionsFlow(self.entry(options={'future_option': 1}))
        self.assertEqual(['power', 'energy_forward', 'energy_reverse'], flow._options.get('measurement_types'))
        self.assertEqual(1, flow._options.get('future_option'))

    async def test_options_prevent_removing_derived_source(self):
        flow = self.module.EnecessOptionsFlow(self.entry(options={'extra_entities': [
            {'key': 'absolute', 'sources': ['main_l1_power_rt'], 'operation': 'absolute'}]}))
        result = await flow.async_step_measurement_types({'measurement_types': ['voltage']})
        self.assertEqual('measurement_in_use', result['errors']['base'])
        self.assertIn('power', flow._options['measurement_types'])

    async def test_options_dispatch_measurements_without_finishing(self):
        flow = self.module.EnecessOptionsFlow(self.entry())
        result = await flow.async_step_init({'extra_action': 'measurement_types'})
        self.assertEqual('measurement_types', result['step_id'])

    async def test_cloud_does_not_offer_phase_writes(self):
        flow = self.module.EnecessOptionsFlow(self.entry('cloud'))
        result = await flow._show_options_menu()
        actions = next(value.config['options'] for key, value in result['data_schema'].schema.items()
                       if str(key) == 'extra_action')
        self.assertNotIn('channel_phases', actions)

    async def test_phase_device_tracks_current_selection_and_online_slaves(self):
        flow = self.module.EnecessOptionsFlow(self.entry())
        flow._available_slaves = ["2", "3"]
        flow._options["ecomain_selected_slaves"] = [1, 2]
        result = await flow.async_step_phase_device()
        values = next(iter(result["data_schema"].schema.values())).config["options"]
        self.assertEqual(["0", "2"], values)

class FirmwareTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_firmware_read_is_connection_error_not_old_firmware(self):
        module = load_flow(self)
        for response in (ConnectionRefusedError(), TimeoutError(), types.SimpleNamespace(registers=[]), types.SimpleNamespace(registers=[None])):
            with self.subTest(response=response):
                read = AsyncMock(side_effect=response) if isinstance(response, Exception) else AsyncMock(return_value=response)
                client = types.SimpleNamespace(read_holding_registers=read, async_close=AsyncMock())
                result = await module.async_validate_local_device(
                    client, firmware_register=3009, minimum_firmware=136,
                    slave_register_start=3101, slave_register_count=3, allowed_slaves={'1', '2', '3'}, firmware_timeout=5)
                self.assertEqual(result.error, 'cannot_connect_local')
                self.assertIsNone(result.firmware_version)
                read.assert_awaited_once_with(3009, 1)
                client.async_close.assert_awaited_once()

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


class PhaseFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)
        from test_ecomain_phase import Transport
        self.transport = Transport()
        self.transport.values[3009] = 139
        client = self.module.EnecessModbusClient("unused", 502)
        client._client = self.transport
        entry = types.SimpleNamespace(data={"device_type": "ecomain", "mode": "manual", "ecomain_serial": "test"},
                                      options={}, entry_id="test")
        self.flow = self.module.EnecessOptionsFlow(entry)
        entry.runtime_data = types.SimpleNamespace(modbus_client=client)

    async def test_old_firmware_blocks_phase_read_and_save(self):
        for version in (135, 136, 138):
            with self.subTest(version=version, operation="read"):
                self.transport.values[3009] = version
                result = await self.flow.async_step_phase_device({"phase_device": "0"})
                self.assertEqual({"base": "phase_firmware_too_old"}, result["errors"])
                self.assertFalse(any(2000 <= command[1] <= 2039 for command in self.transport.commands))
        self.transport.values[3009] = 139
        await self.flow.async_step_channel_phases({})
        desired = {f"channel_{n}": "L2" for n in range(1, 11)}
        for version in (135, 136, 138):
            with self.subTest(version=version, operation="write"):
                self.transport.values[3009] = version
                self.transport.commands.clear()
                result = await self.flow.async_step_channel_phases(desired)
                self.assertEqual({"base": "phase_firmware_too_old"}, result["errors"])
                self.assertFalse(any(2000 <= command[1] <= 2039 for command in self.transport.commands))
                self.assertFalse(any(command[0] == "write" for command in self.transport.commands))

    async def test_firmware_139_or_later_allows_phase_read_and_write(self):
        for version in (139, 140):
            with self.subTest(version=version):
                self.transport.values[3009] = version
                self.transport.values[2000] = 0
                result = await self.flow.async_step_phase_device({"phase_device": "0"})
                self.assertEqual({}, result["errors"])
                values = result["data_schema"]({})
                values["channel_1"] = "L2"
                result = await self.flow.async_step_channel_phases(values)
                self.assertEqual("init", result["step_id"])
                self.assertEqual(1, self.transport.values[2000])

    async def test_read_defaults_and_partial_write_retry(self):
        result = await self.flow.async_step_phase_device({"phase_device": "0"})
        desired = result["data_schema"]({})
        self.assertEqual({f"channel_{n}": "L1" for n in range(1, 11)},
                         {key: value for key, value in desired.items() if key.startswith("channel_")})
        self.assertFalse(any(command[0] == "write" for command in self.transport.commands))
        desired.update(channel_1="L2", channel_2="L3")
        self.transport.fail_writes.add(2001)
        result = await self.flow.async_step_channel_phases(desired)
        self.assertEqual({"channel_2": "phase_write_failed"}, result["errors"])
        self.assertEqual(1, self.transport.values[2000])
        self.transport.fail_writes.clear()
        result = await self.flow.async_step_channel_phases(desired)
        self.assertEqual("init", result["step_id"])
        self.assertEqual(2, self.transport.values[2001])
        self.assertEqual(1, sum(command[0] == "write" and command[1] == 2000 for command in self.transport.commands))

    async def test_failed_read_retry_only_reads(self):
        self.transport.fail_reads.add(2000)
        result = await self.flow.async_step_phase_device({"phase_device": "0"})
        self.assertEqual({"base": "phase_read_failed"}, result["errors"])
        self.assertFalse(any(str(key).startswith("channel_") for key in result["data_schema"].schema))
        self.assertIn("flow_action", [str(key) for key in result["data_schema"].schema])
        self.transport.fail_reads.clear()
        result = await self.flow.async_step_channel_phases({})
        self.assertEqual({}, result["errors"])
        self.assertEqual("L1", result["data_schema"]({})["channel_1"])
        self.assertFalse(any(command[0] == "write" for command in self.transport.commands))

    async def test_unknown_hardware_phase_can_be_corrected(self):
        self.transport.values[2000] = 3
        result = await self.flow.async_step_phase_device({"phase_device": "0"})
        self.assertEqual({}, result["errors"])
        values = result["data_schema"]({"channel_1": "L3"})
        result = await self.flow.async_step_channel_phases(values)
        self.assertEqual("init", result["step_id"])
        self.assertEqual(2, self.transport.values[2000])


class BrandMigrationTests(unittest.TestCase):
    def setUp(self):
        load_flow(self)
        import importlib
        self.registry = importlib.import_module("custom_components.enecess.registry")

    def test_default_entry_titles_updated_but_custom_titles_preserved(self):
        data = {"device_type": "ecomain", "mode": "manual", "ecomain_serial": "123"}
        self.assertEqual("ecoMain 123 (Local)", self.registry.normalize_entry_title(data, "EcoMain 123 (Local)"))
        self.assertEqual("My EcoMain", self.registry.normalize_entry_title(data, "My EcoMain"))
        data = {"device_type": "ecoplug", "username": "test@example.invalid"}
        self.assertEqual("ecoPlug (test@example.invalid)", self.registry.normalize_entry_title(data, "EcoPlug (test@example.invalid)"))
