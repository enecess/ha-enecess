"""Stop in-flight cloud polls before persisting or removing entry energy."""

import asyncio
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntries

from custom_components import enecess
from custom_components.enecess.ecomain.coordinator import EcoMainCloudCoordinator
from custom_components.enecess.runtime import EnecessRuntimeData
from test_runtime import RealHARuntimeFixture


class CloudLifecycleTests(RealHARuntimeFixture):
    async def blocked_poll(self):
        entry = self.make_entry("cloud")
        api = AsyncMock()
        payload = {"household_electricity": {"power": 20, "energy": 5}}
        api.get_passageway.return_value = payload
        coordinator = EcoMainCloudCoordinator(self.hass, entry, api)
        self.addAsyncCleanup(coordinator.async_shutdown)
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = EnecessRuntimeData(coordinator)
        started = asyncio.Event()
        release = asyncio.Event()

        async def request(*args):
            started.set()
            await release.wait()
            return payload

        api.get_passageway.side_effect = request
        poll = asyncio.create_task(coordinator.async_refresh())
        await asyncio.wait_for(started.wait(), 1)
        return entry, coordinator, poll, release

    async def test_unload_cancels_poll_before_persisting_total(self):
        entry, coordinator, poll, release = await self.blocked_poll()
        try:
            with patch.object(
                ConfigEntries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ):
                self.assertTrue(await enecess.async_unload_entry(self.hass, entry))
        finally:
            release.set()
            await asyncio.gather(poll, return_exceptions=True)

        self.assertTrue(poll.cancelled())
        stored = await coordinator._energy._store.async_load()
        self.assertEqual(stored["main_all_energy_accumulated"], 5)
        self.assertIsNone(getattr(entry, "runtime_data", None))

    async def test_removed_entry_energy_is_not_recreated_by_old_poll(self):
        entry, coordinator, poll, release = await self.blocked_poll()
        try:
            with patch.object(
                ConfigEntries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ):
                await enecess.async_unload_entry(self.hass, entry)
            await enecess.async_remove_entry(self.hass, entry)
        finally:
            release.set()
            await asyncio.gather(poll, return_exceptions=True)

        # Run a pending HA storage checkpoint without waiting 60 seconds.
        await coordinator._energy._store._async_callback_delayed_write()
        self.assertIsNone(await coordinator._energy._store.async_load())

    async def test_shutdown_prevents_new_cloud_poll(self):
        entry = self.make_entry("cloud")
        api = AsyncMock()
        api.get_passageway.return_value = {"household_electricity": {"energy": 5}}
        coordinator = EcoMainCloudCoordinator(self.hass, entry, api)
        self.addAsyncCleanup(coordinator.async_shutdown)
        await coordinator.async_config_entry_first_refresh()
        await coordinator.async_shutdown()

        with self.assertRaises(asyncio.CancelledError):
            await coordinator._async_update_data()
        stored = await coordinator._energy._store.async_load()
        self.assertEqual(stored["main_all_energy_accumulated"], 5)
