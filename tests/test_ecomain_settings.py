"""Exercise commissioning writes through the real client and a simulated wire peer."""

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path

from pymodbus.pdu import ExceptionResponse
from pymodbus.pdu.register_message import (
    ReadHoldingRegistersResponse,
    WriteMultipleRegistersResponse,
    WriteSingleRegisterResponse,
)


ROOT = Path(__file__).resolve().parents[1] / "custom_components/enecess"
DEFAULT_RESPONSE = object()


def load_runtime():
    package = types.ModuleType("settings_test_enecess")
    package.__path__ = [str(ROOT)]
    sys.modules[package.__name__] = package
    return importlib.import_module("settings_test_enecess.client_modbus")


class Transport:
    connected = True

    def __init__(self):
        self.values = dict.fromkeys(range(2000, 2140), 0)
        self.values.update(dict.fromkeys(range(2200, 2240), 0))
        self.values.update(dict.fromkeys(range(2043, 2083), 30))
        self.values.update({5000: 0, 5001: 0, 5002: 0})
        self.commands = []
        self.fail_reads = set()
        self.fail_writes = set()
        self.ignore_writes = set()
        self.multiple_response = DEFAULT_RESPONSE
        self.active = False
        self.overlap = False

    async def read_holding_registers(self, *, address, count, device_id):
        self.commands.append(("read", address, count, device_id))
        if address in self.fail_reads:
            raise OSError("simulated read failure")
        return ReadHoldingRegistersResponse(
            registers=[self.values[address + offset] for offset in range(count)]
        )

    async def write_register(self, *, address, value, device_id):
        self.commands.append(("write", address, value, device_id))
        self.overlap |= self.active
        self.active = True
        await asyncio.sleep(0)
        self.active = False
        if address in self.fail_writes:
            raise OSError("simulated write failure")
        if address not in self.ignore_writes:
            self.values[address] = value
        return WriteSingleRegisterResponse(address=address, registers=[value])

    async def write_registers(self, *, address, values, device_id):
        self.commands.append(("write_multiple", address, values, device_id))
        self.overlap |= self.active
        self.active = True
        await asyncio.sleep(0)
        self.active = False
        if address in self.fail_writes:
            raise OSError("simulated write failure")
        if address not in self.ignore_writes:
            self.values.update(enumerate(values, start=address))
        if self.multiple_response is not DEFAULT_RESPONSE:
            return self.multiple_response
        return WriteMultipleRegistersResponse(address=address, count=len(values))


class MultipleRegisterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modbus = load_runtime()
        self.transport = Transport()
        self.client = self.modbus.EnecessModbusClient("simulated", 502)
        self.client._client = self.transport

    async def test_function_16_accepts_real_response_and_preserves_word_order(self):
        self.assertTrue(callable(getattr(self.client, "write_registers", None)))
        await self.client.write_registers(5000, [0x5678, 0x1234])
        self.assertEqual(self.transport.values[5000], 0x5678)
        self.assertEqual(self.transport.values[5001], 0x1234)
        self.assertEqual(
            self.transport.commands,
            [("write_multiple", 5000, [0x5678, 0x1234], 255)],
        )

    async def test_function_16_rejects_missing_error_and_mismatched_echoes(self):
        self.assertTrue(callable(getattr(self.client, "write_registers", None)))
        for response in [
            None,
            ExceptionResponse(16, 4),
            ReadHoldingRegistersResponse(registers=[1, 2]),
            WriteMultipleRegistersResponse(address=5001, count=2),
            WriteMultipleRegistersResponse(address=5000, count=1),
        ]:
            with self.subTest(response=response):
                self.transport.multiple_response = response
                with self.assertRaises(self.modbus.ModbusException):
                    await self.client.write_registers(5000, [1, 2])
        self.assertEqual(len(self.transport.commands), 5)

    async def test_function_16_uses_the_existing_request_lock(self):
        self.assertTrue(callable(getattr(self.client, "write_registers", None)))
        await asyncio.gather(
            self.client.write_registers(5000, [1, 2]),
            self.client.write_register(5002, 3),
        )
        self.assertFalse(self.transport.overlap)


class SettingsTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modbus = load_runtime()
        self.assertIsNotNone(
            importlib.util.find_spec("settings_test_enecess.ecomain.settings"),
            "The channel and solar settings module must exist",
        )
        self.settings = importlib.import_module(
            "settings_test_enecess.ecomain.settings"
        )
        self.transport = Transport()
        self.client = self.modbus.EnecessModbusClient("simulated", 502)
        self.client._client = self.transport


