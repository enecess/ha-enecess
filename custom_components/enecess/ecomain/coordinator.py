import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .model import build_specs_cloud, RegisterSpec
from .. import CONF_ECOMAIN_PORT
from ..client_api import EnecessApi, EnecessApiError, EnecessAuthError
from ..client_modbus import (
    EnecessModbusClient,
    decode_int32_word_swap,
    decode_int64_word_swap,
)
from ..const import (
    CONF_CLOUD_UPDATE_INTERVAL, CONF_LOCAL_UPDATE_INTERVAL, CONST_ECOMAIN_PORT, CONST_ECOMAIN_SERIAL, CONST_ECOMAIN_SELECTED_SLAVES,
    CONST_ECOMAIN_CLOUD_SLAVE_MAP, CONST_CLOUD_TOKEN, CONST_CLOUD_USERNAME, CONST_CLOUD_PASSWORD, CONST_ECOMAIN_HOST
)

_LOGGER = logging.getLogger(__name__)

ENERGY_BLOCKS = [
    (0, 120),
    (120, 120),
    (240, 112),  # up to 351
]

POWER_BLOCKS = [
    (1000, 88),  # 1000..1087
]


class EcoMainModbusCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator for EcoMain local Modbus polling."""

    def __init__(
            self,
            hass: HomeAssistant,
            entry: ConfigEntry,
            client: EnecessModbusClient,
            specs: list[RegisterSpec],
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Enecess EcoMain Local Coordinator",
            update_interval=timedelta(seconds=CONF_LOCAL_UPDATE_INTERVAL),
        )
        self._entry = entry
        self._client = client
        self.specs = specs

    async def _async_update_data(self) -> dict[str, float]:
        try:
            data = self._entry.data
            host = data.get(CONST_ECOMAIN_HOST)
            port = data.get(CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT)
            if not host:
                raise UpdateFailed("No host target to connect")

            await self._client.async_set_target(host, port)

            reg_map: dict[int, int] = {}
            for start, count in ENERGY_BLOCKS + POWER_BLOCKS:
                rr = await self._client.read_holding_registers(start, count)
                reg_map.update(((start + i), r) for i, r in enumerate(rr.registers))

            out: dict[str, float] = {spec.key: 0.0 for spec in self.specs}
            for spec in self.specs:
                if spec.address is None or spec.regs is None:
                    continue
                regs = [reg_map.get(spec.address + i, 0) for i in range(spec.regs)]
                if spec.regs == 2:
                    raw = decode_int32_word_swap(regs, signed=True)
                elif spec.regs == 4:
                    raw = decode_int64_word_swap(regs, signed=False)
                else:
                    raise UpdateFailed(f"Unsupported register count: {spec.regs}")
                out[spec.key] = float(raw) * spec.scale
            return out
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(str(err)) from err


class EcoMainCloudCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator for EcoMain cloud polling."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: EnecessApi) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Enecess EcoMain Cloud Coordinator",
            update_interval=timedelta(seconds=CONF_CLOUD_UPDATE_INTERVAL),
        )
        self._entry = entry
        self._api = api

        self._token: str = entry.data[CONST_CLOUD_TOKEN]
        self._username: str = entry.data[CONST_CLOUD_USERNAME]
        self._password: str = entry.data[CONST_CLOUD_PASSWORD]
        self._serial: str = entry.data[CONST_ECOMAIN_SERIAL]
        self._slave_map: dict[int, Any] = entry.data.get(CONST_ECOMAIN_CLOUD_SLAVE_MAP, {})

        self.specs = build_specs_cloud(entry.data.get(CONST_ECOMAIN_SELECTED_SLAVES))

    async def _refresh_token_and_store(self) -> None:
        token = await self._api.generate_token(self._username, self._password)
        if not token:
            raise UpdateFailed("Cloud auth succeeded but token missing")

        self._token = token
        if self._entry.data.get(CONST_CLOUD_TOKEN) != token:
            self.hass.config_entries.async_update_entry(self._entry, data={**self._entry.data, CONST_CLOUD_TOKEN: token})

    async def _fetch(self) -> dict[int, Any]:
        """Fetch raw cloud payload for main + slaves."""
        targets: dict[int, Any] = {0: self._serial, **(self._slave_map or {})}

        async def _get(idx: int, hw: Any) -> tuple[int, Any]:
            return idx, await self._api.get_passageway(self._token, str(hw))

        results = await asyncio.gather(*(_get(i, hw) for i, hw in targets.items()))
        return dict(results)

    async def _fetch_and_transform(self) -> dict[str, float]:
        data = await self._fetch()
        values: dict[str, float] = {spec.key: 0.0 for spec in self.specs}

        def _apply(index: int) -> None:
            hw_data = data.get(index) or {}
            if index == 0:
                prefix = "main"
                main_data = hw_data.get("household_electricity", {}) or {}
                if main_data:
                    pwr = main_data.get("power")
                    eng = main_data.get("energy")
                    if pwr is not None:
                        values["main_all_power_avg_1m"] = float(pwr)
                    if eng is not None:
                        values["main_all_energy_total_1m"] = float(eng)
            else:
                prefix = f"sub{index}"

            channels = hw_data.get("ch_info", []) or []
            for ch in channels:
                ch_no = ch.get("ch_number") + 1
                if ch_no is None:
                    continue
                power = ch.get("power")
                energy = ch.get("energy")
                if power is not None:
                    values[f"{prefix}_ch{ch_no}_power_avg_1m"] = float(power)
                if energy is not None:
                    values[f"{prefix}_ch{ch_no}_energy_total_1m"] = float(energy)

        _apply(0)
        for idx in sorted((self._slave_map or {}).keys()):
            _apply(idx)

        return values

    async def _async_update_data(self) -> dict[str, float]:
        try:
            return await self._fetch_and_transform()
        except EnecessAuthError:
            await self._refresh_token_and_store()
            return await self._fetch_and_transform()
        except (EnecessApiError, Exception) as err:
            raise UpdateFailed(str(err)) from err
