"""Real HA polling/control interleaving and ecoPlug numeric payload regressions."""

import asyncio
import unittest
from unittest.mock import AsyncMock

from custom_components.enecess.client_api import EnecessApiError
from custom_components.enecess.const import CONST_ECOPLUG_DEVICES
from custom_components.enecess.ecoplug.coordinator import EcoPlugCloudCoordinator
from custom_components.enecess.ecoplug.model import (
    EcoPlugSnapshot,
    parse_latest_plug_data,
)
import test_runtime as runtime_fixture


SERIAL = runtime_fixture.PLUG_SERIAL
OTHER_SERIAL = "FICTIONAL-COMPAT-PLUG-002"


class EcoPlugConcurrencyTests(runtime_fixture.RealHARuntimeFixture):
    def make_coordinator(self):
        entry = self.make_entry("plug")
        self.hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONST_ECOPLUG_DEVICES: [
                    runtime_fixture.PLUG,
                    {"hardware_number": OTHER_SERIAL, "name": "Other fictional plug"},
                ],
            },
        )
        api = AsyncMock()
        api.get_plug_data.return_value = {
            "data": [
                {"time": "2026-01-01T00:00:00Z", "power": 42, "total_energy": 12.5}
            ]
        }
        coordinator = EcoPlugCloudCoordinator(self.hass, entry, api)
        coordinator.async_set_updated_data(
            {
                SERIAL: EcoPlugSnapshot(power_rt=1, energy_total=1, is_on=False),
                OTHER_SERIAL: EcoPlugSnapshot(power_rt=1, energy_total=1, is_on=False),
            }
        )
        self.addAsyncCleanup(coordinator.async_shutdown)
        return coordinator, api

    async def start_poll(self, coordinator, api, *, state_error=False):
        started = asyncio.Event()
        release = asyncio.Event()

        async def state(_token, serial):
            started.set()
            await release.wait()
            if state_error and serial == SERIAL:
                raise EnecessApiError("Fictional stale state failure")
            return {
                "response": {
                    "data": {"p": [{"id": 106, "val": int(serial == OTHER_SERIAL)}]}
                }
            }

        api.get_plug_state.side_effect = state
        task = asyncio.create_task(coordinator.async_refresh())

        async def finish_poll():
            release.set()
            await asyncio.gather(task, return_exceptions=True)

        self.addAsyncCleanup(finish_poll)
        await asyncio.wait_for(started.wait(), 1)
        return task, release

    async def test_old_poll_preserves_command_and_updates_other_readings(self):
        coordinator, api = self.make_coordinator()
        task, release = await self.start_poll(coordinator, api)
        await asyncio.wait_for(coordinator.async_control(SERIAL, True), 1)
        self.assertTrue(coordinator.data[SERIAL].is_on)
        release.set()
        await task
        self.assertTrue(coordinator.data[SERIAL].is_on)
        self.assertIsNone(coordinator.data[SERIAL].state_error)
        self.assertEqual(coordinator.data[SERIAL].power_rt, 42)
        self.assertEqual(coordinator.data[SERIAL].energy_total, 12.5)
        self.assertTrue(coordinator.data[OTHER_SERIAL].is_on)
        # A subsequent poll is authoritative again, including an external change.
        await coordinator.async_refresh()
        self.assertFalse(coordinator.data[SERIAL].is_on)

    async def test_old_state_error_does_not_erase_successful_command(self):
        coordinator, api = self.make_coordinator()
        task, release = await self.start_poll(coordinator, api, state_error=True)
        await coordinator.async_control(SERIAL, True)
        with self.assertLogs(
            "custom_components.enecess.ecoplug.coordinator", level="ERROR"
        ):
            release.set()
            await task
        self.assertTrue(coordinator.data[SERIAL].is_on)
        self.assertIsNone(coordinator.data[SERIAL].state_error)

    async def test_failed_command_does_not_mask_poll(self):
        coordinator, api = self.make_coordinator()
        task, release = await self.start_poll(coordinator, api)
        api.control_plug.side_effect = EnecessApiError("Fictional failed control")
        with self.assertRaises(EnecessApiError):
            await coordinator.async_control(OTHER_SERIAL, False)
        release.set()
        await task
        self.assertTrue(coordinator.data[OTHER_SERIAL].is_on)

    async def test_cancelled_command_does_not_mask_poll(self):
        coordinator, api = self.make_coordinator()
        task, release = await self.start_poll(coordinator, api)
        started = asyncio.Event()

        async def control(*_args):
            started.set()
            await asyncio.Event().wait()

        api.control_plug.side_effect = control
        command = asyncio.create_task(coordinator.async_control(OTHER_SERIAL, False))
        await asyncio.wait_for(started.wait(), 1)
        command.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await command
        release.set()
        await task
        self.assertTrue(coordinator.data[OTHER_SERIAL].is_on)

    async def test_cancelled_poll_keeps_command_and_next_poll_recovers(self):
        coordinator, api = self.make_coordinator()
        task, release = await self.start_poll(coordinator, api)
        await coordinator.async_control(SERIAL, True)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        self.assertTrue(coordinator.data[SERIAL].is_on)
        release.set()
        await coordinator.async_refresh()
        self.assertFalse(coordinator.data[SERIAL].is_on)


class EcoPlugNumericPayloadTests(unittest.TestCase):
    def parse(self, power, energy):
        return parse_latest_plug_data(
            {
                "data": [
                    {
                        "time": "2026-01-01T00:00:00Z",
                        "power": power,
                        "total_energy": energy,
                    }
                ]
            }
        )

    def test_booleans_are_missing_without_discarding_other_fields(self):
        for value in (True, False):
            with self.subTest(value=value):
                self.assertEqual(self.parse(value, "12.5"), (None, 12.5))
                self.assertEqual(self.parse("42", value), (42.0, None))

    def test_numeric_zero_and_strings_remain_valid(self):
        self.assertEqual(self.parse(0, "0"), (0.0, 0.0))
        self.assertEqual(self.parse("42.5", 12.5), (42.5, 12.5))
