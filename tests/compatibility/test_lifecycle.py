"""Regression checks for real HA entry setup and Modbus resource ownership."""

import asyncio
from contextlib import ExitStack
from datetime import timedelta
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntries, current_entry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import EntityPlatform

from custom_components import enecess
from custom_components.enecess.client_modbus import EnecessModbusClient
from test_runtime import RealHARuntimeFixture

_CLOSE = EnecessModbusClient.async_close
_READ = EnecessModbusClient.read_holding_registers
_TARGET = EnecessModbusClient.async_set_target


class Transport:
    """Stand in for an external socket while exercising the real wrapper."""

    def __init__(self, registers):
        self.registers = registers
        self.connected = False
        self.close_count = 0
        self.block_reads = False
        self.read_started = asyncio.Event()

    async def connect(self):
        self.connected = True
        return True

    async def read_holding_registers(self, *, address, count, device_id):
        if self.block_reads:
            self.read_started.set()
            await asyncio.Event().wait()
        if isinstance(self.registers, BaseException):
            raise self.registers
        values = self.registers if address == 3009 else [0] * count
        return SimpleNamespace(registers=values, isError=lambda: False)

    def close(self):
        self.close_count += 1
        self.connected = False


class LifecycleTests(RealHARuntimeFixture):
    """Failed or cancelled setup releases its own resources before a retry."""

    def transport_context(self, transport):
        stack = ExitStack()
        for name, implementation in (
            ("async_close", _CLOSE),
            ("read_holding_registers", _READ),
            ("async_set_target", _TARGET),
        ):
            stack.enter_context(patch.object(EnecessModbusClient, name, implementation))
        stack.enter_context(
            patch(
                "custom_components.enecess.client_modbus.AsyncModbusTcpClient",
                return_value=transport,
            )
        )
        return stack

    async def test_first_refresh_failure_closes_each_retry(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        for _ in range(2):
            transport = Transport([])
            with self.transport_context(transport):
                with self.assertRaises(ConfigEntryNotReady):
                    await enecess.async_setup_entry(self.hass, entry)
                await entry._async_process_on_unload(self.hass)
                self.assertEqual(transport.close_count, 1)
                self.assertFalse(transport.connected)
                self.assertIsNone(getattr(entry, "runtime_data", None))

    async def test_cancelled_first_refresh_closes_connection(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        transport = Transport([139])
        transport.block_reads = True
        with self.transport_context(transport):
            setup = asyncio.create_task(enecess.async_setup_entry(self.hass, entry))
            await transport.read_started.wait()
            setup.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await setup
            self.assertEqual(transport.close_count, 1)
            self.assertIsNone(getattr(entry, "runtime_data", None))

    async def test_unexpected_modbus_bug_is_not_disguised_as_connection_failure(self):
        from custom_components.enecess.ecomain.coordinator import (
            EcoMainModbusCoordinator,
        )

        entry = self.make_entry("local")
        client = SimpleNamespace(
            async_set_target=AsyncMock(),
            read_holding_registers=AsyncMock(
                side_effect=TypeError("fictional decoder bug")
            ),
        )
        coordinator = EcoMainModbusCoordinator(self.hass, entry, client, [])
        with self.assertRaisesRegex(TypeError, "fictional decoder bug"):
            await coordinator._async_update_data()

    async def test_platform_setup_failure_closes_connection(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        transport = Transport([139])
        with (
            self.transport_context(transport),
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
                side_effect=RuntimeError("fictional platform failure"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "fictional platform failure"):
                await enecess.async_setup_entry(self.hass, entry)
            self.assertEqual(transport.close_count, 1)
            self.assertIsNone(getattr(entry, "runtime_data", None))

    async def test_ha_stop_closes_loaded_connection_without_entry_unload(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        transport = Transport([139])
        with (
            self.transport_context(transport),
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            await enecess.async_setup_entry(self.hass, entry)
            self.assertTrue(transport.connected)
            await self.hass.async_stop(force=True)
            self.assertFalse(transport.connected)
            self.assertEqual(transport.close_count, 1)
            with self.assertNoLogs("homeassistant.core", level="ERROR"):
                await entry._async_process_on_unload(self.hass)

    async def test_partial_platform_failure_and_cancellation_remove_live_entities(self):
        from custom_components.enecess.ecomain.model import build_sensor_descriptions
        from custom_components.enecess.ecomain.sensor import EcoMainSensor

        for failure in (
            RuntimeError("fictional switch failure"),
            asyncio.CancelledError(),
        ):
            with self.subTest(failure=type(failure).__name__):
                entry = self.make_entry("local")
                token = current_entry.set(entry)
                transport = Transport([139])
                platform = EntityPlatform(
                    hass=self.hass,
                    logger=logging.getLogger(__name__),
                    domain="sensor",
                    platform_name="enecess",
                    platform=None,
                    scan_interval=timedelta(seconds=30),
                    entity_namespace=None,
                )
                platform.config_entry = entry
                self.addAsyncCleanup(platform.async_reset)
                coordinators = []

                async def partial_forward(*args):
                    coordinator = entry.runtime_data.coordinator
                    coordinators.append(coordinator)
                    description = build_sensor_descriptions(coordinator.specs)[0]
                    await platform.async_add_entities(
                        [
                            EcoMainSensor(
                                coordinator,
                                "local",
                                f"FICTIONAL-PARTIAL-{type(failure).__name__}",
                                description,
                            )
                        ]
                    )
                    self.assertEqual(len(platform.entities), 1)
                    raise failure

                async def rollback(*args):
                    await platform.async_reset()
                    return True

                try:
                    with (
                        self.transport_context(transport),
                        patch.object(
                            ConfigEntries,
                            "async_forward_entry_setups",
                            side_effect=partial_forward,
                        ),
                        patch.object(
                            ConfigEntries,
                            "async_unload_platforms",
                            side_effect=rollback,
                        ),
                    ):
                        with self.assertRaises(type(failure)):
                            await enecess.async_setup_entry(self.hass, entry)
                        self.assertFalse(platform.entities)
                        self.assertFalse(coordinators[0]._listeners)
                        self.assertFalse(transport.connected)
                finally:
                    await platform.async_reset()
                    current_entry.reset(token)

    async def test_failed_unload_keeps_connection_then_success_closes_it(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        transport = Transport([139])
        with (
            self.transport_context(transport),
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch.object(
                ConfigEntries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                side_effect=[False, True],
            ),
        ):
            self.assertTrue(await enecess.async_setup_entry(self.hass, entry))
            self.assertFalse(await enecess.async_unload_entry(self.hass, entry))
            self.assertTrue(transport.connected)
            self.assertEqual(transport.close_count, 0)
            self.assertTrue(await enecess.async_unload_entry(self.hass, entry))
            self.assertFalse(transport.connected)
            self.assertEqual(transport.close_count, 1)

    async def test_verified_firmware_change_reloads_without_options_change(self):
        entry = self.make_entry("local")
        self.hass.config_entries.async_update_entry(
            entry, data={**entry.data, "ecomain_firmware_version": 136}
        )
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        with (
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch.object(
                ConfigEntries,
                "async_reload",
                new_callable=AsyncMock,
            ) as reload,
        ):
            await enecess.async_setup_entry(self.hass, entry)
            self.assertEqual(entry.data["ecomain_firmware_version"], 139)
            await self.hass.async_block_till_done()
            reload.assert_not_awaited()
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "ecomain_firmware_version": 138}
            )
            await self.hass.async_block_till_done()
            reload.assert_awaited_once_with(entry.entry_id)

    async def test_unload_cancels_poll_waiting_for_modbus_lock(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        transport = Transport([139])
        with (
            self.transport_context(transport),
            patch.object(ConfigEntries, "async_forward_entry_setups", new_callable=AsyncMock),
            patch.object(ConfigEntries, "async_unload_platforms", new_callable=AsyncMock, return_value=True),
        ):
            await enecess.async_setup_entry(self.hass, entry)
            runtime = entry.runtime_data
            await runtime.modbus_client._lock.acquire()
            poll = asyncio.create_task(runtime.coordinator.async_refresh())
            try:
                await asyncio.sleep(0)
                self.assertFalse(poll.done())
                await enecess.async_unload_entry(self.hass, entry)
            finally:
                runtime.modbus_client._lock.release()
                await asyncio.gather(poll, return_exceptions=True)
                connected_after_unload = transport.connected
                await runtime.modbus_client.async_close()
            self.assertTrue(poll.cancelled())
            self.assertFalse(connected_after_unload)
            self.assertIsNone(getattr(entry, "runtime_data", None))

    async def test_ha_stop_cancels_blocked_modbus_read(self):
        entry = self.make_entry("local")
        token = current_entry.set(entry)
        self.addCleanup(current_entry.reset, token)
        transport = Transport([139])
        with (
            self.transport_context(transport),
            patch.object(ConfigEntries, "async_forward_entry_setups", new_callable=AsyncMock),
        ):
            await enecess.async_setup_entry(self.hass, entry)
            runtime = entry.runtime_data
            transport.block_reads = True
            poll = asyncio.create_task(runtime.coordinator.async_refresh())
            await asyncio.wait_for(transport.read_started.wait(), 1)
            try:
                await self.hass.async_stop(force=True)
                self.assertTrue(poll.done())
                self.assertTrue(poll.cancelled())
                self.assertFalse(transport.connected)
            finally:
                poll.cancel()
                await asyncio.gather(poll, return_exceptions=True)

    async def test_shutdown_coordinator_cannot_open_new_modbus_poll(self):
        from custom_components.enecess.ecomain.coordinator import EcoMainModbusCoordinator

        entry = self.make_entry("local")
        transport = Transport([139])
        with self.transport_context(transport):
            client = EnecessModbusClient("192.0.2.1", 502)
            coordinator = EcoMainModbusCoordinator(self.hass, entry, client, [])
            await coordinator.async_shutdown()
            try:
                with self.assertRaises(asyncio.CancelledError):
                    await coordinator._async_update_data()
                self.assertFalse(transport.connected)
            finally:
                await client.async_close()