class ChannelSettingsTests(SettingsTestCase):
    def channel_patch(self, *, phases=None, transformers=None):
        return self.settings.ChannelSettings(
            phases=phases or {},
            transformers=transformers or {},
        )

    async def test_reads_first_and_last_phase_and_transformer_for_each_meter(self):
        for device, phase_start, ct_start in [
            (0, 2000, 2043),
            (1, 2010, 2053),
            (2, 2020, 2063),
            (3, 2030, 2073),
        ]:
            with self.subTest(device=device):
                self.transport.commands.clear()
                self.transport.values[phase_start] = 0x8001
                self.transport.values[phase_start + 9] = 2
                self.transport.values[ct_start] = 100
                actual = await self.settings.async_read_channel_settings(
                    self.client, device
                )
                self.assertEqual(actual.phases["channel_1"], "L2")
                self.assertEqual(actual.phases["channel_10"], "L3")
                self.assertEqual(actual.transformers["channel_1"], "100")
                self.assertEqual(actual.transformers["channel_10"], "30")
                self.assertEqual(len(actual.phases), 10)
                self.assertEqual(len(actual.transformers), 10)
                self.assertEqual(
                    self.transport.commands,
                    [
                        ("read", phase_start, 10, 255),
                        ("read", ct_start, 10, 255),
                    ],
                )

    async def test_undefined_phase_and_transformer_remain_unselected(self):
        self.transport.values.update({2000: 3, 2043: 0, 2052: 31})
        actual = await self.settings.async_read_channel_settings(self.client, 0)
        self.assertIsNone(actual.phases["channel_1"])
        self.assertIsNone(actual.transformers["channel_1"])
        self.assertIsNone(actual.transformers["channel_10"])

    async def test_writes_first_and_last_channels_for_each_meter(self):
        for device, phase_start, ct_start in [
            (0, 2000, 2043),
            (1, 2010, 2053),
            (2, 2020, 2063),
            (3, 2030, 2073),
        ]:
            with self.subTest(device=device):
                errors = await self.settings.async_write_channel_settings(
                    self.client,
                    device,
                    self.channel_patch(
                        phases={"channel_1": "L2", "channel_10": "L3"},
                        transformers={"channel_1": "100", "channel_10": "100"},
                    ),
                )
                self.assertEqual(errors, {})
                self.assertEqual(self.transport.values[phase_start], 1)
                self.assertEqual(self.transport.values[phase_start + 9], 2)
                self.assertEqual(self.transport.values[ct_start], 100)
                self.assertEqual(self.transport.values[ct_start + 9], 100)

    async def test_branch_transformer_accepts_30(self):
        self.transport.values[2043] = 100
        errors = await self.settings.async_write_channel_settings(
            self.client,
            0,
            self.channel_patch(
                transformers={"channel_1": "30"},
            ),
        )
        self.assertEqual(errors, {})
        self.assertEqual(self.transport.values[2043], 30)

    async def test_empty_and_none_patches_do_no_io(self):
        for desired in [
            self.channel_patch(),
            self.channel_patch(
                phases={"channel_1": None},
                transformers={"channel_10": None},
            ),
        ]:
            self.assertEqual(
                await self.settings.async_write_channel_settings(
                    self.client, 0, desired
                ),
                {},
            )
        self.assertEqual(self.transport.commands, [])

    async def test_partial_patch_preserves_omitted_and_unselected_values(self):
        self.transport.values.update({2000: 3, 2043: 0})
        errors = await self.settings.async_write_channel_settings(
            self.client,
            0,
            self.channel_patch(
                phases={"channel_1": None},
                transformers={"channel_1": None, "channel_10": "100"},
            ),
        )
        self.assertEqual(errors, {})
        self.assertEqual(
            [self.transport.values[a] for a in [2000, 2043, 2052]], [3, 0, 100]
        )
        self.assertEqual(
            [command for command in self.transport.commands if command[0] == "write"],
            [("write", 2052, 100, 255)],
        )

    async def test_unchanged_values_are_not_written_and_reserved_phase_bits_are_preserved(
        self,
    ):
        self.transport.values[2000] = 0x8000
        errors = await self.settings.async_write_channel_settings(
            self.client,
            0,
            self.channel_patch(
                phases={"channel_1": "L1"},
                transformers={"channel_1": "30"},
            ),
        )
        self.assertEqual(errors, {})
        self.assertTrue(
            all(command[0] == "read" for command in self.transport.commands)
        )
        self.assertEqual(self.transport.values[2000], 0x8000)

    async def test_initial_read_failure_prevents_every_write(self):
        for address in [2000, 2043]:
            with self.subTest(address=address):
                self.transport.commands.clear()
                self.transport.fail_reads = {address}
                errors = await self.settings.async_write_channel_settings(
                    self.client,
                    0,
                    self.channel_patch(
                        phases={"channel_1": "L2"},
                        transformers={"channel_10": "100"},
                    ),
                )
                self.assertEqual(
                    errors,
                    {
                        "channel_1_phase": "write_failed",
                        "channel_10_transformer": "write_failed",
                    },
                )
                self.assertTrue(
                    all(command[0] == "read" for command in self.transport.commands)
                )

    async def test_partial_failures_report_fields_and_retry_skips_successes(self):
        self.transport.fail_writes.add(2000)
        self.transport.ignore_writes.add(2043)
        desired = self.channel_patch(
            phases={"channel_1": "L2", "channel_10": "L3"},
            transformers={"channel_1": "100", "channel_10": "100"},
        )
        self.assertEqual(
            await self.settings.async_write_channel_settings(self.client, 0, desired),
            {
                "channel_1_phase": "write_failed",
                "channel_1_transformer": "verify_failed",
            },
        )
        self.assertEqual(self.transport.values[2009], 2)
        self.assertEqual(self.transport.values[2052], 100)
        self.transport.fail_writes.clear()
        self.transport.ignore_writes.clear()
        self.transport.commands.clear()
        self.assertEqual(
            await self.settings.async_write_channel_settings(self.client, 0, desired),
            {},
        )
        self.assertEqual(
            [
                command[1]
                for command in self.transport.commands
                if command[0] == "write"
            ],
            [2000, 2043],
        )

    async def test_invalid_meter_and_choices_are_rejected_before_io(self):
        for device in [-1, 4, True, "0", 0.0]:
            with self.subTest(device=device):
                with self.assertRaises(ValueError):
                    await self.settings.async_read_channel_settings(self.client, device)
                with self.assertRaises(ValueError):
                    await self.settings.async_write_channel_settings(
                        self.client, device, self.channel_patch()
                    )
        for desired in [
            self.channel_patch(phases={"channel_11": None}),
            self.channel_patch(phases={"channel_1": "L4"}),
            self.channel_patch(transformers={"channel_0": "30"}),
            self.channel_patch(transformers={"channel_1": 30}),
            self.channel_patch(transformers={"channel_1": "31"}),
        ]:
            with self.subTest(desired=desired):
                with self.assertRaises(ValueError):
                    await self.settings.async_write_channel_settings(
                        self.client, 0, desired
                    )
        self.assertEqual(self.transport.commands, [])


