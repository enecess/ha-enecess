import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import timedelta
import logging
from typing import TypeVar

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..client_api import EnecessApi, EnecessApiError, EnecessAuthError
from ..const import (
    CONF_CLOUD_UPDATE_INTERVAL,
    CONST_CLOUD_PASSWORD,
    CONST_CLOUD_TOKEN,
    CONST_CLOUD_USERNAME,
    CONST_ECOPLUG_DEVICES,
)
from .model import (
    EcoPlugConfig,
    EcoPlugSnapshot,
    parse_latest_plug_data,
    parse_plug_is_on,
)

_LOGGER = logging.getLogger(__name__)

_ResultT = TypeVar("_ResultT")
_ORDINARY_REQUEST_ERRORS = (
    EnecessApiError,
    ClientError,
    asyncio.TimeoutError,
    OSError,
)


class EcoPlugCloudCoordinator(
    DataUpdateCoordinator[dict[str, EcoPlugSnapshot]]
):
    """Coordinate cloud polling and control for one EcoPlug account."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: EnecessApi,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Enecess EcoPlug Cloud Coordinator",
            update_interval=timedelta(seconds=CONF_CLOUD_UPDATE_INTERVAL),
        )
        self._entry = entry
        self._api = api
        self._token_lock = asyncio.Lock()
        self._token: str = entry.data[CONST_CLOUD_TOKEN]
        self._username: str = entry.data[CONST_CLOUD_USERNAME]
        self._password: str = entry.data[CONST_CLOUD_PASSWORD]
        self._plugs = tuple(
            EcoPlugConfig(**item) for item in entry.data[CONST_ECOPLUG_DEVICES]
        )
        self._hardware_numbers = frozenset(
            plug.hardware_number for plug in self._plugs
        )

    async def _refresh_token(self, failed_token: str) -> None:
        """Refresh once when concurrent requests rejected the same token."""
        async with self._token_lock:
            if self._token != failed_token:
                return

            _LOGGER.warning("EcoPlug account token rejected; refreshing credentials")
            token = await self._api.generate_token(self._username, self._password)
            if not token:
                raise EnecessAuthError("Cloud auth succeeded but token missing")

            self._token = token
            if self._entry.data.get(CONST_CLOUD_TOKEN) != token:
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    data={**self._entry.data, CONST_CLOUD_TOKEN: token},
                )

    async def _request_with_auth_retry(
        self,
        request: Callable[[str], Awaitable[_ResultT]],
    ) -> _ResultT:
        """Run an authenticated request, refreshing and retrying at most once."""
        failed_token = self._token
        try:
            return await request(failed_token)
        except EnecessAuthError:
            await self._refresh_token(failed_token)
            return await request(self._token)

    async def _fetch_data(
        self, plug: EcoPlugConfig, token: str
    ) -> dict[str, object]:
        return await self._api.get_plug_data(token, plug.hardware_number)

    async def _fetch_state(
        self, plug: EcoPlugConfig, token: str
    ) -> dict[str, object]:
        return await self._api.get_plug_state(token, plug.hardware_number)

    def _request_error(
        self,
        plug: EcoPlugConfig,
        operation: str,
        result: object,
    ) -> str | None:
        if not isinstance(result, BaseException):
            return None
        if isinstance(result, EnecessAuthError):
            raise result
        if not isinstance(result, _ORDINARY_REQUEST_ERRORS):
            raise result

        message = str(result)
        _LOGGER.error(
            "EcoPlug %s %s request failed: %s",
            plug.hardware_number,
            operation,
            message,
        )
        return message

    async def _fetch_one(
        self, plug: EcoPlugConfig, token: str
    ) -> tuple[object, object]:
        return await asyncio.gather(
            self._fetch_data(plug, token),
            self._fetch_state(plug, token),
            return_exceptions=True,
        )

    def _build_snapshot(
        self,
        plug: EcoPlugConfig,
        data_result: object,
        state_result: object,
    ) -> EcoPlugSnapshot:
        data_error = self._request_error(plug, "data", data_result)
        state_error = self._request_error(plug, "state", state_result)

        power_rt: float | None = None
        energy_total: float | None = None
        if data_error is None:
            power_rt, energy_total = parse_latest_plug_data(data_result)

        is_on: bool | None = None
        if state_error is None:
            is_on = parse_plug_is_on(state_result)

        return EcoPlugSnapshot(
            power_rt=power_rt,
            energy_total=energy_total,
            is_on=is_on,
            data_error=data_error,
            state_error=state_error,
        )

    async def _fetch_attempt(
        self, token: str
    ) -> dict[str, EcoPlugSnapshot]:
        results = await asyncio.gather(
            *(self._fetch_one(plug, token) for plug in self._plugs)
        )

        # Auth invalidates the whole attempt, so detect it before converting
        # any ordinary request failures or publishing any snapshot values.
        for data_result, state_result in results:
            for result in (data_result, state_result):
                if isinstance(result, EnecessAuthError):
                    raise result

        return {
            plug.hardware_number: self._build_snapshot(
                plug, data_result, state_result
            )
            for plug, (data_result, state_result) in zip(self._plugs, results)
        }

    async def _async_update_data(self) -> dict[str, EcoPlugSnapshot]:
        failed_token = self._token
        try:
            return await self._fetch_attempt(failed_token)
        except EnecessAuthError:
            try:
                await self._refresh_token(failed_token)
            except (EnecessAuthError, *_ORDINARY_REQUEST_ERRORS) as err:
                raise UpdateFailed(str(err)) from err

        try:
            return await self._fetch_attempt(self._token)
        except EnecessAuthError as err:
            raise UpdateFailed(str(err)) from err

    async def async_control(self, hardware_number: str, is_on: bool) -> None:
        """Set one selected plug and publish the accepted state immediately."""
        if hardware_number not in self._hardware_numbers:
            raise ValueError(f"EcoPlug is not selected: {hardware_number}")

        await self._request_with_auth_retry(
            lambda token: self._api.control_plug(token, hardware_number, is_on)
        )

        current = self.data or {}
        snapshot = current.get(hardware_number, EcoPlugSnapshot())
        updated = dict(current)
        updated[hardware_number] = replace(
            snapshot,
            is_on=is_on,
            state_error=None,
        )
        self.async_set_updated_data(updated)
