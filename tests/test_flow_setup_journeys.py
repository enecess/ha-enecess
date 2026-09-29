"""Exercise complete setup journeys through submitted forms with offline services."""

import types
import unittest
from unittest.mock import AsyncMock

from flow_test_support import load_flow, submit_values


class SetupJourneyTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.m = load_flow(self)
    def flow(self):
        f = self.m.ConfigFlow()
        f.context = {}
        f.async_set_unique_id = AsyncMock(return_value=None)
        return f

    async def submit(self, f, r, **values):
        values = submit_values(r, values)
        return await getattr(f, 'async_step_' + r['step_id'])(values)

    async def local(self, mode, slaves):
        f = self.flow()
        f._async_mdns_scan = AsyncMock(return_value=[self.m.DiscoveredDevice('TEST-AUDIT-01', 'audit.local', 'audit', '192.0.2.10')])
        async def validate(host, port):
            f._ecomain_local_config.update(ecomain_online_slaves=list(slaves), ecomain_firmware_version=139)
        f._async_validate_local_device = AsyncMock(side_effect=validate)
        if mode == 'zeroconf':
            discovery = self.m.DEVICE_CONFIGS['ecomain'].discovery
            r = await f.async_step_zeroconf(types.SimpleNamespace(type=discovery.mdns_type, name=f'{discovery.mdns_prefix}TEST-AUDIT-01.{discovery.mdns_type}', hostname='audit.local.', host='192.0.2.10'))
        else:
            r = await f.async_step_user()
            r = await self.submit(f, r, device_type='ecomain')
            r = await self.submit(f, r, mode=mode)
            if mode == 'manual':
                r = await self.submit(f, r, ecomain_serial='TEST-AUDIT-01', ecomain_host='192.0.2.10')
            else:
                r = await self.submit(f, r, ecomain_serial='TEST-AUDIT-01')
        r = await self.submit(f, r)
        if slaves:
            self.assertEqual('ecomain_local_setup', r['step_id'])
            r = await self.submit(f, r, ecomain_selected_slaves=list(slaves))
        self.assertEqual('measurement_types_local', r['step_id'])
        r = await self.submit(f, r, measurement_types=['power'])
        return f, r

    async def cloud(self, device='ecomain', fail=None):
        f = self.flow()
        records = [{'id': 1, 'hardware_number': 'TEST-CLOUD-01'}, {'id': 2, 'hardware_number': 'TEST-CLOUD-02'}]
        async def hardware(token, hardware_type, parent_id=None):
            if hardware_type in (0, 2):
                return records
            if fail:
                raise fail
            return [{'hardware_number': f'TEST-CLOUD-0{parent_id}_1'}]
        f._cloud_api = types.SimpleNamespace(generate_token=AsyncMock(return_value='fake-token'), get_hardware_list=AsyncMock(side_effect=hardware))
        r = await f.async_step_user()
        r = await self.submit(f, r, device_type=device)
        if device == 'ecomain':
            r = await self.submit(f, r, mode='cloud')
        r = await self.submit(f, r, username='user@example.invalid', password='fake-password')
        return f, r

    async def test_success_local_all_entry_paths(self):
        for mode in ('manual', 'auto', 'zeroconf'):
            for slaves in ([], ['1']):
                with self.subTest(mode=mode, slaves=slaves):
                    f, r = await self.local(mode, slaves)
                    r = await self.submit(f, r, extra_action='finish')
                    self.assertEqual('create_entry', r['type'])
                    self.assertEqual([1] if slaves else [], r['data']['ecomain_selected_slaves'])
                    self.assertEqual(['power'], r['options']['measurement_types'])

    async def test_success_cloud_and_master_change(self):
        f, r = await self.cloud()
        r = await self.submit(f, r, ecomain_cloud_master_id='1')
        r = await self.submit(f, r, ecomain_selected_slaves=['1'])
        self.assertEqual('measurement_types', r['step_id'])
        r = await self.submit(f, r, measurement_types=['power'])
        for unused in range(3):
            r = await self.submit(f, r, flow_action='back')
        self.assertEqual('ecomain_cloud_master', r['step_id'])
        r = await self.submit(f, r, ecomain_cloud_master_id='2')
        r = await self.submit(f, r, ecomain_selected_slaves=['1'])
        r = await self.submit(f, r, measurement_types=['power'])
        r = await self.submit(f, r, extra_action='finish')
        self.assertEqual('TEST-CLOUD-02', r['data']['ecomain_serial'])
        self.assertEqual({1: 'TEST-CLOUD-02_1'}, r['data']['ecomain_cloud_slave_map'])

    async def test_cloud_credentials_change_refreshes_devices_and_saved_credentials(self):
        f, r = await self.cloud()
        r = await self.submit(f, r, ecomain_cloud_master_id='1')
        r = await self.submit(f, r, ecomain_selected_slaves=['1'])
        r = await self.submit(f, r, measurement_types=['power'])
        for unused in range(4):
            r = await self.submit(f, r, flow_action='back')
        self.assertEqual('ecomain_cloud_login', r['step_id'])
        f._cloud_api.generate_token.return_value = 'replacement-token'
        f._cloud_api.get_hardware_list.side_effect = None
        f._cloud_api.get_hardware_list.return_value = [{'id': 3, 'hardware_number': 'TEST-CLOUD-03'}]
        r = await self.submit(f, r, username='replacement@example.invalid', password='replacement-password')
        self.assertIsNone(f._measurement_types)
        self.assertEqual('3', r['data_schema']({})['ecomain_cloud_master_id'])
        f._cloud_api.get_hardware_list.return_value = []
        r = await self.submit(f, r, ecomain_cloud_master_id='3')
        r = await self.submit(f, r)
        r = await self.submit(f, r, measurement_types=['power'])
        r = await self.submit(f, r, extra_action='finish')
        self.assertEqual('create_entry', r['type'])
        self.assertEqual('replacement@example.invalid', r['data']['username'])
        self.assertEqual('replacement-password', r['data']['password'])
        self.assertEqual('TEST-CLOUD-03', r['data']['ecomain_serial'])

    async def test_local_back_visits_actual_pages_without_repeating_network_work(self):
        for mode in ('manual', 'auto', 'zeroconf'):
            for slaves in ([], ['1']):
                with self.subTest(mode=mode, slaves=slaves):
                    f, r = await self.local(mode, slaves)
                    previous_pages = ['measurement_types_local']
                    if slaves:
                        previous_pages.append('ecomain_local_setup')
                    previous_pages.append('ecomain_local_confirm')
                    if mode != 'zeroconf':
                        previous_pages.extend(['ecomain_manual' if mode == 'manual' else 'ecomain_auto_scan', 'ecomain_mode', 'user'])
                    for expected in previous_pages:
                        r = await self.submit(f, r, flow_action='back')
                        self.assertEqual(expected, r['step_id'])
                    f._async_validate_local_device.assert_awaited_once()
                    self.assertEqual(1 if mode == 'auto' else 0, f._async_mdns_scan.await_count)

    async def test_ecoplug_credentials_change_then_finish(self):
        f, r = await self.cloud('ecoplug')
        r = await self.submit(f, r, flow_action='back', ecoplug_selected=['TEST-CLOUD-01'])
        r = await self.submit(f, r, username='other@example.invalid', password='other-password')
        self.assertNotIn('ecoplug_selected', r['data_schema']({}))
        r = await self.submit(f, r, ecoplug_selected=['TEST-CLOUD-02'])
        self.assertEqual('create_entry', r['type'])
        self.assertEqual('other@example.invalid', r['data']['username'])
        self.assertEqual(['TEST-CLOUD-02'], [d['hardware_number'] for d in r['data']['ecoplug_devices']])

    async def test_cloud_login_errors_allow_retry_back_and_cancel(self):
        for device in ('ecomain', 'ecoplug'):
            for error in ('auth_failed', 'cannot_connect', 'no_devices_found'):
                for action in ('retry', 'back', 'cancel'):
                    with self.subTest(device=device, error=error, action=action):
                        f = self.flow()
                        api = types.SimpleNamespace(
                            generate_token=AsyncMock(return_value='fake-token'),
                            get_hardware_list=AsyncMock(return_value=[]))
                        f._cloud_api = api
                        if error == 'auth_failed':
                            api.generate_token.side_effect = self.m.EnecessAuthError('offline auth failure')
                        elif error == 'cannot_connect':
                            api.generate_token.side_effect = OSError('offline network failure')
                        r = await f.async_step_user()
                        r = await self.submit(f, r, device_type=device)
                        if device == 'ecomain':
                            r = await self.submit(f, r, mode='cloud')
                        r = await self.submit(f, r, username='user@example.invalid', password='fake-password')
                        self.assertEqual('form', r['type'])
                        self.assertEqual(device + '_cloud_login', r['step_id'])
                        self.assertEqual(error, r['errors']['base'])
                        if action == 'retry':
                            api.generate_token.side_effect = None
                            api.get_hardware_list.return_value = [{'id': 1, 'hardware_number': 'TEST-CLOUD-01'}]
                            r = await self.submit(f, r, username='corrected@example.invalid', password='corrected-password')
                            self.assertEqual('ecomain_cloud_master' if device == 'ecomain' else 'ecoplug_select', r['step_id'])
                            self.assertEqual('corrected@example.invalid', f._cloud_username)
                        else:
                            before = api.generate_token.await_count
                            r = await self.submit(f, r, flow_action=action)
                            self.assertEqual(before, api.generate_token.await_count)
                            if action == 'back':
                                self.assertEqual('ecomain_mode' if device == 'ecomain' else 'user', r['step_id'])
                            else:
                                self.assertEqual('abort', r['type'])
                                self.assertEqual('user_cancelled', r['reason'])
                        f.async_set_unique_id.assert_not_awaited()

    async def test_cloud_master_errors_allow_retry_back_and_cancel(self):
        for exception in (self.m.EnecessAuthError('offline auth failure'), OSError('offline network failure')):
            for action in ('retry', 'back', 'cancel'):
                with self.subTest(exception=type(exception).__name__, action=action):
                    f, r = await self.cloud(fail=exception)
                    try:
                        r = await self.submit(f, r, ecomain_cloud_master_id='1')
                    except Exception as error:
                        self.fail(f'Cloud master error escaped instead of returning a form: {error!r}')
                    self.assertEqual('form', r['type'])
                    self.assertEqual('ecomain_cloud_master', r['step_id'])
                    expected = 'auth_failed' if isinstance(exception, self.m.EnecessAuthError) else 'cannot_connect'
                    self.assertEqual(expected, r['errors']['base'])
                    if action == 'retry':
                        f._cloud_api.get_hardware_list.side_effect = None
                        f._cloud_api.get_hardware_list.return_value = []
                        r = await self.submit(f, r, ecomain_cloud_master_id='1')
                        self.assertEqual('ecomain_cloud_confirm', r['step_id'])
                        r = await self.submit(f, r)
                        r = await self.submit(f, r, measurement_types=['power'])
                        r = await self.submit(f, r, extra_action='finish')
                        self.assertEqual('create_entry', r['type'])
                    else:
                        before = f._cloud_api.get_hardware_list.await_count
                        r = await self.submit(f, r, flow_action=action)
                        self.assertEqual(before, f._cloud_api.get_hardware_list.await_count)
                        if action == 'back':
                            self.assertEqual('ecomain_cloud_login', r['step_id'])
                        else:
                            self.assertEqual('abort', r['type'])
                            self.assertEqual('user_cancelled', r['reason'])
                        f.async_set_unique_id.assert_not_awaited()

    async def test_local_device_change_discards_completed_extra_and_drafts(self):
        f, r = await self.local('manual', ['1'])
        r = await self.submit(f, r, extra_action='add_formula')
        r = await self.submit(f, r, extra_entity_name='Audited', extra_formula_result_type='power')
        r = await self.submit(f, r, extra_formula_sources_power=['main_l1_power_rt'])
        r = await self.submit(f, r, extra_formula_expression='a')
        for unused in range(4):
            r = await self.submit(f, r, flow_action='back')
        r = await self.submit(f, r, ecomain_host='192.0.2.11', ecomain_serial='TEST-AUDIT-02')
        self.assertEqual([], f._extra_entities)
        self.assertIsNone(f._measurement_types)
        r = await self.submit(f, r)
        r = await self.submit(f, r, ecomain_selected_slaves=[])
        r = await self.submit(f, r, measurement_types=['voltage'])
        r = await self.submit(f, r, extra_action='finish')
        self.assertEqual('TEST-AUDIT-02', r['data']['ecomain_serial'])
        self.assertEqual('192.0.2.11', r['data']['ecomain_host'])
        self.assertEqual([], r['options']['extra_entities'])
        self.assertEqual(['voltage'], r['options']['measurement_types'])

    async def test_manual_validation_error_retry_and_navigation(self):
        f = self.flow()
        r = await f.async_step_user()
        r = await self.submit(f, r, device_type='ecomain')
        r = await self.submit(f, r, mode='manual')
        r = await self.submit(f, r, ecomain_serial='TEST-ERROR-01', ecomain_host='192.0.2.10')
        f._async_validate_local_device = AsyncMock(return_value={'base': 'cannot_connect'})
        r = await self.submit(f, r)
        self.assertEqual('cannot_connect', r['errors']['base'])
        r = await self.submit(f, r, flow_action='back')
        self.assertEqual('ecomain_local_confirm', r['step_id'])
        f._async_validate_local_device.assert_awaited_once()
        async def validate(host, port):
            f._ecomain_local_config.update(ecomain_online_slaves=[], ecomain_firmware_version=139)
        f._async_validate_local_device = AsyncMock(side_effect=validate)
        r = await self.submit(f, r)
        self.assertEqual('measurement_types_local', r['step_id'])
        r = await self.submit(f, r, measurement_types=['power'])
        r = await self.submit(f, r, extra_action='finish')
        self.assertEqual('create_entry', r['type'])

    async def test_scan_no_devices_retry(self):
        f = self.flow()
        f._async_mdns_scan = AsyncMock(side_effect=[[], [self.m.DiscoveredDevice('TEST-SCAN-01', 'audit.local', 'audit', '192.0.2.10')]])
        r = await f.async_step_user()
        r = await self.submit(f, r, device_type='ecomain')
        r = await self.submit(f, r, mode='auto')
        self.assertEqual('no_devices_found', r['errors']['base'])
        r = await self.submit(f, r)
        self.assertEqual('ecomain_auto_scan', r['step_id'])
        r = await self.submit(f, r, ecomain_serial='TEST-SCAN-01')
        self.assertEqual('ecomain_local_confirm', r['step_id'])

    async def test_changed_auto_mode_survives_empty_scan_then_retry_and_finish(self):
        f, r = await self.local('manual', [])
        for unused in range(4):
            r = await self.submit(f, r, flow_action='back')
        self.assertEqual('ecomain_mode', r['step_id'])
        f._async_mdns_scan = AsyncMock(side_effect=[[], [self.m.DiscoveredDevice(
            'TEST-RETRY-AUTO-01', 'retry.local', 'retry-service', '192.0.2.20')]])
        r = await self.submit(f, r, mode='auto')
        self.assertEqual('ecomain_auto_scan', r['step_id'])
        self.assertEqual('no_devices_found', r['errors']['base'])
        r = await self.submit(f, r)
        self.assertEqual('ecomain_auto_scan', r['step_id'])
        r = await self.submit(f, r, ecomain_serial='TEST-RETRY-AUTO-01')
        r = await self.submit(f, r)
        self.assertEqual('measurement_types_local', r['step_id'])
        r = await self.submit(f, r, measurement_types=['power'])
        r = await self.submit(f, r, extra_action='finish')
        self.assertEqual('create_entry', r['type'])
        self.assertEqual('auto', r['data']['mode'])
        self.assertEqual('TEST-RETRY-AUTO-01', r['data']['ecomain_serial'])
        self.assertEqual('192.0.2.20', r['data']['ecomain_host'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
