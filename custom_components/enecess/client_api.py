from dataclasses import dataclass
from typing import Any, Optional

import aiohttp

from .const import CONST_CLOUD_HEADER_TOKEN


class EnecessAuthError(Exception):
    """Authentication failed (token invalid/expired, bad credentials, etc.)."""


class EnecessApiError(Exception):
    """API request failed."""


@dataclass
class EnecessApi:
    session: aiohttp.ClientSession
    base_url: str

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    async def _json(self, resp: aiohttp.ClientResponse) -> dict[str, Any]:
        return await resp.json(content_type=None)

    async def generate_token(self, username: str, password: str) -> str:
        url = self._url("/pb/generate/token/")
        payload = {"username": username, "password": password}

        async with self.session.post(url, json=payload, timeout=20) as resp:
            data = await self._json(resp)

        if data.get("status") != 200 or not data.get("data", {}).get("token"):
            raise EnecessAuthError(data.get("msg") or "Failed to obtain token")
        return data["data"]["token"]

    async def get_hardware_list(
            self,
            token: str,
            hardware_type: int,
            parent_id: Optional[int] = None,
            **kwargs
    ) -> list[dict[str, Any]]:
        url = self._url("/api/v1/hardware/")
        headers = {CONST_CLOUD_HEADER_TOKEN: token}
        params: dict[str, str] = {"hardware_type": str(hardware_type)}
        if parent_id is not None:
            params["parent_id"] = str(parent_id)
        params.update({k: str(v) for k, v in kwargs.items()})

        async with self.session.get(url, headers=headers, params=params, timeout=20) as resp:
            if resp.status in (401, 403):
                raise EnecessAuthError("Token invalid or expired")
            data = await self._json(resp)

        if data.get("status") != 200:
            raise EnecessApiError(data.get("msg") or "Failed to fetch hardware list")
        return data.get("data") or []

    async def get_passageway(self, token: str, hardware_number: str) -> dict[str, Any]:
        url = self._url("/api/v1/passageway/get_channel_info/")
        headers = {CONST_CLOUD_HEADER_TOKEN: token}
        params = {"hardware_number": str(hardware_number)}

        async with self.session.get(url, headers=headers, params=params, timeout=20) as resp:
            if resp.status in (401, 403):
                raise EnecessAuthError("Token invalid or expired")
            data = await self._json(resp)

        if data.get("status") != 200:
            raise EnecessApiError(data.get("msg") or f"Failed to fetch passageway: {hardware_number}")
        return data.get("data") or {}
