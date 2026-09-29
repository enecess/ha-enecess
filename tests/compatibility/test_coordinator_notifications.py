"""Real HA notification behavior for unchanged local and ecoPlug snapshots."""

from unittest.mock import AsyncMock, Mock

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.enecess.client_api import EnecessApiError
from custom_components.enecess.ecomain.coordinator import EcoMainModbusCoordinator
from custom_components.enecess.ecoplug.coordinator import EcoPlugCloudCoordinator
import test_runtime as runtime_fixture


class CoordinatorNotificationTests(runtime_fixture.RealHARuntimeFixture):
    def listen(self, coordinator):
        listener = Mock()
        self.addCleanup(coordinator.async_add_listener(listener))
        self.addAsyncCleanup(coordinator.async_shutdown)
        return listener

    def local_coordinator(self, updates):
        coordinator = EcoMainModbusCoordinator(
            self.hass, self.make_entry("local"), AsyncMock(), []
        )
        coordinator._async_read_data = AsyncMock(side_effect=updates)
        return coordinator

    def plug_coordinator(self):
        api = AsyncMock()
        api.get_plug_data.return_value = {
            "data": [
                {"time": "2026-01-01T00:00:00Z", "power": 42, "total_energy": 12.5}
            ]
        }
        api.get_plug_state.return_value = {
            "response": {"data": {"p": [{"id": 106, "val": 0}]}}
        }
        coordinator = EcoPlugCloudCoordinator(self.hass, self.make_entry("plug"), api)
        return coordinator, api

    async def test_local_equal_readings_are_suppressed_but_changes_notify(self):
        coordinator = self.local_coordinator(
            [{"main_l1_power_rt": value} for value in (42.0, 42.0, 43.0)]
        )
        listener = self.listen(coordinator)
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 1)
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 1)
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 2)
        self.assertEqual(coordinator.data["main_l1_power_rt"], 43.0)

    async def test_local_failure_and_equal_recovery_notify_availability(self):
        coordinator = self.local_coordinator(
            [
                {"main_l1_power_rt": 42.0},
                UpdateFailed("Fictional read failure"),
                {"main_l1_power_rt": 42.0},
            ]
        )
        listener = self.listen(coordinator)
        await coordinator.async_refresh()
        with self.assertLogs("custom_components.enecess.ecomain.coordinator", "ERROR"):
            await coordinator.async_refresh()
        self.assertFalse(coordinator.last_update_success)
        self.assertEqual(listener.call_count, 2)
        await coordinator.async_refresh()
        self.assertTrue(coordinator.last_update_success)
        self.assertEqual(listener.call_count, 3)

    async def test_plug_equal_snapshots_are_suppressed_but_changes_notify(self):
        coordinator, api = self.plug_coordinator()
        listener = self.listen(coordinator)
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 1)
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 1)
        api.get_plug_data.return_value["data"][0]["power"] = 43
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 2)
        self.assertEqual(coordinator.data[runtime_fixture.PLUG_SERIAL].power_rt, 43)

    async def test_plug_partial_failure_and_recovery_notify_without_duplicates(self):
        coordinator, api = self.plug_coordinator()
        listener = self.listen(coordinator)
        await coordinator.async_refresh()
        api.get_plug_state.side_effect = EnecessApiError("Fictional state failure")
        with self.assertLogs("custom_components.enecess.ecoplug.coordinator", "ERROR"):
            await coordinator.async_refresh()
        snapshot = coordinator.data[runtime_fixture.PLUG_SERIAL]
        self.assertEqual(snapshot.power_rt, 42)
        self.assertIsNotNone(snapshot.state_error)
        self.assertEqual(listener.call_count, 2)
        await coordinator.async_refresh()
        self.assertEqual(listener.call_count, 2)
        api.get_plug_state.side_effect = None
        await coordinator.async_refresh()
        self.assertIsNone(coordinator.data[runtime_fixture.PLUG_SERIAL].state_error)
        self.assertFalse(coordinator.data[runtime_fixture.PLUG_SERIAL].is_on)
        self.assertEqual(listener.call_count, 3)

    async def test_successful_plug_command_notifies_immediately(self):
        coordinator, api = self.plug_coordinator()
        listener = self.listen(coordinator)
        await coordinator.async_refresh()
        await coordinator.async_control(runtime_fixture.PLUG_SERIAL, True)
        self.assertEqual(listener.call_count, 2)
        self.assertTrue(coordinator.data[runtime_fixture.PLUG_SERIAL].is_on)
        self.assertIsNone(coordinator.data[runtime_fixture.PLUG_SERIAL].state_error)
        api.control_plug.assert_awaited_once()
        # Publishing the command must not require another cloud poll.
        self.assertEqual(api.get_plug_state.await_count, 1)
