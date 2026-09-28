"""Authenticate and exchange validated payloads with the enecess cloud API."""

from dataclasses import dataclass
from typing import Any, TypeVar

import aiohttp

from .const import CONST_CLOUD_HEADER_TOKEN

_PayloadT = TypeVar("_PayloadT", dict, list)


class EnecessAuthError(Exception):
    """Authentication failed (token invalid/expired, bad credentials, etc.)."""


class EnecessApiError(Exception):
    """API request failed."""


@dataclass
class EnecessApi:
    """Wrap authenticated cloud requests and validate response envelopes."""

    session: aiohttp.ClientSession
    base_url: str

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    async def _json(self, resp: aiohttp.ClientResponse) -> dict[str, Any]:
        try:
            data = await resp.json(content_type=None)
        except (ValueError, TypeError) as err:
            raise EnecessApiError("Invalid cloud JSON response") from err
        if not isinstance(data, dict):
            raise EnecessApiError("Invalid cloud response")
        return data

    async def _request_payload(
        self,
        method: str,
        path: str,
        expected_type: type[_PayloadT],
        *,
        login: bool = False,
        **request_kwargs: Any,
    ) -> _PayloadT:
        """Validate transport status and the API envelope without echoing secrets."""
        try:
            async with getattr(self.session, method)(
                self._url(path), **request_kwargs
            ) as resp:
                if resp.status in (401, 403):
                    raise EnecessAuthError("Cloud authentication failed")
                if not 200 <= resp.status < 300:
                    raise EnecessApiError("Cloud HTTP request failed")
                data = await self._json(resp)
        except (aiohttp.ClientError, TimeoutError, OSError) as err:
            raise EnecessApiError("Cloud connection failed") from err
        status = data.get("status")
        if status in (401, 403) or (login and status in (400, 422)):
            raise EnecessAuthError("Cloud authentication failed")
        if status != 200:
            raise EnecessApiError("Cloud API request failed")
        payload = data.get("data")
        if payload is None and not login:
            return expected_type()
        if not isinstance(payload, expected_type):
            raise EnecessApiError("Invalid cloud response data")
        if isinstance(payload, list) and any(
            not isinstance(item, dict) for item in payload
        ):
            raise EnecessApiError("Invalid cloud hardware list")
        return payload

    async def _request_data(
        self,
        method: str,
        path: str,
        token: str,
        *,
        timeout: int,
        **request_kwargs: Any,
    ) -> dict[str, Any]:
        """Send an authenticated request and return successful business data."""
        return await self._request_payload(
            method,
            path,
            dict,
            headers={CONST_CLOUD_HEADER_TOKEN: token},
            timeout=timeout,
            **request_kwargs,
        )

    async def generate_token(self, username: str, password: str) -> str:
        """Exchange account credentials for a validated access token."""
        payload = {"username": username, "password": password}
        data = await self._request_payload(
            "post",
            "/pb/generate/token/",
            dict,
            login=True,
            json=payload,
            timeout=20,
        )
        token = data.get("token")
        if not isinstance(token, str) or not token:
            raise EnecessApiError("Invalid cloud token response")
        return token

    async def get_hardware_list(
        self, token: str, hardware_type: int, parent_id: int | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        """List cloud devices matching the requested type and parent."""
        params: dict[str, str] = {"hardware_type": str(hardware_type)}
        if parent_id is not None:
            params["parent_id"] = str(parent_id)
        params.update({k: str(v) for k, v in kwargs.items()})

        return await self._request_payload(
            "get",
            "/api/v1/hardware/",
            list,
            headers={CONST_CLOUD_HEADER_TOKEN: token},
            params=params,
            timeout=20,
        )

    async def get_passageway(self, token: str, hardware_number: str) -> dict[str, Any]:
        """Read ecoMain channel measurements for one hardware serial."""
        return await self._request_data(
            "get",
            "/api/v1/passageway/get_channel_info/",
            token,
            params={"hardware_number": str(hardware_number)},
            timeout=20,
        )

    async def get_plug_data(self, token: str, hardware_number: str) -> dict[str, Any]:
        """Fetch the latest ecoPlug power and energy measurements."""
        return await self._request_data(
            "get",
            "/api/v1/other/plug/data/",
            token,
            params={"hardware_number": str(hardware_number)},
            timeout=20,
        )

    async def get_plug_state(self, token: str, hardware_number: str) -> dict[str, Any]:
        """Query the current ecoPlug relay configuration."""
        return await self._request_data(
            "post",
            "/api/v1/other/plug/control/",
            token,
            json={
                "instruction": "plug_conf",
                "query_conf": "106",
                "hardware_number": str(hardware_number),
            },
            timeout=15,
        )

    async def control_plug(
        self,
        token: str,
        hardware_number: str,
        is_on: bool,
    ) -> dict[str, Any]:
        """Set the relay state of one ecoPlug device."""
        return await self._request_data(
            "post",
            "/api/v1/other/plug/control/",
            token,
            json={
                "instruction": "on_off",
                "is_on_off": 1 if is_on else 0,
                "hardware_number": str(hardware_number),
            },
            timeout=15,
        )
