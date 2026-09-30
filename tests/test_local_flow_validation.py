"""Keep setup and options validation bounded and release temporary connections."""

import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from flow_test_support import load_flow


class ValidationClient:
    """Provide controlled register responses without a network transport."""

    def __init__(self, firmware=139, slaves=None, block=False):
        self.firmware = firmware
        self.slaves = [1, 0, 1] if slaves is None else slaves
        self.block = block
        self.started = asyncio.Event()
        self.closed = False

    async def read_holding_registers(self, address, count):
        self.started.set()
        if self.block:
            await asyncio.Event().wait()
        result = [self.firmware] if address == 3009 else self.slaves
        if isinstance(result, Exception):
            raise result
        return SimpleNamespace(registers=result)

    async def async_close(self):
        self.closed = True


class LocalFlowValidationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    def options_flow(self):
        return self.module.EnecessOptionsFlow(
            SimpleNamespace(
                data={
                    "device_type": "ecomain",
                    "mode": "manual",
                    "ecomain_host": "192.0.2.10",
                    "ecomain_serial": "FICTIONAL-VALIDATION-001",
                    "ecomain_firmware_version": 136,
                },
                options={},
                entry_id="fictional-validation",
            )
        )

    async def test_options_firmware_probe_respects_validation_timeout(self):
        flow = self.options_flow()
        client = ValidationClient(block=True)
        with (
            patch.object(self.module, "EnecessModbusClient", return_value=client),
            patch.object(self.module, "CONF_ECOMAIN_FIRMWARE_READ_TIMEOUT", 0.001),
        ):
            try:
                result = await asyncio.wait_for(flow._async_refresh_local_slaves(), 0.1)
            except TimeoutError:
                self.fail("Options validation ignored the configured firmware deadline")
        self.assertEqual(result, {"base": "cannot_connect_local"})
        self.assertEqual(flow._firmware_version, 136)
        self.assertEqual(flow._available_slaves, [])
        self.assertTrue(client.closed)

    async def test_options_preserves_detected_firmware_when_slave_probe_fails(self):
        flow = self.options_flow()
        client = ValidationClient(slaves=ConnectionError())
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            result = await flow._async_refresh_local_slaves()
        self.assertEqual(result, {"base": "cannot_connect_local"})
        self.assertEqual(flow._firmware_version, 139)
        self.assertEqual(flow._available_slaves, [])
        self.assertTrue(client.closed)

    async def test_options_rejects_old_firmware_with_local_connection_error(self):
        flow = self.options_flow()
        client = ValidationClient(firmware=135)
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            result = await flow._async_refresh_local_slaves()
        self.assertEqual(result, {"base": "cannot_connect_local"})
        self.assertEqual(flow._firmware_version, 135)
        self.assertTrue(client.closed)

    async def test_options_closes_connection_when_validation_is_cancelled(self):
        flow = self.options_flow()
        client = ValidationClient(block=True)
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            task = asyncio.create_task(flow._async_refresh_local_slaves())
            await client.started.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertTrue(client.closed)

    async def test_options_exposes_only_online_slaves_after_success(self):
        flow = self.options_flow()
        client = ValidationClient()
        with patch.object(self.module, "EnecessModbusClient", return_value=client):
            result = await flow._async_refresh_local_slaves()
        self.assertIsNone(result)
        self.assertEqual(flow._firmware_version, 139)
        self.assertEqual(flow._available_slaves, ["1", "3"])
        self.assertTrue(client.closed)
