"""Standalone smoke tests against installed Home Assistant, without HA stubs.

Run with: python -m unittest discover -s tests/compatibility -v
Network clients and platform forwarding are mocked. Core, config entries,
registries, selectors, coordinators and entity classes are real HA objects.
These tests do not exercise full platform registration or recorder restore.
"""

import importlib
from pathlib import Path
import tempfile
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from aiohttp.resolver import ThreadedResolver

from custom_components import enecess
from custom_components.enecess import const as c
from custom_components.enecess.client_api import EnecessApi
from custom_components.enecess.client_modbus import EnecessModbusClient
from custom_components.enecess.config_flow import ConfigFlow
import homeassistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import (
    ConfigEntries,
    ConfigEntry,
    ConfigEntryState,
    current_entry,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, entity_registry, frame
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

SERIAL = "FICTIONAL-COMPAT-MAIN-001"
PLUG_SERIAL = "FICTIONAL-COMPAT-PLUG-001"
PLUG = {"hardware_number": PLUG_SERIAL, "name": "Compatibility plug"}


class FixtureResolver(ThreadedResolver):
    """Provide HA's resolver lifecycle without multicast discovery."""

    async def real_close(self):
        await self.close()


def entry_data(kind):
    data = {
        c.CONST_DEVICE_TYPE: c.CONST_DEVICE_ECOMAIN,
        c.CONST_ADD_MODE: c.CONST_ADD_MODE_CLOUD,
        c.CONST_ECOMAIN_SERIAL: SERIAL,
        c.CONST_CLOUD_USERNAME: "compatibility@example.invalid",
        c.CONST_CLOUD_PASSWORD: "fictional-password",
        c.CONST_CLOUD_TOKEN: "fictional-token",
        c.CONST_ECOMAIN_SELECTED_SLAVES: [],
        c.CONST_ECOMAIN_CLOUD_SLAVE_MAP: {},
    }
    if kind == "local":
        data.update(
            {
                c.CONST_ADD_MODE: c.CONST_ADD_MODE_LOCAL,
                c.CONST_ECOMAIN_HOST: "192.0.2.1",
                c.CONST_ECOMAIN_PORT: 502,
                c.CONST_ECOMAIN_FIRMWARE_VERSION: 139,
            }
        )
    elif kind == "plug":
        data.update(
            {
                c.CONST_DEVICE_TYPE: c.CONST_DEVICE_ECOPLUG,
                c.CONST_ECOPLUG_DEVICES: [PLUG],
            }
        )
    return data


class RealHARuntimeFixture(unittest.IsolatedAsyncioTestCase):
    """Provide real HA objects with isolated, fictional network boundaries."""

    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.temp.name)
        frame.async_setup(self.hass)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        if hasattr(device_registry, "async_setup"):
            device_registry.async_setup(self.hass)
        await device_registry.async_load(self.hass)
        await entity_registry.async_load(self.hass)
        self.entries = []
        # Avoid starting multicast discovery merely to create an HTTP session.
        self.resolver = FixtureResolver()
        context = patch(
            "homeassistant.helpers.aiohttp_client._async_make_resolver",
            return_value=self.resolver,
        )
        context.start()
        self.addCleanup(context.stop)
        # All calls at the network boundary are intercepted, including discovery.
        self.mocks = {}
        methods = {
            EnecessApi: {
                "generate_token": "fictional-token",
                "get_hardware_list": [PLUG],
                "get_passageway": {
                    "household_electricity": {"power": 120.0, "energy": 2.0},
                    "ch_info": [{"ch_number": 0, "power": 25.0, "energy": 0.5}],
                },
                "get_plug_data": {
                    "data": [
                        {
                            "time": "2026-01-01T00:00:00Z",
                            "power": 42.0,
                            "total_energy": 12.5,
                        }
                    ]
                },
                "get_plug_state": {
                    "response": {"data": {"p": [{"id": 106, "val": 1}]}}
                },
                "control_plug": None,
            },
            EnecessModbusClient: {"async_set_target": None, "async_close": None},
        }
        for cls, names in methods.items():
            for name, value in names.items():
                mock = AsyncMock(return_value=value)
                self.mocks[name] = mock
                context = patch.object(cls, name, mock)
                context.start()
                self.addCleanup(context.stop)

        async def read_registers(address, count, **kwargs):
            values = (
                [139]
                if address == c.CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER
                else [0] * count
            )
            return SimpleNamespace(registers=values)

        context = patch.object(
            EnecessModbusClient,
            "read_holding_registers",
            AsyncMock(side_effect=read_registers),
        )
        self.mocks["read_holding_registers"] = context.start()
        self.addCleanup(context.stop)

    async def asyncTearDown(self):
        for entry in self.entries:
            await entry._async_process_on_unload(self.hass)
        await self.hass.async_stop(force=True)
        await self.hass.async_block_till_done()
        await self.resolver.close()
        self.temp.cleanup()

    def make_entry(self, kind):
        entry = ConfigEntry(
            domain=c.DOMAIN,
            title="Compatibility fixture",
            version=1,
            minor_version=1,
            data=entry_data(kind),
            options={},
            source="user",
            unique_id=f"compatibility-{kind}",
            discovery_keys=MappingProxyType({}),
            subentries_data=[],
            state=ConfigEntryState.SETUP_IN_PROGRESS,
        )
        # Register without initiating HA's integration-loader setup pipeline.
        self.hass.config_entries._entries[entry.entry_id] = entry
        self.entries.append(entry)
        return entry


