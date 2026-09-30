"""Close ecoPlug polling, authentication and queued controls with the entry."""

import asyncio
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntries

from custom_components import enecess
from custom_components.enecess.client_api import EnecessAuthError
from custom_components.enecess.const import CONST_CLOUD_TOKEN
from custom_components.enecess.ecoplug.coordinator import EcoPlugCloudCoordinator
from custom_components.enecess.runtime import EnecessRuntimeData
from test_runtime import PLUG_SERIAL, RealHARuntimeFixture


class EcoPlugLifecycleTests(RealHARuntimeFixture):
    async def make_coordinator(self):
        entry = self.make_entry("plug")
        api = AsyncMock()
        api.get_plug_data.return_value = {
            "data": [
                {"time": "2026-01-01T00:00:00Z", "power": 42, "total_energy": 12.5}
            ]
        }
        api.get_plug_state.return_value = {
            "response": {"data": {"p": [{"id": 106, "val": 0}]}}
        }
        coordinator = EcoPlugCloudCoordinator(self.hass, entry, api)
        self.addAsyncCleanup(coordinator.async_shutdown)
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = EnecessRuntimeData(coordinator)
        return entry, coordinator, api

    def track_task(self, coroutine):
        task = asyncio.create_task(coroutine)

        async def finish():
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        self.addAsyncCleanup(finish)
        return task

    async def test_unload_cancels_poll_before_it_can_refresh_authentication(self):
        entry, coordinator, api = await self.make_coordinator()
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def data(*args):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
            raise EnecessAuthError("Fictional expired token")

        api.get_plug_data.side_effect = data
        poll = self.track_task(coordinator.async_refresh())
        await asyncio.wait_for(started.wait(), 1)
        before = coordinator.data.copy()
        observed = []
        self.addCleanup(
            coordinator.async_add_listener(lambda: observed.append(coordinator.data))
        )
        with patch.object(
            ConfigEntries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ):
            self.assertTrue(await enecess.async_unload_entry(self.hass, entry))

        self.assertTrue(poll.cancelled())
        self.assertTrue(cancelled.is_set())
        self.assertIsNone(getattr(entry, "runtime_data", None))
        self.assertEqual(coordinator.data, before)
        self.assertEqual(observed, [])
        api.generate_token.assert_not_awaited()

    async def test_shutdown_cancels_token_refresh_without_writing_entry(self):
        entry, coordinator, api = await self.make_coordinator()
        original_token = entry.data[CONST_CLOUD_TOKEN]
        started = asyncio.Event()
        cancelled = asyncio.Event()
        api.get_plug_data.side_effect = EnecessAuthError("Fictional expired token")

        async def token(*args):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
            return "fictional-late-token"

        api.generate_token.side_effect = token
        poll = self.track_task(coordinator.async_refresh())
        await asyncio.wait_for(started.wait(), 1)
        await coordinator.async_shutdown()
        self.assertTrue(poll.cancelled())
        self.assertTrue(cancelled.is_set())
        self.assertEqual(entry.data[CONST_CLOUD_TOKEN], original_token)
        self.assertEqual(api.get_plug_data.await_count, 2)

    async def test_shutdown_cancels_in_flight_and_queued_controls_without_confirmation(
        self,
    ):
        _, coordinator, api = await self.make_coordinator()
        started = asyncio.Event()
        queued = asyncio.Event()
        cancelled = asyncio.Event()

        async def control(*args):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async def turn_off():
            queued.set()
            await coordinator.async_control(PLUG_SERIAL, False)

        api.control_plug.side_effect = control
        first = self.track_task(coordinator.async_control(PLUG_SERIAL, True))
        await asyncio.wait_for(started.wait(), 1)
        second = self.track_task(turn_off())
        await asyncio.wait_for(queued.wait(), 1)
        observed = []
        self.addCleanup(
            coordinator.async_add_listener(lambda: observed.append(coordinator.data))
        )
        before = coordinator.data.copy()
        await coordinator.async_shutdown()
        self.assertTrue(first.cancelled())
        self.assertTrue(second.cancelled())
        self.assertTrue(cancelled.is_set())
        api.control_plug.assert_awaited_once_with("fictional-token", PLUG_SERIAL, True)
        self.assertEqual(coordinator.data, before)
        self.assertFalse(coordinator.data[PLUG_SERIAL].state_confirmed)
        self.assertEqual(observed, [])

    async def test_shutdown_rejects_new_poll_without_network_requests(self):
        _, coordinator, api = await self.make_coordinator()
        await coordinator.async_shutdown()
        reads = api.get_plug_data.await_count
        states = api.get_plug_state.await_count
        with self.assertRaises(asyncio.CancelledError):
            await coordinator._async_update_data()
        self.assertEqual(api.get_plug_data.await_count, reads)
        self.assertEqual(api.get_plug_state.await_count, states)

    async def test_shutdown_rejects_new_control_without_network_requests(self):
        _, coordinator, api = await self.make_coordinator()
        await coordinator.async_shutdown()
        before = coordinator.data.copy()
        with self.assertRaises(asyncio.CancelledError):
            await coordinator.async_control(PLUG_SERIAL, True)
        api.control_plug.assert_not_awaited()
        self.assertEqual(coordinator.data, before)
