"""Exercise bounded recovery with fictional HTTP responses and a loopback peer."""

import asyncio
from collections import deque
from contextlib import asynccontextmanager
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp
from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus import ModbusException

from custom_components.enecess.client_api import (
    EnecessApi,
    EnecessApiError,
    EnecessAuthError,
)
from custom_components.enecess.client_modbus import EnecessModbusClient
from custom_components.enecess.ecomain.coordinator import (
    EcoMainModbusCoordinator,
    EcoMainCloudCoordinator,
)
from custom_components.enecess.ecoplug.coordinator import EcoPlugCloudCoordinator
from test_runtime import RealHARuntimeFixture, PLUG_SERIAL

_GET_PLUG_DATA = EnecessApi.get_plug_data
_GET_PLUG_STATE = EnecessApi.get_plug_state


class HttpPeer:
    """Return queued transport outcomes without connecting to a cloud service."""

    def __init__(self, *outcomes):
        self.outcomes = deque(outcomes)
        self.calls = []
        self.active = 0

    @asynccontextmanager
    async def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        outcome = self.outcomes.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        self.active += 1
        try:
            status, payload = outcome
            yield SimpleNamespace(status=status, json=AsyncMock(return_value=payload))
        finally:
            self.active -= 1

    post = get


OK = (200, {"status": 200, "data": {"fictional": 42}})


class CloudRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        context = patch(
            "custom_components.enecess.client_api.CONF_CLOUD_RETRY_DELAY",
            0,
            create=True,
        )
        context.start()
        self.addCleanup(context.stop)

    async def test_read_endpoints_recover_after_one_transient_failure(self):
        for method in ("get_passageway", "get_plug_data", "get_plug_state"):
            for failure in (
                TimeoutError(),
                aiohttp.ServerDisconnectedError(),
                (502, {}),
                (503, {}),
                (504, {}),
            ):
                with self.subTest(method=method, failure=failure):
                    peer = HttpPeer(failure, OK)
                    result = await getattr(
                        EnecessApi(peer, "https://example.invalid"), method
                    )("fictional-token", "FICTIONAL-001")
                    self.assertEqual(result, {"fictional": 42})
                    self.assertEqual(len(peer.calls), 2)
                    self.assertEqual(peer.active, 0)

    async def test_exhaustion_stops_after_two_attempts_and_next_read_recovers(self):
        peer = HttpPeer(TimeoutError(), TimeoutError(), OK)
        api = EnecessApi(peer, "https://example.invalid")
        with self.assertRaises(EnecessApiError):
            await api.get_plug_state("fictional", "FICTIONAL-001")
        self.assertEqual(len(peer.calls), 2)
        self.assertEqual(
            await api.get_plug_state("fictional", "FICTIONAL-001"), {"fictional": 42}
        )

    async def test_permanent_and_malformed_errors_are_not_retried(self):
        for failure, error in (
            ((401, {}), EnecessAuthError),
            ((403, {}), EnecessAuthError),
            ((400, {}), EnecessApiError),
            ((429, {}), EnecessApiError),
            ((200, {"status": 401}), EnecessAuthError),
            ((200, {"status": 200, "data": "invalid"}), EnecessApiError),
            ((200, []), EnecessApiError),
            (aiohttp.InvalidURL("fictional"), EnecessApiError),
        ):
            with self.subTest(failure=failure):
                peer = HttpPeer(failure, OK)
                with self.assertRaises(error):
                    await EnecessApi(peer, "https://example.invalid").get_plug_data(
                        "fictional", "FICTIONAL-001"
                    )
                self.assertEqual(len(peer.calls), 1)

    async def test_control_and_login_are_not_retried_on_timeout(self):
        for method, args in (
            ("control_plug", ("fictional", "FICTIONAL-001", True)),
            ("generate_token", ("fictional", "fictional")),
        ):
            peer = HttpPeer(TimeoutError(), OK)
            with self.assertRaises(EnecessApiError):
                await getattr(EnecessApi(peer, "https://example.invalid"), method)(
                    *args
                )
            self.assertEqual(len(peer.calls), 1)

    async def test_retry_wait_releases_response_and_is_cancellable(self):
        peer = HttpPeer((503, {}), OK)

        async def cancel_wait(delay):
            self.assertEqual(peer.active, 0)
            raise asyncio.CancelledError

        with patch("asyncio.sleep", side_effect=cancel_wait):
            with self.assertRaises(asyncio.CancelledError):
                await EnecessApi(peer, "https://example.invalid").get_plug_state(
                    "fictional", "FICTIONAL-001"
                )
        self.assertEqual(len(peer.calls), 1)

    async def test_device_listing_read_can_recover(self):
        peer = HttpPeer(
            TimeoutError(),
            (200, {"status": 200, "data": [{"hardware_number": "FICTIONAL-001"}]}),
        )
        result = await EnecessApi(peer, "https://example.invalid").get_hardware_list(
            "fictional", 1
        )
        self.assertEqual(result, [{"hardware_number": "FICTIONAL-001"}])
        self.assertEqual(len(peer.calls), 2)


class ModbusRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        self.writers = []
        self.tasks = set()
        self.drop = 0
        self.received = asyncio.Event()
        self.server = await asyncio.start_server(self.handle, "127.0.0.1", 0)
        self.client = EnecessModbusClient(
            "127.0.0.1", self.server.sockets[0].getsockname()[1]
        )

    async def handle(self, reader, writer):
        self.tasks.add(asyncio.current_task())
        self.writers.append(writer)
        try:
            while True:
                header = await reader.readexactly(7)
                tid, protocol, length, unit = struct.unpack(">HHHB", header)
                pdu = await reader.readexactly(length - 1)
                self.requests.append(pdu)
                self.received.set()
                if self.drop:
                    self.drop -= 1
                    continue
                if pdu[0] == 3:
                    count = struct.unpack(">H", pdu[3:5])[0]
                    response = bytes([3, count * 2]) + struct.pack(">H", 139) * count
                else:
                    response = pdu
                writer.write(
                    struct.pack(">HHHB", tid, protocol, len(response) + 1, unit)
                    + response
                )
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            self.tasks.discard(asyncio.current_task())

    async def asyncTearDown(self):
        await self.client.async_close()
        for writer in self.writers:
            writer.close()
        self.server.close()
        await self.server.wait_closed()
        await asyncio.gather(*list(self.tasks))

    async def test_lost_reply_is_retried_once_after_two_seconds(self):
        self.drop = 1
        started = asyncio.get_running_loop().time()
        result = await self.client.read_holding_registers(3009, 1)
        elapsed = asyncio.get_running_loop().time() - started
        self.assertEqual(result.registers, [139])
        self.assertEqual(len(self.requests), 2)
        self.assertGreaterEqual(elapsed, 2)
        self.assertLess(elapsed, 3)

    async def test_unresponsive_peer_stops_after_two_requests_then_recovers(self):
        self.drop = 99
        with (
            self.assertLogs("pymodbus", level="ERROR"),
            self.assertRaises(ModbusException),
        ):
            await self.client.read_holding_registers(3009, 1)
        self.assertEqual(len(self.requests), 2)
        self.drop = 0
        self.assertEqual(
            (await self.client.read_holding_registers(3009, 1)).registers, [139]
        )

    async def test_disconnected_client_is_reused(self):
        await self.client.async_connect()
        original = self.client._client
        original.close()
        self.assertEqual(
            (await self.client.read_holding_registers(3009, 1)).registers, [139]
        )
        self.assertIs(self.client._client, original)

    async def test_cancelled_read_closes_transport_and_propagates_cancellation(self):
        self.drop = 99
        task = asyncio.create_task(self.client.read_holding_registers(3009, 1))
        await self.received.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertIsNone(self.client._client)
        self.assertEqual(len(self.requests), 1)

    async def test_phase_write_resends_same_absolute_value_at_most_once(self):
        self.drop = 1
        await self.client.write_register(2000, 1)
        self.assertEqual(self.requests, [bytes.fromhex("0607d00001")] * 2)

    async def test_cancelled_write_is_not_retried(self):
        self.drop = 99
        task = asyncio.create_task(self.client.write_register(2000, 1))
        await self.received.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertIsNone(self.client._client)
        self.assertEqual(len(self.requests), 1)

    async def test_disconnect_reconnects_in_background_using_same_client(self):
        await self.client.async_connect()
        original = self.client._client
        started = asyncio.get_running_loop().time()
        self.writers[0].close()
        async with asyncio.timeout(3):
            while len(self.writers) < 2 or not original.connected:
                await asyncio.sleep(0.01)
        self.assertGreaterEqual(asyncio.get_running_loop().time() - started, 1)
        self.assertIs(self.client._client, original)
        self.assertEqual(
            (await self.client.read_holding_registers(3009, 1)).registers, [139]
        )


