"""Keep relay acknowledgments independent from account polling health."""

import asyncio
from contextlib import nullcontext
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.enecess.client_api import EnecessApiError, EnecessAuthError
from custom_components.enecess.const import CONST_ECOPLUG_DEVICES
from custom_components.enecess.ecoplug.coordinator import EcoPlugCloudCoordinator
from custom_components.enecess.ecoplug.model import EcoPlugConfig
from custom_components.enecess.ecoplug.sensor import EcoPlugSensor, SENSOR_DESCRIPTIONS
from custom_components.enecess.ecoplug.switch import EcoPlugSwitch
import test_runtime as runtime_fixture


SERIAL = "FICTIONAL-CONTROL-HEALTH-001"
OTHER_SERIAL = "FICTIONAL-CONTROL-HEALTH-002"
LOGGER = "custom_components.enecess.ecoplug.coordinator"


class ControlHealthTests(runtime_fixture.RealHARuntimeFixture):
    async def make_coordinator(self):
        entry = self.make_entry("plug")
        self.hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONST_ECOPLUG_DEVICES: [
                    {"hardware_number": SERIAL, "name": "Controlled fictional plug"},
                    {"hardware_number": OTHER_SERIAL, "name": "Other fictional plug"},
                ],
            },
        )
        api = AsyncMock()
        api.generate_token.return_value = "fictional-refreshed-token"
        api.get_plug_data.return_value = {
            "data": [
                {
                    "time": "2026-01-01T00:00:00Z",
                    "power": 42,
                    "total_energy": 12.5,
                }
            ]
        }
        api.get_plug_state.return_value = {
            "response": {"data": {"p": [{"id": 106, "val": 0}]}}
        }
        coordinator = EcoPlugCloudCoordinator(self.hass, entry, api)
        switches = {
            serial: EcoPlugSwitch(coordinator, EcoPlugConfig(serial, serial))
            for serial in (SERIAL, OTHER_SERIAL)
        }
        sensors = {
            serial: [
                EcoPlugSensor(coordinator, EcoPlugConfig(serial, serial), desc)
                for desc in SENSOR_DESCRIPTIONS
            ]
            for serial in (SERIAL, OTHER_SERIAL)
        }
        observed = []
        listener = Mock(
            side_effect=lambda: observed.append(
                (
                    coordinator.last_update_success,
                    switches[SERIAL].available,
                    switches[OTHER_SERIAL].available,
                    sensors[OTHER_SERIAL][0].available,
                )
            )
        )
        self.addCleanup(coordinator.async_add_listener(listener))
        self.addAsyncCleanup(coordinator.async_shutdown)
        await coordinator.async_refresh()
        return coordinator, api, switches, sensors, listener, observed

    async def fail_poll(self, coordinator, api):
        async def stalled_read(*args):
            await asyncio.Event().wait()

        previous = api.get_plug_data.side_effect
        api.get_plug_data.side_effect = stalled_read
        try:
            logs = (
                self.assertLogs(LOGGER, "ERROR")
                if coordinator.last_update_success
                else nullcontext()
            )
            with (
                patch(
                    "custom_components.enecess.ecoplug.coordinator.CONF_CLOUD_UPDATE_TIMEOUT",
                    0.01,
                ),
                logs,
            ):
                await coordinator.async_refresh()
        finally:
            api.get_plug_data.side_effect = previous

    async def hold_command(self, coordinator, api):
        started = asyncio.Event()
        release = asyncio.Event()

        async def control(*args):
            started.set()
            await release.wait()

        api.control_plug.side_effect = control
        task = asyncio.create_task(coordinator.async_control(SERIAL, True))

        async def finish_command():
            release.set()
            await asyncio.gather(task, return_exceptions=True)

        self.addAsyncCleanup(finish_command)
        await asyncio.wait_for(started.wait(), 1)
        return task, release

    async def start_stalled_poll(self, coordinator, api):
        started = asyncio.Event()

        async def read(*args):
            started.set()
            await asyncio.Event().wait()

        api.get_plug_data.side_effect = read
        task = asyncio.create_task(coordinator.async_refresh())

        async def finish_poll():
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        self.addAsyncCleanup(finish_poll)
        await asyncio.wait_for(started.wait(), 1)
        return task

    async def test_cancelled_live_poll_publishes_revoked_confirmation(self):
        coordinator, api, switches, _, _, observed = await self.make_coordinator()
        await coordinator.async_control(SERIAL, True)
        poll = await self.start_stalled_poll(coordinator, api)
        poll.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await poll
        self.assertFalse(coordinator.last_update_success)
        self.assertFalse(switches[SERIAL].available)
        self.assertEqual(observed[-1], (False, False, False, False))

    async def test_shutdown_cancellation_does_not_publish_to_listeners(self):
        coordinator, api, _, _, listener, _ = await self.make_coordinator()
        await coordinator.async_control(SERIAL, True)
        poll = await self.start_stalled_poll(coordinator, api)
        before = listener.call_count
        await coordinator.async_shutdown()
        poll.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await poll
        self.assertEqual(listener.call_count, before)

    async def test_repeated_commands_preserve_the_scheduled_measurement_poll(self):
        coordinator, api, switches, _, _, _ = await self.make_coordinator()
        timer = coordinator._unsub_refresh.__self__
        deadline = timer.when()
        clock = self.hass.loop.time()
        reads = api.get_plug_data.await_count
        for elapsed, value in ((10, True), (30, False), (50, True)):
            with patch.object(self.hass.loop, "time", return_value=clock + elapsed):
                await coordinator.async_control(SERIAL, value)
            self.assertFalse(timer.cancelled())
            self.assertEqual(coordinator._unsub_refresh.__self__.when(), deadline)
            self.assertEqual(switches[SERIAL].is_on, value)
        self.assertEqual(api.get_plug_data.await_count, reads)
        self.assertTrue(coordinator.last_update_success)

    async def test_late_ack_restores_only_its_relay_after_account_poll_failure(self):
        coordinator, api, switches, sensors, _, observed = await self.make_coordinator()
        task, release = await self.hold_command(coordinator, api)
        await self.fail_poll(coordinator, api)
        self.assertFalse(switches[SERIAL].available)
        exception = coordinator.last_exception
        reads = api.get_plug_data.await_count
        untouched = coordinator.data[OTHER_SERIAL]
        release.set()
        await task
        self.assertFalse(coordinator.last_update_success)
        self.assertIs(coordinator.last_exception, exception)
        self.assertTrue(switches[SERIAL].available)
        self.assertTrue(switches[SERIAL].is_on)
        self.assertFalse(switches[OTHER_SERIAL].available)
        self.assertTrue(
            all(not sensor.available for group in sensors.values() for sensor in group)
        )
        self.assertIs(coordinator.data[OTHER_SERIAL], untouched)
        self.assertEqual(api.get_plug_data.await_count, reads)
        self.assertEqual(observed[-1], (False, True, False, False))

    async def test_newer_ack_survives_overlapping_failure_but_expires_on_next_failure(
        self,
    ):
        (
            coordinator,
            api,
            switches,
            sensors,
            listener,
            observed,
        ) = await self.make_coordinator()
        poll_started = asyncio.Event()
        fail = asyncio.Event()

        async def failed_fetch(token):
            poll_started.set()
            await fail.wait()
            raise TimeoutError("fictional account timeout")

        with patch.object(coordinator, "_fetch_attempt", side_effect=failed_fetch):
            poll = asyncio.create_task(coordinator.async_refresh())
            await asyncio.wait_for(poll_started.wait(), 1)
            await coordinator.async_control(SERIAL, True)
            with self.assertLogs(LOGGER, "ERROR"):
                fail.set()
                await poll
        self.assertFalse(coordinator.last_update_success)
        self.assertTrue(switches[SERIAL].available)
        self.assertTrue(switches[SERIAL].is_on)
        self.assertFalse(sensors[SERIAL][0].available)
        before = listener.call_count
        await self.fail_poll(coordinator, api)
        self.assertFalse(switches[SERIAL].available)
        self.assertEqual(listener.call_count, before + 1)
        self.assertEqual(observed[-1], (False, False, False, False))
        await coordinator.async_refresh()
        self.assertTrue(coordinator.last_update_success)
        self.assertTrue(switches[SERIAL].available)
        self.assertFalse(switches[SERIAL].is_on)
        self.assertTrue(
            all(sensor.available for group in sensors.values() for sensor in group)
        )

    async def test_authoritative_equal_poll_keeps_notification_suppression(self):
        coordinator, api, switches, _, listener, _ = await self.make_coordinator()
        await coordinator.async_control(SERIAL, True)
        before = listener.call_count

        async def read_state(token, serial):
            return {
                "response": {"data": {"p": [{"id": 106, "val": int(serial == SERIAL)}]}}
            }

        api.get_plug_state.side_effect = read_state
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, before)
        await self.fail_poll(coordinator, api)
        self.assertFalse(switches[SERIAL].available)

    async def test_unexpected_and_auth_poll_failures_revoke_old_confirmation(self):
        coordinator, api, switches, _, _, _ = await self.make_coordinator()
        await self.fail_poll(coordinator, api)
        for error, expected in (
            (TypeError("fictional decoder bug"), TypeError),
            (EnecessAuthError("fictional expired token"), ConfigEntryAuthFailed),
        ):
            with self.subTest(error=type(error).__name__):
                await coordinator.async_control(SERIAL, True)
                logs = (
                    self.assertLogs(LOGGER, "WARNING")
                    if isinstance(error, EnecessAuthError)
                    else nullcontext()
                )
                with (
                    patch.object(coordinator, "_fetch_attempt", side_effect=error),
                    logs,
                ):
                    with self.assertRaises(expected):
                        await coordinator._async_update_data()
                self.assertFalse(switches[SERIAL].available)

    async def test_failed_or_cancelled_command_does_not_restore_unavailable_relay(self):
        coordinator, api, switches, sensors, _, _ = await self.make_coordinator()
        await self.fail_poll(coordinator, api)
        api.control_plug.side_effect = EnecessApiError("fictional rejected control")
        with self.assertRaises(EnecessApiError):
            await coordinator.async_control(SERIAL, True)
        self.assertFalse(switches[SERIAL].available)
        task, _ = await self.hold_command(coordinator, api)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(switches[SERIAL].available)
        self.assertFalse(coordinator.last_update_success)
        self.assertFalse(sensors[SERIAL][0].available)
