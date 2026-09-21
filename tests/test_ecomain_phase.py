"""Exercise phase operations through the real client with an in-memory wire peer."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "custom_components/enecess"


def load_runtime():
    package = types.ModuleType("phase_test_enecess")
    package.__path__ = [str(ROOT)]
    sys.modules[package.__name__] = package
    return (
        importlib.import_module("phase_test_enecess.client_modbus"),
        importlib.import_module("phase_test_enecess.ecomain.phase"),
    )


class Response:
    def __init__(self, *, registers=None, address=None, error=False):
        self.registers = registers
        self.address = address
        self.error = error

    def isError(self):
        return self.error


class Transport:
    connected = True

    def __init__(self):
        self.values = {address: 0 for address in range(2000, 2040)}
        self.commands = []
        self.fail_writes = set()
        self.ignore_writes = set()
        self.fail_reads = set()
        self.short_read = False
        self.write_response = None

    async def read_holding_registers(self, *, address, count, device_id):
        self.commands.append(("read", address, count, device_id))
        if address in self.fail_reads:
            raise OSError("read failed")
        values = [self.values[address + offset] for offset in range(count)]
        return Response(registers=values[:-1] if self.short_read else values)

    async def write_register(self, *, address, value, device_id):
        self.commands.append(("write", address, value, device_id))
        if address in self.fail_writes:
            return Response(error=True)
        if address not in self.ignore_writes:
            self.values[address] = value
        return self.write_response or Response(address=address, registers=[value])


class PhaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modbus, self.phase = load_runtime()
        self.transport = Transport()
        self.client = self.modbus.EnecessModbusClient("unused", 502)
        self.client._client = self.transport

    async def test_reads_all_ten_channels_for_each_device_and_masks_reserved_bits(self):
        for device, start in [(0, 2000), (1, 2010), (2, 2020), (3, 2030)]:
            self.transport.values[start] = 0x8001
            self.transport.values[start + 9] = 2
            result = await self.phase.async_read_phases(self.client, device)
            self.assertEqual(result, {
                "channel_1": "L2", "channel_2": "L1", "channel_3": "L1",
                "channel_4": "L1", "channel_5": "L1", "channel_6": "L1",
                "channel_7": "L1", "channel_8": "L1", "channel_9": "L1",
                "channel_10": "L3",
            })
            self.assertEqual(self.transport.commands[-1], ("read", start, 10, 255))

    async def test_unknown_phase_is_explicitly_invalid(self):
        self.transport.values[2004] = 3
        phases = await self.phase.async_read_phases(self.client, 0)
        self.assertIsNone(phases["channel_5"])
        self.assertEqual(phases["channel_1"], "L1")

    async def test_writes_only_changed_channels_and_verifies_each(self):
        self.transport.values[2030] = 0x8000
        errors = await self.phase.async_write_phases(
            self.client, 3, {"channel_1": "L1", "channel_2": "L2", "channel_10": "L3"}
        )
        self.assertEqual(errors, {})
        self.assertEqual(self.transport.commands, [
            ("read", 2030, 10, 255), ("write", 2031, 1, 255),
            ("read", 2031, 1, 255), ("write", 2039, 2, 255),
            ("read", 2039, 1, 255),
        ])

    async def test_corrects_invalid_current_phase(self):
        self.transport.values[2000] = 3
        self.assertEqual(await self.phase.async_write_phases(self.client, 0, {"channel_1": "L1"}), {})
        self.assertEqual(self.transport.values[2000], 0)

    async def test_partial_failure_preserves_success_and_distinguishes_verification(self):
        self.transport.fail_writes.add(2010)
        self.transport.ignore_writes.add(2011)
        errors = await self.phase.async_write_phases(
            self.client, 1, {"channel_1": "L2", "channel_2": "L3", "channel_3": "L2"}
        )
        self.assertEqual(errors, {"channel_1": "phase_write_failed", "channel_2": "phase_verify_failed"})
        self.assertEqual(self.transport.values[2012], 1)

    async def test_initial_read_failure_never_writes(self):
        self.transport.fail_reads.add(2000)
        self.assertEqual(await self.phase.async_write_phases(self.client, 0, {"channel_1": "L2"}), {"channel_1": "phase_write_failed"})
        self.assertEqual(self.transport.commands, [("read", 2000, 10, 255)])

    async def test_short_reads_are_rejected(self):
        self.transport.short_read = True
        with self.assertRaises(self.modbus.ModbusException):
            await self.phase.async_read_phases(self.client, 0)

    async def test_invalid_inputs_fail_before_any_io(self):
        for device in [-1, 4, True, "0", 0.0]:
            with self.assertRaises(ValueError):
                await self.phase.async_read_phases(self.client, device)
            with self.assertRaises(ValueError):
                await self.phase.async_write_phases(self.client, device, {"channel_1": "L1"})
        for desired in [{"channel_0": "L1"}, {"channel_11": "L1"}, {"channel_01": "L1"}, {"channel_1": "L4"}, {"channel_1": 0}, {"channel_1": "L2", "invalid": "L1"}]:
            with self.assertRaises(ValueError):
                await self.phase.async_write_phases(self.client, 0, desired)
        self.assertEqual(self.transport.commands, [])

    async def test_malformed_write_echo_is_rejected(self):
        for response in [Response(address=2001, registers=[1]), Response(address=2000, registers=[2]), Response(address=2000), Response(error=True)]:
            self.transport.write_response = response
            with self.assertRaises(self.modbus.ModbusException):
                await self.client.write_register(2000, 1)

    async def test_legacy_slave_keyword_compatibility(self):
        calls = []

        async def legacy_write(*, address, value, slave):
            calls.append((address, value, slave))
            response = Response(address=address)
            del response.registers
            response.value = value
            return response

        with patch.object(self.transport, "write_register", legacy_write):
            await self.client.write_register(2039, 2)
        self.assertEqual(calls, [(2039, 2, 255)])

    async def test_readback_transport_failure_is_verification_failure(self):
        self.transport.fail_reads.add(2001)
        errors = await self.phase.async_write_phases(self.client, 0, {"channel_2": "L2"})
        self.assertEqual(errors, {"channel_2": "phase_verify_failed"})

    async def test_real_pymodbus_write_response_is_accepted(self):
        from pymodbus.pdu.register_message import WriteSingleRegisterResponse

        self.transport.write_response = WriteSingleRegisterResponse(address=2000, registers=[1])
        await self.client.write_register(2000, 1)


if __name__ == "__main__":
    unittest.main()
