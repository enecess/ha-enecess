"""Typed, non-persistent data owned by one enecess config entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .client_modbus import EnecessModbusClient
    from .ecomain.coordinator import EcoMainCloudCoordinator, EcoMainModbusCoordinator
    from .ecoplug.coordinator import EcoPlugCloudCoordinator


@dataclass
class EnecessRuntimeData:
    """Keep the coordinator and optional owned Modbus connection together."""

    coordinator: (
        EcoMainCloudCoordinator | EcoMainModbusCoordinator | EcoPlugCloudCoordinator
    )
    modbus_client: EnecessModbusClient | None = None


type EnecessConfigEntry = ConfigEntry[EnecessRuntimeData]
