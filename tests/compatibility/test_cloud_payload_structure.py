"""Keep valid cloud measurements when individual nested records are malformed."""

from unittest.mock import AsyncMock

from custom_components.enecess.ecomain.coordinator import EcoMainCloudCoordinator
from test_runtime import RealHARuntimeFixture


class CloudPayloadStructureTests(RealHARuntimeFixture):
    def coordinator(self, payload):
        api = AsyncMock()
        api.get_passageway.return_value = payload
        coordinator = EcoMainCloudCoordinator(self.hass, self.make_entry("cloud"), api)
        self.addAsyncCleanup(coordinator.async_shutdown)
        return coordinator

    async def test_bad_channel_elements_keep_valid_household_and_channel_values(self):
        coordinator = self.coordinator({
            "household_electricity": {"power": 20, "energy": 5},
            "ch_info": [None, "bad", 7, {"ch_number": 0, "power": 2.5, "energy": 1}],
        })
        await coordinator.async_refresh()
        self.assertTrue(coordinator.last_update_success)
        self.assertEqual(coordinator.data["main_all_power_avg_1m"], 20)
        self.assertEqual(coordinator.data["main_all_energy_total_1m"], 5)
        self.assertEqual(coordinator.data["main_ch1_power_avg_1m"], 2.5)

    async def test_bad_household_container_keeps_valid_channels(self):
        for household in ("bad", [1], 7, True):
            with self.subTest(household=household):
                coordinator = self.coordinator({
                    "household_electricity": household,
                    "ch_info": [{"ch_number": 0, "power": 2.5, "energy": 1}],
                })
                values = await coordinator._async_update_data()
                self.assertEqual(values["main_ch1_power_avg_1m"], 2.5)
                self.assertNotIn("main_all_power_avg_1m", values)

    async def test_bad_channel_container_keeps_valid_household(self):
        for channels in ("bad", {"ch_number": 0}, 7, True):
            with self.subTest(channels=channels):
                coordinator = self.coordinator({
                    "household_electricity": {"power": 20, "energy": 5},
                    "ch_info": channels,
                })
                values = await coordinator._async_update_data()
                self.assertEqual(values["main_all_power_avg_1m"], 20)
                self.assertNotIn("main_ch1_power_avg_1m", values)
