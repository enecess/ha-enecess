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
        coordinator = self.coordinator(
            {
                "household_electricity": {"power": 20, "energy": 5},
                "ch_info": [
                    None,
                    "bad",
                    7,
                    {"ch_number": 0, "power": 2.5, "energy": 1},
                ],
            }
        )
        await coordinator.async_refresh()
        self.assertTrue(coordinator.last_update_success)
        self.assertEqual(coordinator.data["main_all_power_avg_1m"], 20)
        self.assertEqual(coordinator.data["main_all_energy_total_1m"], 5)
        self.assertEqual(coordinator.data["main_ch1_power_avg_1m"], 2.5)

    async def test_bad_household_container_keeps_valid_channels(self):
        for household in ("bad", [1], 7, True):
            with self.subTest(household=household):
                coordinator = self.coordinator(
                    {
                        "household_electricity": household,
                        "ch_info": [{"ch_number": 0, "power": 2.5, "energy": 1}],
                    }
                )
                values = await coordinator._async_update_data()
                self.assertEqual(values["main_ch1_power_avg_1m"], 2.5)
                self.assertNotIn("main_all_power_avg_1m", values)

    async def test_bad_channel_container_keeps_valid_household(self):
        for channels in ("bad", {"ch_number": 0}, 7, True):
            with self.subTest(channels=channels):
                coordinator = self.coordinator(
                    {
                        "household_electricity": {"power": 20, "energy": 5},
                        "ch_info": channels,
                    }
                )
                values = await coordinator._async_update_data()
                self.assertEqual(values["main_all_power_avg_1m"], 20)
                self.assertNotIn("main_ch1_power_avg_1m", values)

    async def test_invalid_channel_numbers_cannot_replace_valid_values_or_abort_poll(
        self,
    ):
        for number in (
            False,
            True,
            0.5,
            1.5,
            float("inf"),
            float("-inf"),
            float("nan"),
            -1,
            10,
            "-1",
            "10",
            "",
            "bad",
            "0.5",
            None,
        ):
            with self.subTest(number=number):
                coordinator = self.coordinator(
                    {
                        "household_electricity": {"power": 20, "energy": 5},
                        "ch_info": [
                            {"ch_number": 0, "power": 10, "energy": 1},
                            {"ch_number": 1, "power": 11, "energy": 2},
                            {"ch_number": number, "power": 999, "energy": 999},
                        ],
                    }
                )
                await coordinator.async_refresh()
                self.assertTrue(coordinator.last_update_success)
                self.assertEqual(
                    coordinator.data,
                    {
                        "main_all_power_avg_1m": 20.0,
                        "main_all_energy_total_1m": 5.0,
                        "main_ch1_power_avg_1m": 10.0,
                        "main_ch1_energy_total_1m": 1.0,
                        "main_ch2_power_avg_1m": 11.0,
                        "main_ch2_energy_total_1m": 2.0,
                        "main_all_energy_accumulated": 5.0,
                        "main_ch1_energy_accumulated": 1.0,
                        "main_ch2_energy_accumulated": 2.0,
                    },
                )

    async def test_supported_integer_channel_numbers_preserve_zero_readings(self):
        for number, key in (
            (0, "main_ch1_power_avg_1m"),
            (9, "main_ch10_power_avg_1m"),
            (0.0, "main_ch1_power_avg_1m"),
            (9.0, "main_ch10_power_avg_1m"),
            ("0", "main_ch1_power_avg_1m"),
            ("9", "main_ch10_power_avg_1m"),
        ):
            with self.subTest(number=number):
                coordinator = self.coordinator(
                    {
                        "ch_info": [{"ch_number": number, "power": 0, "energy": 0}],
                    }
                )
                values = await coordinator._async_update_data()
                self.assertEqual(values[key], 0.0)
                self.assertEqual(len(values), 3)