class SolarSettingsTests(SettingsTestCase):
    def solar_patch(
        self, *, capacity=0, temperature_coefficient=0.0, inverter_channels=None
    ):
        return self.settings.SolarSettings(
            capacity=capacity,
            temperature_coefficient=temperature_coefficient,
            inverter_channels=inverter_channels or {},
        )

    async def test_reads_low_word_first_parameters_and_requested_inverter_groups(
        self,
    ):
        self.transport.values.update(
            {
                5000: 0x5678,
                5001: 0x1234,
                5002: 0xFE70,
                2200: 1,
                2209: 1,
                2210: 1,
                2219: 1,
                2220: 1,
                2229: 1,
                2230: 1,
                2239: 1,
            }
        )
        actual = await self.settings.async_read_solar_settings(self.client, [0, 1, 2, 3])
        self.assertEqual(actual.capacity, 0x12345678)
        self.assertEqual(actual.temperature_coefficient, -0.4)
        self.assertEqual(
            actual.inverter_channels,
            {0: ["1", "10"], 1: ["1", "10"], 2: ["1", "10"], 3: ["1", "10"]},
        )
        self.assertEqual(
            self.transport.commands,
            [
                ("read", 5000, 3, 255),
                ("read", 2200, 10, 255),
                ("read", 2210, 10, 255),
                ("read", 2220, 10, 255),
                ("read", 2230, 10, 255),
            ],
        )

    async def test_writes_capacity_in_one_low_word_first_request_and_negative_coefficient(
        self,
    ):
        errors = await self.settings.async_write_solar_settings(
            self.client,
            self.solar_patch(capacity=0x12345678, temperature_coefficient=-0.400),
        )
        self.assertEqual(errors, {})
        self.assertEqual(
            self.transport.commands,
            [
                ("read", 5000, 3, 255),
                ("write_multiple", 5000, [0x5678, 0x1234], 255),
                ("read", 5000, 2, 255),
                ("write", 5002, 0xFE70, 255),
                ("read", 5002, 1, 255),
            ],
        )

    async def test_capacity_and_coefficient_extremes_are_exact(self):
        for capacity, coefficient, words, raw in [
            (2147483647, 32.767, [0xFFFF, 0x7FFF], 0x7FFF),
            (2147483648, -0.4, [0, 0x8000], 0xFE70),
            (4294967295, 0, [0xFFFF, 0xFFFF], 0),
            (0, -32.768, [0, 0], 0x8000),
        ]:
            with self.subTest(capacity=capacity, coefficient=coefficient):
                self.assertEqual(
                    await self.settings.async_write_solar_settings(
                        self.client,
                        self.solar_patch(
                            capacity=capacity, temperature_coefficient=coefficient
                        ),
                    ),
                    {},
                )
                self.assertEqual(
                    [self.transport.values[5000], self.transport.values[5001]], words
                )
                self.assertEqual(self.transport.values[5002], raw)
                actual = await self.settings.async_read_solar_settings(self.client, [])
                self.assertEqual(actual.capacity, capacity)
                self.assertEqual(actual.temperature_coefficient, coefficient)

    async def test_reads_unsigned_capacity_across_signed_boundary(self):
        for words, expected in [
            ([0, 0], 0),
            ([0, 0x8000], 2147483648),
            ([0xFFFF, 0xFFFF], 4294967295),
        ]:
            with self.subTest(words=words):
                self.transport.values.update({5000: words[0], 5001: words[1]})
                actual = await self.settings.async_read_solar_settings(self.client, [])
                self.assertEqual(actual.capacity, expected)

    async def test_invalid_numeric_representations_are_rejected_before_io(self):
        for capacity in [-1, 4294967296, True, 1.5, float("nan"), float("inf"), "1"]:
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    await self.settings.async_write_solar_settings(
                        self.client, self.solar_patch(capacity=capacity)
                    )
        for coefficient in [
            -32.769,
            32.768,
            -0.4001,
            0.0001,
            float("nan"),
            float("inf"),
            float("-inf"),
            1 << 1024,
            True,
            "-0.4",
        ]:
            with self.subTest(coefficient=coefficient):
                with self.assertRaises(ValueError):
                    await self.settings.async_write_solar_settings(
                        self.client,
                        self.solar_patch(temperature_coefficient=coefficient),
                    )
        self.assertEqual(self.transport.commands, [])

    async def test_invalid_inverter_devices_and_channels_are_rejected_before_io(self):
        for device in [-1, 4, True, "0", 0.0]:
            with self.subTest(device=device):
                with self.assertRaises(ValueError):
                    await self.settings.async_read_solar_settings(
                        self.client, [0, device]
                    )
                with self.assertRaises(ValueError):
                    await self.settings.async_write_solar_settings(
                        self.client, self.solar_patch(inverter_channels={device: ["1"]})
                    )
        for channels in [["0"], ["11"], ["01"], [1], "1"]:
            with self.subTest(channels=channels):
                with self.assertRaises(ValueError):
                    await self.settings.async_write_solar_settings(
                        self.client, self.solar_patch(inverter_channels={0: channels})
                    )
        self.assertEqual(self.transport.commands, [])

    async def test_inverter_first_last_addresses_and_missing_groups_are_preserved(self):
        self.transport.values.update({2214: 1, 2225: 1})
        self.assertEqual(
            await self.settings.async_write_solar_settings(
                self.client,
                self.solar_patch(inverter_channels={0: ["1", "10"], 3: ["1", "10"]}),
            ),
            {},
        )
        self.assertEqual(
            [self.transport.values[a] for a in [2200, 2209, 2230, 2239]], [1, 1, 1, 1]
        )
        self.assertEqual([self.transport.values[a] for a in [2214, 2225]], [1, 1])
        self.assertFalse(
            any(2210 <= command[1] < 2230 for command in self.transport.commands)
        )

    async def test_explicit_empty_inverter_group_clears_only_that_group(self):
        self.transport.values.update({2200: 1, 2209: 1, 2210: 1})
        self.assertEqual(
            await self.settings.async_write_solar_settings(
                self.client, self.solar_patch(inverter_channels={0: []})
            ),
            {},
        )
        self.assertEqual(
            [self.transport.values[a] for a in [2200, 2209, 2210]], [0, 0, 1]
        )
        self.assertEqual(
            self.transport.commands,
            [
                ("read", 5000, 3, 255),
                ("read", 2200, 10, 255),
                ("write", 2200, 0, 255),
                ("read", 2200, 1, 255),
                ("write", 2209, 0, 255),
                ("read", 2209, 1, 255),
            ],
        )

    async def test_first_and_last_inverter_channels_for_every_meter(self):
        for device, first, last in [
            (0, 2200, 2209),
            (1, 2210, 2219),
            (2, 2220, 2229),
            (3, 2230, 2239),
        ]:
            with self.subTest(device=device):
                self.transport.commands.clear()
                errors = await self.settings.async_write_solar_settings(
                    self.client,
                    self.solar_patch(inverter_channels={device: ["1", "10"]}),
                )
                self.assertEqual(errors, {})
                self.assertEqual(
                    self.transport.commands,
                    [
                        ("read", 5000, 3, 255),
                        ("read", first, 10, 255),
                        ("write", first, 1, 255),
                        ("read", first, 1, 255),
                        ("write", last, 1, 255),
                        ("read", last, 1, 255),
                    ],
                )
                self.assertFalse(
                    any(2100 <= command[1] <= 2139 for command in self.transport.commands)
                )

    async def test_unchanged_parameters_and_flags_are_not_written(self):
        self.transport.values.update({5002: 0xFE70, 2209: 1})
        self.assertEqual(
            await self.settings.async_write_solar_settings(
                self.client,
                self.solar_patch(
                    temperature_coefficient=-0.4, inverter_channels={0: ["10"]}
                ),
            ),
            {},
        )
        self.assertEqual(
            self.transport.commands, [("read", 5000, 3, 255), ("read", 2200, 10, 255)]
        )

    async def test_initial_parameter_or_group_read_failure_prevents_every_write(self):
        for address in [5000, 2230]:
            with self.subTest(address=address):
                self.transport.commands.clear()
                self.transport.fail_reads = {address}
                self.assertEqual(
                    await self.settings.async_write_solar_settings(
                        self.client,
                        self.solar_patch(
                            capacity=1,
                            temperature_coefficient=-0.4,
                            inverter_channels={0: ["1"], 3: ["10"]},
                        ),
                    ),
                    {
                        "capacity": "write_failed",
                        "temperature_coefficient": "write_failed",
                        "inverter_channels_0": "write_failed",
                        "inverter_channels_3": "write_failed",
                    },
                )
                self.assertTrue(
                    all(command[0] == "read" for command in self.transport.commands)
                )

    async def test_partial_failures_retain_successes_and_retry_only_remaining_changes(
        self,
    ):
        self.transport.fail_writes.add(5000)
        self.transport.ignore_writes.add(2200)
        desired = self.solar_patch(
            capacity=0x12345678,
            temperature_coefficient=-0.4,
            inverter_channels={0: ["1", "10"]},
        )
        self.assertEqual(
            await self.settings.async_write_solar_settings(self.client, desired),
            {"capacity": "write_failed", "inverter_channels_0": "verify_failed"},
        )
        self.assertEqual(
            [self.transport.values[5002], self.transport.values[2209]], [0xFE70, 1]
        )
        self.transport.fail_writes.clear()
        self.transport.ignore_writes.clear()
        self.transport.commands.clear()
        self.assertEqual(
            await self.settings.async_write_solar_settings(self.client, desired), {}
        )
        self.assertEqual(
            [command for command in self.transport.commands if command[0] != "read"],
            [("write_multiple", 5000, [0x5678, 0x1234], 255), ("write", 2200, 1, 255)],
        )

    async def test_readback_failure_is_distinguished_from_write_failure(self):
        self.transport.fail_reads.add(5002)
        self.assertEqual(
            await self.settings.async_write_solar_settings(
                self.client, self.solar_patch(temperature_coefficient=-0.4)
            ),
            {"temperature_coefficient": "verify_failed"},
        )

    async def test_capacity_readback_mismatch_and_other_field_write_failures_are_reported(
        self,
    ):
        self.transport.ignore_writes.add(5000)
        self.transport.fail_writes.update({5002, 2209})
        self.assertEqual(
            await self.settings.async_write_solar_settings(
                self.client,
                self.solar_patch(
                    capacity=1,
                    temperature_coefficient=-0.4,
                    inverter_channels={0: ["10"]},
                ),
            ),
            {
                "capacity": "verify_failed",
                "temperature_coefficient": "write_failed",
                "inverter_channels_0": "write_failed",
            },
        )

    async def test_group_write_failure_takes_priority_over_another_flag_verify_failure(
        self,
    ):
        self.transport.fail_writes.add(2200)
        self.transport.ignore_writes.add(2209)
        self.assertEqual(
            await self.settings.async_write_solar_settings(
                self.client, self.solar_patch(inverter_channels={0: ["1", "10"]})
            ),
            {"inverter_channels_0": "write_failed"},
        )


if __name__ == "__main__":
    unittest.main()
