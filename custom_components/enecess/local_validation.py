"""Validate firmware and slave availability during local configuration."""

import asyncio
from dataclasses import dataclass

from pymodbus import ModbusException

from .client_modbus import EnecessModbusClient
from .const import CONF_ECOMAIN_SOLAR_DEVICE_INDEX, CONF_ECOMAIN_SOLAR_FIRMWARE_VERSION


@dataclass(frozen=True)
class LocalValidationResult:
    """Carry a flow error or validated firmware and online slave indexes."""

    error: str | None = None
    online_slaves: list[str] | None = None
    firmware_version: int | None = None


async def async_validate_local_device(
    client: EnecessModbusClient,
    *,
    firmware_register: int,
    minimum_firmware: int,
    slave_register_start: int,
    slave_register_count: int,
    allowed_slaves: set[str],
    firmware_timeout: float,
) -> LocalValidationResult:
    """Validate local firmware and collect online slave indexes."""
    try:
        try:
            response = await asyncio.wait_for(
                client.read_holding_registers(firmware_register, 1),
                timeout=firmware_timeout,
            )
            firmware_version = response.registers[0]
            if firmware_version < minimum_firmware:
                return LocalValidationResult(
                    error="cannot_connect_local", firmware_version=firmware_version
                )
        except (ModbusException, OSError, TimeoutError):
            return LocalValidationResult(error="cannot_connect_local")

        try:
            if firmware_version >= CONF_ECOMAIN_SOLAR_FIRMWARE_VERSION:
                slave_register_count = CONF_ECOMAIN_SOLAR_DEVICE_INDEX
            response = await client.read_holding_registers(
                slave_register_start,
                slave_register_count,
            )
            if any(value not in (0, 1) for value in response.registers):
                return LocalValidationResult(
                    error="cannot_connect_local", firmware_version=firmware_version
                )
            online_slaves = [
                str(index)
                for index, value in enumerate(response.registers, start=1)
                if value == 1 and str(index) in allowed_slaves
            ]
            return LocalValidationResult(
                online_slaves=online_slaves, firmware_version=firmware_version
            )
        except (ModbusException, OSError, TimeoutError):
            return LocalValidationResult(
                error="cannot_connect_local", firmware_version=firmware_version
            )
    finally:
        await client.async_close()
