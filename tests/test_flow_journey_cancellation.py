"""Replay displayed setup pages and verify cancellation has no side effects."""

from copy import deepcopy
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from flow_test_support import load_flow
from test_ecomain_phase import Transport


class ClosingTransport(Transport):
    def close(self):
        self.commands.append(('close',))


class JourneyCancellationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    async def submit(self, flow, result, **values):
        self.assertEqual('form', result['type'], 'A terminal flow cannot accept another submission')
        return await getattr(flow, 'async_step_' + result['step_id'])(result['data_schema'](values))

    def make_flow(self):
        flow = self.module.ConfigFlow()
        flow.context = {}
        flow.async_create_entry = Mock(wraps=flow.async_create_entry)
        flow.hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(async_update_entry=Mock()))
        flow._async_mdns_scan = AsyncMock(return_value=[self.module.DiscoveredDevice(
            'TEST-JOURNEY-01', 'test.local', 'test-service', '192.0.2.10')])
        api = types.SimpleNamespace(generate_token=AsyncMock(return_value='fake-token'),
            get_hardware_list=AsyncMock(side_effect=lambda token, hardware_type, parent_id=None:
                [{'id': 1, 'hardware_number': 'TEST-JOURNEY-01'}] if hardware_type in (0, 2)
                else [{'hardware_number': 'TEST-JOURNEY-01_1'}]))
        flow._cloud_api = api
        transport = ClosingTransport()
        transport.values.update({3009: 139, 3101: 1, 3102: 0, 3103: 0})
        client = self.module.EnecessModbusClient('192.0.2.10', 502)
        client._client = transport
        return flow, api, transport, client

    async def start(self, flow, route):
        if route == 'zeroconf':
            discovery = self.module.DEVICE_CONFIGS['ecomain'].discovery
            return await flow.async_step_zeroconf(types.SimpleNamespace(
                type=discovery.mdns_type,
                name=f'{discovery.mdns_prefix}TEST-JOURNEY-01.{discovery.mdns_type}',
                hostname='test.local.', host='192.0.2.10'))
        return await flow.async_step_user()

    def inputs(self, route):
        return {
            'user': {'device_type': 'ecoplug' if route == 'ecoplug' else 'ecomain'},
            'ecomain_mode': {'mode': route},
            'ecomain_manual': {'ecomain_host': '192.0.2.10', 'ecomain_serial': 'TEST-JOURNEY-01'},
            'ecomain_auto_scan': {'ecomain_serial': 'TEST-JOURNEY-01'},
            'ecomain_local_confirm': {},
            'ecomain_local_setup': {'ecomain_selected_slaves': ['1']},
            'ecomain_cloud_login': {'username': 'test@example.invalid', 'password': 'fake-password'},
            'ecoplug_cloud_login': {'username': 'test@example.invalid', 'password': 'fake-password'},
            'ecomain_cloud_master': {'ecomain_cloud_master_id': '1'},
            'ecomain_cloud_confirm': {'ecomain_selected_slaves': ['1']},
            'measurement_types': {'measurement_types': ['power']},
        }

    async def test_cancel_at_every_setup_page_aborts_without_saving_or_more_io(self):
        routes = {
            'manual': ['ecomain_mode', 'ecomain_manual', 'ecomain_local_confirm',
                       'ecomain_local_setup', 'measurement_types', 'extra_entities'],
            'auto': ['ecomain_mode', 'ecomain_auto_scan', 'ecomain_local_confirm',
                     'ecomain_local_setup', 'measurement_types', 'extra_entities'],
            'zeroconf': ['ecomain_local_confirm', 'ecomain_local_setup', 'measurement_types', 'extra_entities'],
            'cloud': ['ecomain_mode', 'ecomain_cloud_login', 'ecomain_cloud_master',
                      'ecomain_cloud_confirm', 'measurement_types', 'extra_entities'],
            'ecoplug': ['ecoplug_cloud_login', 'ecoplug_select'],
        }
        for route, steps in routes.items():
            for target in steps:
                with self.subTest(route=route, target=target):
                    flow, api, transport, client = self.make_flow()
                    with patch.object(self.module, 'EnecessModbusClient', return_value=client):
                        result = await self.start(flow, route)
                        while result['step_id'] != target:
                            result = await self.submit(flow, result, **self.inputs(route)[result['step_id']])
                        calls = (list(transport.commands), list(api.generate_token.mock_calls),
                                 list(api.get_hardware_list.mock_calls))
                        result = await self.submit(flow, result, flow_action='cancel')
                    self.assertEqual({'type': 'abort', 'reason': 'user_cancelled'}, result)
                    self.assertEqual(calls, (transport.commands, api.generate_token.mock_calls,
                                             api.get_hardware_list.mock_calls))
                    flow.async_create_entry.assert_not_called()
                    flow.hass.config_entries.async_update_entry.assert_not_called()

    async def test_formula_source_replacement_never_reuses_removed_alias(self):
        for options in (False, True):
            with self.subTest(options=options):
                data = {'device_type': 'ecomain', 'mode': 'manual', 'ecomain_serial': 'TEST-JOURNEY-01',
                        'ecomain_firmware_version': 139}
                if options:
                    flow = self.module.EnecessOptionsFlow(types.SimpleNamespace(data=data, options={}, entry_id='test'))
                    flow._async_refresh_available_slaves = AsyncMock()
                    result = await flow.async_step_init()
                else:
                    flow, _, _, _ = self.make_flow()
                    flow._entry_data = data
                    result = await flow.async_step_extra_entities()
                result = await self.submit(flow, result, extra_action='add_formula')
                result = await self.submit(flow, result, extra_entity_name='Difference',
                    extra_formula_result_type='power', extra_entity_sources=['main_l1_power_rt', 'main_l2_power_rt'])
                result = await self.submit(flow, result, flow_action='back', extra_formula_expression='a-b')
                result = await self.submit(flow, result, extra_entity_sources=['main_l2_power_rt', 'main_l3_power_rt'])
                self.assertEqual({'b': 'main_l2_power_rt', 'c': 'main_l3_power_rt'}, flow._formula_draft['variables'])
                result = await self.submit(flow, result)
                self.assertEqual('formula_invalid', result['errors']['base'])
                self.assertEqual([], flow._extra_entities)
                result = await self.submit(flow, result, flow_action='back')
                result = await self.submit(flow, result, extra_entity_sources=['main_l1_power_rt', 'main_l2_power_rt'])
                self.assertEqual({'a': 'main_l1_power_rt', 'b': 'main_l2_power_rt'}, flow._formula_draft['variables'])
                result = await self.submit(flow, result)
                self.assertEqual('a-b', flow._extra_entities[0]['expression'])

    async def test_rejected_upstream_change_preserves_completed_entities(self):
        flow, _, _, client = self.make_flow()
        with patch.object(self.module, 'EnecessModbusClient', return_value=client):
            result = await self.start(flow, 'manual')
            while result['step_id'] != 'extra_entities':
                result = await self.submit(flow, result, **self.inputs('manual')[result['step_id']])
            result = await self.submit(flow, result, extra_action='add_formula')
            result = await self.submit(flow, result, extra_entity_name='Power',
                extra_formula_result_type='power', extra_entity_sources=['main_l1_power_rt'])
            result = await self.submit(flow, result, extra_formula_expression='a')
            original = deepcopy(flow._extra_entities)
            while result['step_id'] != 'ecomain_manual':
                result = await self.submit(flow, result, flow_action='back')
            result = await self.submit(flow, result, ecomain_host=' ')
            self.assertTrue(result['errors'])
            self.assertEqual(original, flow._extra_entities)
            self.assertEqual(['power'], flow._measurement_types)
