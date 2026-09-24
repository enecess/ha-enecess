"""Missing cloud readings must not become valid zero-valued formula inputs."""
import unittest

from test_ecomain_registers import load_runtime


class CloudFormulaSourcesTests(unittest.IsolatedAsyncioTestCase):
    async def values(self, payload):
        model, runtime = load_runtime()
        coordinator = object.__new__(runtime.EcoMainCloudCoordinator)
        coordinator.specs = model.build_specs_cloud([1])
        coordinator._slave_map = {1: "TEST_CLOUD_SUB_001"}

        async def fetch():
            return payload

        coordinator._fetch = fetch
        return await coordinator._fetch_and_transform()

    async def test_missing_cloud_measurements_are_absent_but_real_zero_is_retained(self):
        self.assertEqual(await self.values({}), {})
        values = await self.values({0: {"household_electricity": {"power": 0, "energy": None},
                                       "ch_info": [{"ch_number": 0, "power": None, "energy": 0}]}})
        self.assertEqual(values, {"main_all_power_avg_1m": 0.0, "main_ch1_energy_total_1m": 0.0})

    async def test_invalid_cloud_scalars_do_not_poison_other_measurements(self):
        for value in ("bad", True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                values = await self.values({0: {"household_electricity": {"power": value, "energy": value},
                                               "ch_info": [{"ch_number": 0, "power": value, "energy": value},
                                                           {"ch_number": 1, "power": "2.5", "energy": 1}]}})
                self.assertEqual(values, {"main_ch2_power_avg_1m": 2.5, "main_ch2_energy_total_1m": 1.0})
