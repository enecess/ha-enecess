"""Poll and normalize ecoMain measurements over Modbus or the cloud."""

import asyncio
from datetime import timedelta
import logging
import math
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus import ModbusException

from ..client_api import EnecessApi, EnecessApiError, EnecessAuthError
from ..client_modbus import (
    EnecessModbusClient,
    decode_int16,
    decode_int32_word_swap,
    decode_int64_word_swap,
)
from ..const import (
    CONF_CLOUD_UPDATE_INTERVAL,
    CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER,
    CONF_ECOMAIN_MIN_FIRMWARE_VERSION,
    CONF_ECOMAIN_PORT,
    CONF_LOCAL_UPDATE_INTERVAL,
    CONST_CLOUD_PASSWORD,
    CONST_CLOUD_TOKEN,
    CONST_CLOUD_USERNAME,
    CONST_ECOMAIN_CLOUD_SLAVE_MAP,
    CONST_ECOMAIN_HOST,
    CONST_ECOMAIN_PORT,
    CONST_ECOMAIN_SERIAL,
)
from ..extra import build_entry_specs
from .model import RegisterSpec, available_local_measurements

_LOGGER = logging.getLogger(__name__)


def build_read_blocks(specs: list[RegisterSpec]) -> list[tuple[int, int]]:
    """Coalesce adjacent complete values without reading unselected registers."""
    blocks: list[tuple[int, int]] = []
    intervals = sorted(
        {
            (spec.address, spec.regs)
            for spec in specs
            if spec.address is not None and spec.regs is not None
        }
    )
    for address, width in intervals:
        if width < 1 or width > 125:
            raise ValueError(f"Unsupported register count: {width}")
        if blocks:
            start, count = blocks[-1]
            if address == start + count and count + width <= 125:
                blocks[-1] = (start, count + width)
                continue
        blocks.append((address, width))
    return blocks


class EcoMainModbusCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator for ecoMain local Modbus polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: EnecessModbusClient,
        specs: list[RegisterSpec],
    ) -> None:
        """Initialize the coordinator and its entry-owned connection state."""
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=entry,
            name="enecess ecoMain Local Coordinator",
            update_interval=timedelta(seconds=CONF_LOCAL_UPDATE_INTERVAL),
        )
        self._entry = entry
        self._client = client
        self._requested_specs = list(specs)
        self.specs = list(specs)
        self.firmware_version: int | None = None
        self._validated_target: tuple[str, int] | None = None

    async def _async_update_data(self) -> dict[str, float]:
        try:
            return await self._async_read_data()
        except UpdateFailed:
            raise
        except (ModbusException, OSError, TimeoutError) as err:
            raise UpdateFailed(str(err)) from err

    async def _async_read_data(self) -> dict[str, float]:
        """Validate firmware and decode all configured register blocks."""
        data = self._entry.data
        host = data.get(CONST_ECOMAIN_HOST)
        port = data.get(CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT)
        if not host:
            raise UpdateFailed("No host target to connect")

        await self._client.async_set_target(host, port)
        target = (host, port)
        if self._validated_target != target:
            firmware = await self._client.read_holding_registers(
                CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER, 1
            )
            if len(firmware.registers) != 1:
                raise UpdateFailed("Incomplete ecoMain firmware response")
            version = firmware.registers[0]
            if (
                not isinstance(version, int)
                or isinstance(version, bool)
                or not 0 <= version <= 65535
            ):
                raise UpdateFailed("Invalid ecoMain firmware response")
            if version < CONF_ECOMAIN_MIN_FIRMWARE_VERSION:
                raise UpdateFailed(
                    f"ecoMain firmware {version} is unsupported; version {CONF_ECOMAIN_MIN_FIRMWARE_VERSION}+ is required"
                )
            available = available_local_measurements(version)
            self.specs = [
                spec
                for spec in self._requested_specs
                if spec.measurement_type in available
                or (spec.measurement_type is None and spec.kind in ("power", "energy"))
            ]
            self.firmware_version = version
            self._validated_target = target

        reg_map: dict[int, int] = {}
        for start, count in build_read_blocks(self.specs):
            rr = await self._client.read_holding_registers(start, count)
            if len(rr.registers) != count:
                raise UpdateFailed(
                    f"Incomplete register read at {start}: expected {count}, got {len(rr.registers)}"
                )
            reg_map.update(((start + i), r) for i, r in enumerate(rr.registers))

        out: dict[str, float] = {}
        for spec in self.specs:
            if spec.address is None or spec.regs is None:
                continue
            regs = [reg_map[spec.address + i] for i in range(spec.regs)]
            if spec.regs == 1:
                raw = decode_int16(regs, signed=spec.signed)
            elif spec.regs == 2:
                raw = decode_int32_word_swap(regs, signed=spec.signed)
            elif spec.regs == 4:
                raw = decode_int64_word_swap(regs, signed=spec.signed)
            else:
                raise UpdateFailed(f"Unsupported register count: {spec.regs}")
            out[spec.key] = float(raw) * spec.scale
        return out


class EcoMainCloudCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator for ecoMain cloud polling."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: EnecessApi
    ) -> None:
        """Initialize the coordinator and its entry-owned connection state."""
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=entry,
            name="enecess ecoMain Cloud Coordinator",
            update_interval=timedelta(seconds=CONF_CLOUD_UPDATE_INTERVAL),
        )
        self._entry = entry
        self._api = api

        self._token: str = entry.data[CONST_CLOUD_TOKEN]
        self._username: str = entry.data[CONST_CLOUD_USERNAME]
        self._password: str = entry.data[CONST_CLOUD_PASSWORD]
        self._serial: str = entry.data[CONST_ECOMAIN_SERIAL]
        self._slave_map: dict[int, Any] = entry.data.get(
            CONST_ECOMAIN_CLOUD_SLAVE_MAP, {}
        )

        self.specs = build_entry_specs(entry.data, entry.options)

    async def _refresh_token_and_store(self) -> None:
        token = await self._api.generate_token(self._username, self._password)
        if not token:
            raise EnecessAuthError("Cloud auth succeeded but token missing")

        self._token = token
        if self._entry.data.get(CONST_CLOUD_TOKEN) != token:
            self.hass.config_entries.async_update_entry(
                self._entry, data={**self._entry.data, CONST_CLOUD_TOKEN: token}
            )

    async def _fetch(self) -> dict[int, Any]:
        """Fetch raw cloud payload for main + slaves."""
        targets: dict[int, Any] = {0: self._serial, **(self._slave_map or {})}

        async def _get(idx: int, hw: Any) -> tuple[int, Any]:
            return idx, await self._api.get_passageway(self._token, str(hw))

        results = await asyncio.gather(*(_get(i, hw) for i, hw in targets.items()))
        return dict(results)

    async def _fetch_and_transform(self) -> dict[str, float]:
        data = await self._fetch()
        values: dict[str, float] = {}

        def _store(key: str, raw: Any) -> None:
            if raw is None or isinstance(raw, bool):
                return
            try:
                value = float(raw)
            except (TypeError, ValueError, OverflowError):
                return
            if math.isfinite(value):
                values[key] = value

        def _apply(index: int) -> None:
            hw_data = data.get(index) or {}
            if index == 0:
                prefix = "main"
                main_data = hw_data.get("household_electricity", {}) or {}
                if main_data:
                    pwr = main_data.get("power")
                    eng = main_data.get("energy")
                    _store("main_all_power_avg_1m", pwr)
                    _store("main_all_energy_total_1m", eng)
            else:
                prefix = f"sub{index}"

            channels = hw_data.get("ch_info", []) or []
            for ch in channels:
                raw_ch_no = ch.get("ch_number")
                if raw_ch_no is None:
                    continue
                try:
                    ch_no = int(raw_ch_no) + 1
                except (TypeError, ValueError):
                    continue
                power = ch.get("power")
                energy = ch.get("energy")
                _store(f"{prefix}_ch{ch_no}_power_avg_1m", power)
                _store(f"{prefix}_ch{ch_no}_energy_total_1m", energy)

        _apply(0)
        for idx in sorted((self._slave_map or {}).keys()):
            _apply(idx)

        return values

    async def _async_update_data(self) -> dict[str, float]:
        try:
            try:
                return await self._fetch_and_transform()
            except EnecessAuthError:
                await self._refresh_token_and_store()
                return await self._fetch_and_transform()
        except EnecessAuthError as err:
            raise ConfigEntryAuthFailed("Cloud authentication failed") from err
        except (EnecessApiError, OSError, TimeoutError) as err:
            raise UpdateFailed("Cloud request failed") from err