class CoordinatorRecoveryTests(RealHARuntimeFixture):
    async def test_plug_retries_only_failed_state_and_reports_exhaustion(self):
        data = HttpPeer(
            *[
                (
                    200,
                    {
                        "status": 200,
                        "data": {
                            "data": [
                                {
                                    "time": "2026-01-01T00:00:00Z",
                                    "power": 42,
                                    "total_energy": 12.5,
                                }
                            ]
                        },
                    },
                )
            ]
            * 3
        )
        state_ok = (
            200,
            {
                "status": 200,
                "data": {"response": {"data": {"p": [{"id": 106, "val": 1}]}}},
            },
        )
        state = HttpPeer(
            TimeoutError(), state_ok, TimeoutError(), TimeoutError(), state_ok
        )
        api = EnecessApi(
            SimpleNamespace(get=data.get, post=state.post), "https://example.invalid"
        )
        coordinator = EcoPlugCloudCoordinator(self.hass, self.make_entry("plug"), api)
        with (
            patch.object(EnecessApi, "get_plug_data", _GET_PLUG_DATA),
            patch.object(EnecessApi, "get_plug_state", _GET_PLUG_STATE),
            patch("custom_components.enecess.client_api.CONF_CLOUD_RETRY_DELAY", 0),
        ):
            recovered = (await coordinator._async_update_data())[PLUG_SERIAL]
            self.assertTrue(recovered.is_on)
            self.assertIsNone(recovered.state_error)
            self.assertEqual(recovered.power_rt, 42)
            self.assertEqual((len(data.calls), len(state.calls)), (1, 2))
            with self.assertLogs(
                "custom_components.enecess.ecoplug.coordinator", level="ERROR"
            ):
                failed = (await coordinator._async_update_data())[PLUG_SERIAL]
            self.assertIsNone(failed.is_on)
            self.assertIsNotNone(failed.state_error)
            self.assertEqual(failed.power_rt, 42)
            recovered = (await coordinator._async_update_data())[PLUG_SERIAL]
            self.assertTrue(recovered.is_on)
            self.assertIsNone(recovered.state_error)
            self.assertEqual((len(data.calls), len(state.calls)), (3, 5))

    async def test_main_failed_request_does_not_leave_other_reads_running(self):
        api = AsyncMock()
        pending_finished = asyncio.Event()

        async def read(token, serial):
            if serial == "FICTIONAL-SUB-001":
                try:
                    await asyncio.sleep(0.03)
                    return {}
                finally:
                    pending_finished.set()
            raise EnecessApiError("fictional outage")

        api.get_passageway.side_effect = read
        entry = self.make_entry("main")
        self.hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "ecomain_cloud_slave_map": {1: "FICTIONAL-SUB-001"}},
        )
        coordinator = EcoMainCloudCoordinator(self.hass, entry, api)
        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()
        self.assertTrue(pending_finished.is_set())

    async def test_local_poll_has_total_deadline_and_recovers(self):
        client = AsyncMock()

        async def slow_read(address, count):
            await asyncio.sleep(0.03)
            return SimpleNamespace(registers=[139] * count)

        client.read_holding_registers.side_effect = slow_read
        coordinator = EcoMainModbusCoordinator(
            self.hass, self.make_entry("local"), client, []
        )
        # Firmware plus one read block must share the same time budget.
        coordinator._requested_specs = [
            SimpleNamespace(
                address=10,
                regs=1,
                measurement_type=None,
                kind="power",
                key="fictional",
                signed=False,
                scale=1,
            )
        ]
        with patch(
            "custom_components.enecess.ecomain.coordinator.CONF_LOCAL_UPDATE_TIMEOUT",
            0.05,
            create=True,
        ):
            with self.assertRaises(UpdateFailed):
                await coordinator._async_update_data()
        client.read_holding_registers.side_effect = None
        client.read_holding_registers.return_value = SimpleNamespace(registers=[42])
        self.assertEqual(await coordinator._async_update_data(), {"fictional": 42})

    async def test_cloud_poll_deadline_cancels_pending_requests(self):
        for cls, module in (
            (EcoMainCloudCoordinator, "ecomain"),
            (EcoPlugCloudCoordinator, "ecoplug"),
        ):
            cancelled = asyncio.Event()

            async def slow(*args):
                try:
                    await asyncio.sleep(0.2)
                    return {}
                except asyncio.CancelledError:
                    cancelled.set()
                    raise

            api = AsyncMock()
            api.get_passageway.side_effect = slow
            api.get_plug_data.side_effect = slow
            api.get_plug_state.side_effect = slow
            coordinator = cls(self.hass, self.make_entry("plug"), api)
            with patch(
                f"custom_components.enecess.{module}.coordinator.CONF_CLOUD_UPDATE_TIMEOUT",
                0.01,
                create=True,
            ):
                with self.assertRaises(UpdateFailed):
                    await coordinator._async_update_data()
            self.assertTrue(cancelled.is_set())
