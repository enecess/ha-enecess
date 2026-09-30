"""Verify stable measurement presentation independently of selected defaults."""

from types import SimpleNamespace
import unittest

from flow_test_support import load_flow


LOCAL_ORDER = [
    "energy_forward",
    "energy_reverse",
    "reactive_energy_forward",
    "reactive_energy_reverse",
    "apparent_energy",
    "power",
    "reactive_power",
    "apparent_power",
    "voltage",
    "current",
    "power_factor",
    "frequency",
]


class MeasurementDisplayTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    async def test_setup_and_options_order_does_not_promote_selected_measurements(self):
        data = {
            "device_type": "ecomain",
            "mode": "manual",
            "ecomain_serial": "FICTIONAL-DISPLAY-001",
            "ecomain_firmware_version": 139,
        }
        for options in (False, True):
            for selected in (
                ["power", "energy_forward", "energy_reverse"],
                ["apparent_energy", "current", "power"],
            ):
                with self.subTest(options=options, selected=selected):
                    if options:
                        flow = self.module.EnecessOptionsFlow(
                            SimpleNamespace(
                                data=data,
                                options={"measurement_types": selected},
                                entry_id="display",
                            )
                        )
                    else:
                        flow = self.module.ConfigFlow()
                        flow._entry_data = data
                        flow._measurement_types = selected
                    result = await flow.async_step_measurement_types()
                    field = next(
                        value
                        for key, value in result["data_schema"].schema.items()
                        if str(key) == "measurement_types"
                    )
                    self.assertEqual(field.config["options"], LOCAL_ORDER)
                    self.assertEqual(
                        result["data_schema"]({})["measurement_types"], selected
                    )

    def test_preserved_offline_choices_keep_physical_order_and_selection(self):
        selected = ["apparent_energy", "current", "voltage", "power"]
        for firmware in (None, 136, 138):
            with self.subTest(firmware=firmware):
                schema = self.module._measurement_schema(
                    {"mode": "manual", "ecomain_firmware_version": firmware},
                    selected,
                    preserve_selected=True,
                )
                field = next(iter(schema.schema.values()))
                self.assertEqual(
                    field.config["options"],
                    ["energy_forward", "energy_reverse", "apparent_energy",
                     "power", "voltage", "current"],
                )
                self.assertEqual(schema({})["measurement_types"], selected)

    def test_legacy_and_cloud_order_is_independent_of_default_selection(self):
        for mode, firmware, selected, expected in (
            ("manual", None, ["power", "energy_forward", "energy_reverse"],
             ["energy_forward", "energy_reverse", "power"]),
            ("manual", 136, ["power", "energy_forward", "energy_reverse"],
             ["energy_forward", "energy_reverse", "power"]),
            ("cloud", None, ["power", "energy"], ["energy", "power"]),
        ):
            with self.subTest(mode=mode, firmware=firmware):
                schema = self.module._measurement_schema(
                    {"mode": mode, "ecomain_firmware_version": firmware}, selected
                )
                self.assertEqual(
                    next(iter(schema.schema.values())).config["options"], expected
                )
                self.assertEqual(schema({})["measurement_types"], selected)