class RealHARuntimeTests(RealHARuntimeFixture):
    """Exercise the integration against an installed HA release."""

    async def test_all_production_modules_import_real_ha(self):
        self.assertTrue(homeassistant.__file__)
        root = Path(enecess.__file__).parent
        modules = []
        for source in sorted(root.rglob("*.py")):
            relative = source.relative_to(root).with_suffix("")
            parts = list(relative.parts)
            if parts[-1] == "__init__":
                parts.pop()
            name = ".".join(["custom_components.enecess", *parts])
            with self.subTest(module=name):
                modules.append(importlib.import_module(name))
        self.assertGreater(len(modules), 15)

    async def test_config_flow_real_selector_schemas(self):
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {"source": "user"}
        result = await flow.async_step_user()
        self.assertEqual(result["type"], "form")
        self.assertEqual(
            result["data_schema"]({c.CONST_DEVICE_TYPE: c.CONST_DEVICE_ECOMAIN}),
            {c.CONST_DEVICE_TYPE: c.CONST_DEVICE_ECOMAIN},
        )
        result = await flow.async_step_user(
            {c.CONST_DEVICE_TYPE: c.CONST_DEVICE_ECOMAIN}
        )
        self.assertEqual(result["step_id"], "ecomain_mode")
        result["data_schema"]({c.CONST_ADD_MODE: c.CONST_ADD_MODE_CLOUD})
        result = await flow.async_step_ecomain_mode(
            {c.CONST_ADD_MODE: c.CONST_ADD_MODE_CLOUD}
        )
        self.assertEqual(result["step_id"], "ecomain_cloud_login")
        result["data_schema"](
            {
                c.CONST_CLOUD_USERNAME: "compatibility@example.invalid",
                c.CONST_CLOUD_PASSWORD: "fictional-password",
            }
        )

    async def test_options_flow_local_schema(self):
        entry = self.make_entry("local")
        flow = ConfigFlow.async_get_options_flow(entry)
        flow.hass = self.hass
        flow.handler = entry.entry_id
        flow.context = {}
        result = await flow.async_step_init()
        self.assertEqual(result["type"], "form")
        self.assertFalse(result["errors"])
        result["data_schema"]({c.CONST_EXTRA_ACTION: c.CONST_EXTRA_ACTION_FINISH})
        measurement = await flow.async_step_measurement_types()
        self.assertEqual(measurement["step_id"], "measurement_types")
        self.assertTrue(measurement["data_schema"]({})[c.CONST_MEASUREMENT_TYPES])

    async def test_options_flow_plug_schema(self):
        flow = ConfigFlow.async_get_options_flow(self.make_entry("plug"))
        flow.hass = self.hass
        flow.context = {}
        result = await flow.async_step_init()
        self.assertEqual(result["step_id"], "ecoplug_select")
        self.assertFalse(result["errors"])
        self.assertEqual(
            result["data_schema"]({})[c.CONST_ECOPLUG_SELECTED], [PLUG_SERIAL]
        )

    async def exercise_entry(self, kind):
        entry = self.make_entry(kind)
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        with (
            patch.object(
                ConfigEntries, "async_forward_entry_setups", new_callable=AsyncMock
            ) as forward,
            patch.object(
                ConfigEntries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ) as unload,
        ):
            self.assertTrue(await enecess.async_setup_entry(self.hass, entry))
            forward.assert_awaited_once_with(entry, enecess.PLATFORMS)
            coordinator = entry.runtime_data.coordinator
            self.assertIsInstance(coordinator, DataUpdateCoordinator)
            self.assertTrue(coordinator.last_update_success)
            self.assertTrue(coordinator.data)
            entities = []
            sensor = importlib.import_module("custom_components.enecess.sensor")
            switch = importlib.import_module("custom_components.enecess.switch")
            await sensor.async_setup_entry(self.hass, entry, entities.extend)
            await switch.async_setup_entry(self.hass, entry, entities.extend)
            self.assertTrue(entities)
            self.assertEqual(
                len({entity.unique_id for entity in entities}), len(entities)
            )
            for entity in entities:
                self.assertTrue(entity.device_info["identifiers"])
                self.assertIsInstance(entity, (SensorEntity, SwitchEntity))
            if kind == "plug":
                self.assertEqual(len(entities), 3)
                self.assertEqual(
                    [entity.native_value for entity in entities[:2]], [42.0, 12.5]
                )
                self.assertTrue(all(entity.available for entity in entities))
                control = entities[-1]
                self.assertTrue(control.is_on)
                await control.async_turn_off()
                self.assertFalse(control.is_on)
                await control.async_turn_on()
                self.assertTrue(control.is_on)
                self.assertEqual(self.mocks["control_plug"].await_count, 2)
            elif kind == "local":
                self.assertEqual(coordinator.firmware_version, 139)
                self.assertTrue(
                    all(value == 0.0 for value in coordinator.data.values())
                )
                self.assertTrue(all(entity.available for entity in entities))
            else:
                self.assertEqual(coordinator.data["main_all_power_avg_1m"], 120.0)
            self.assertTrue(await enecess.async_unload_entry(self.hass, entry))
            unload.assert_awaited_once_with(entry, enecess.PLATFORMS)
            self.assertIsNone(getattr(entry, "runtime_data", None))
            if kind == "local":
                self.mocks["async_close"].assert_awaited_once()

    async def test_ecomain_local_setup_entities_unload(self):
        await self.exercise_entry("local")

    async def test_ecomain_cloud_setup_entities_unload(self):
        await self.exercise_entry("cloud")

    async def test_ecoplug_cloud_setup_control_unload(self):
        await self.exercise_entry("plug")


if __name__ == "__main__":
    unittest.main()
