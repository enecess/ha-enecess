"""Exercise discovery identity and cancellation with the real HA flow manager."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant import loader
from homeassistant.config_entries import SOURCE_IGNORE
from test_runtime import RealHARuntimeFixture

from custom_components.enecess import config_flow as flow_module, const as c


class DiscoveryFlowTests(RealHARuntimeFixture):
    """Keep discovery cards identifiable while users reset configuration drafts."""

    async def asyncSetUp(self):
        await super().asyncSetUp()
        loader.async_setup(self.hass)
        path = Path(flow_module.__file__).parent
        integration = loader.Integration(
            self.hass,
            "custom_components.enecess",
            path,
            json.loads((path / "manifest.json").read_text()),
        )
        self.hass.data[loader.DATA_INTEGRATIONS][c.DOMAIN] = integration
        context = patch(
            "homeassistant.config_entries._async_get_flow_handler",
            AsyncMock(return_value=flow_module.ConfigFlow),
        )
        context.start()
        self.addCleanup(context.stop)
        # Entry registration remains real; setting up network platforms is out of scope.
        context = patch.object(
            self.hass.config_entries, "async_setup", AsyncMock(return_value=True)
        )
        context.start()
        self.addCleanup(context.stop)

    async def asyncTearDown(self):
        for flow in self.hass.config_entries.flow.async_progress():
            self.hass.config_entries.flow.async_abort(flow["flow_id"])
        await super().asyncTearDown()

    async def discover(self, host="192.0.2.10", serial="FICTIONAL-DISCOVERY-001"):
        config = c.DEVICE_CONFIGS[c.CONST_DEVICE_ECOMAIN].discovery
        return await self.hass.config_entries.flow.async_init(
            c.DOMAIN,
            context={"source": "zeroconf"},
            data=SimpleNamespace(
                type=config.mdns_type,
                name=f"{config.mdns_prefix}{serial}.{config.mdns_type}",
                hostname="fictional-discovery.local.",
                host=host,
            ),
        )

    async def test_discovery_titles_identify_devices_without_loaded_translations(self):
        first = await self.discover()
        second = await self.discover("192.0.2.11", "FICTIONAL-DISCOVERY-002")
        progress = {
            item["flow_id"]: item
            for item in self.hass.config_entries.flow.async_progress()
        }
        for result, expected in (
            (first, "ecoMain FICTIONAL-DISCOVERY-001"),
            (second, "ecoMain FICTIONAL-DISCOVERY-002"),
        ):
            with self.subTest(title=expected):
                # HA uses name when config.flow_title has not been loaded yet.
                placeholders = progress[result["flow_id"]]["context"][
                    "title_placeholders"
                ]
                self.assertEqual(placeholders.get("name"), expected)

    async def test_repeated_discovery_keeps_only_original_pending_card(self):
        first = await self.discover()
        second = await self.discover("192.0.2.11")
        self.assertEqual(second["type"], "abort")
        self.assertEqual(second["reason"], "already_in_progress")
        progress = self.hass.config_entries.flow.async_progress()
        self.assertEqual([item["flow_id"] for item in progress], [first["flow_id"]])

    async def test_cancel_retains_identity_card_and_original_device(self):
        result = await self.discover()
        flow_id = result["flow_id"]
        manager = self.hass.config_entries.flow
        result = await manager.async_configure(flow_id, {})
        self.assertEqual(result["step_id"], "measurement_types_local")
        result = await manager.async_configure(
            flow_id, {"measurement_types": ["voltage"], "flow_action": "save"}
        )
        result = await manager.async_configure(flow_id, {"extra_action": "cancel"})
        self.assertEqual(result["flow_id"], flow_id)
        self.assertEqual(result["step_id"], "ecomain_local_confirm")
        self.assertEqual(result["data_schema"]({}), {})
        self.assertEqual(
            result["description_placeholders"]["ecomain_host"], "192.0.2.10"
        )
        progress = manager.async_progress()
        self.assertEqual(len(progress), 1)
        self.assertEqual(
            progress[0]["context"]["title_placeholders"].get("name"),
            "ecoMain FICTIONAL-DISCOVERY-001",
        )
        self.assertEqual(
            progress[0]["context"].get("unique_id"),
            "ecomain:FICTIONAL-DISCOVERY-001:mode_local",
        )
        self.assertEqual(self.hass.config_entries.async_entries(c.DOMAIN), [])
        duplicate = await self.discover("192.0.2.11")
        self.assertEqual(duplicate["reason"], "already_in_progress")
        restarted = await manager.async_configure(flow_id, {})
        self.assertEqual(restarted["step_id"], "measurement_types_local")
        defaults = restarted["data_schema"]({})["measurement_types"]
        self.assertNotEqual(defaults, ["voltage"])

    async def test_discovery_card_can_be_ignored_and_stays_ignored(self):
        result = await self.discover()
        manager = self.hass.config_entries.flow
        progress = manager.async_progress()[0]
        unique_id = progress["context"].get("unique_id")
        self.assertEqual(unique_id, "ecomain:FICTIONAL-DISCOVERY-001:mode_local")
        ignored = await manager.async_init(
            c.DOMAIN,
            context={"source": SOURCE_IGNORE},
            data={"unique_id": unique_id, "title": "Fictional discovered meter"},
        )
        self.assertEqual(ignored["type"], "create_entry")
        self.assertFalse(
            any(p["flow_id"] == result["flow_id"] for p in manager.async_progress())
        )
        repeated = await self.discover("192.0.2.11")
        self.assertEqual(repeated["reason"], "already_configured")
        self.assertEqual(len(self.hass.config_entries.async_entries(c.DOMAIN)), 1)

    async def test_discovery_updates_auto_host_but_preserves_manual_host(self):
        for mode in (c.CONST_ADD_MODE_LOCAL_AUTO, c.CONST_ADD_MODE_LOCAL_MANUAL):
            with self.subTest(mode=mode):
                entry = self.make_entry("local")
                self.hass.config_entries.async_update_entry(
                    entry,
                    unique_id="ecomain:FICTIONAL-DISCOVERY-001:mode_local",
                    data={**entry.data, c.CONST_ADD_MODE: mode},
                )
                result = await self.discover()
                self.assertEqual(result["reason"], "already_configured")
                self.assertEqual(entry.data[c.CONST_MDNS_IP], "192.0.2.10")
                self.assertEqual(
                    entry.data[c.CONST_ECOMAIN_HOST],
                    "192.0.2.10"
                    if mode == c.CONST_ADD_MODE_LOCAL_AUTO
                    else "192.0.2.1",
                )
                self.hass.config_entries._entries.pop(entry.entry_id)

    async def test_cancelled_scan_releases_shared_zeroconf_browser(self):
        flow = flow_module.ConfigFlow()
        flow.hass = self.hass
        started = asyncio.Event()
        browser = SimpleNamespace(async_cancel=AsyncMock())

        def start_browser(*args, **kwargs):
            started.set()
            return browser

        with (
            patch.object(
                flow_module.zeroconf,
                "async_get_async_instance",
                AsyncMock(return_value=SimpleNamespace(zeroconf=object())),
            ),
            patch.object(flow_module, "AsyncServiceBrowser", side_effect=start_browser),
        ):
            task = asyncio.create_task(
                flow._async_mdns_scan(c.DEVICE_CONFIGS["ecomain"].discovery)
            )
            await started.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        browser.async_cancel.assert_awaited_once()
