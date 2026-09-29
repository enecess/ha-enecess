"""Verify firmware details and conditional upgrade guidance on measurement forms."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from flow_test_support import load_flow, submit_values


class MeasurementFirmwareFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module = load_flow(self)

    async def test_local_versions_cloud_and_navigation_in_both_flows(self):
        for options in (False, True):
            for mode, version, step in (
                ("manual", 136, "measurement_types_legacy"),
                ("manual", 138, "measurement_types_legacy"),
                ("manual", 139, "measurement_types_local"),
                ("auto", 140, "measurement_types_local"),
                ("manual", None, "measurement_types_local"),
                ("cloud", None, "measurement_types"),
            ):
                with self.subTest(options=options, mode=mode, version=version):
                    data = {
                        "device_type": "ecomain",
                        "mode": mode,
                        "ecomain_serial": "FICTIONAL-FIRMWARE-001",
                        "ecomain_firmware_version": version,
                    }
                    if options:
                        flow = self.module.EnecessOptionsFlow(
                            SimpleNamespace(data=data, options={}, entry_id="firmware")
                        )
                        await flow._show_options_menu()
                    else:
                        flow = self.module.ConfigFlow()
                        flow._entry_data = data
                        await flow.async_step_extra_entities()
                    result = await flow.async_step_measurement_types()
                    self.assertEqual(result["step_id"], step)
                    fields = result.get("description_placeholders") or {}
                    self.assertEqual(
                        fields,
                        {}
                        if mode == "cloud"
                        else {
                            "firmware_version": str(version)
                            if version is not None
                            else "—"
                        },
                    )
                    self.assertEqual(result["data_schema"]({})["flow_action"], "save")
                    handler = getattr(flow, "async_step_" + step)
                    result = await handler(
                        submit_values(result, {"measurement_types": []})
                    )
                    self.assertEqual(result["step_id"], step)
                    self.assertEqual(
                        result["errors"]["base"], "no_measurements_selected"
                    )
                    result = await handler(
                        submit_values(result, {"measurement_types": ["power"]})
                    )
                    self.assertEqual(
                        result["step_id"], "init" if options else "extra_entities"
                    )
                    result = await flow.async_step_measurement_types()
                    result = await handler(
                        submit_values(result, {"flow_action": "back"})
                    )
                    self.assertEqual(
                        result["step_id"], "init" if options else "extra_entities"
                    )

    def test_chinese_guidance_is_short_and_only_on_legacy_local_page(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "custom_components/enecess/translations/zh-Hans.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in ("config", "options"):
            steps = data[section]["step"]
            self.assertNotIn("固件", steps["measurement_types"]["description"])
            self.assertIn(
                "{firmware_version}", steps["measurement_types_local"]["description"]
            )
            self.assertNotIn("139", steps["measurement_types_local"]["description"])
            self.assertIn(
                "更多测量类型需升级至固件 139 或以上。",
                steps["measurement_types_legacy"]["description"],
            )
