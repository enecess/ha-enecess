import asyncio
from dataclasses import dataclass
from typing import Any, Protocol


class LocalModbusClient(Protocol):
    async def read_holding_registers(self, address: int, count: int) -> Any:
        """Read holding registers from the local device."""

    async def async_close(self) -> None:
        """Close the temporary Modbus connection."""


@dataclass(frozen=True)
class LocalValidationResult:
    error: str | None = None
    online_slaves: list[str] | None = None


async def async_validate_local_device(
        client: LocalModbusClient,
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
            firmware_version = int(response.registers[0]) & 0xFFFF
            if firmware_version < minimum_firmware:
                return LocalValidationResult(error="firmware_too_old")
        except Exception:
            return LocalValidationResult(error="firmware_too_old")

        try:
            response = await client.read_holding_registers(
                slave_register_start,
                slave_register_count,
            )
            online_slaves = [
                str(index)
                for index, value in enumerate(response.registers, start=1)
                if (int(value) & 0xFFFF) == 1 and str(index) in allowed_slaves
            ]
            return LocalValidationResult(online_slaves=online_slaves)
        except Exception:
            return LocalValidationResult(error="cannot_connect_local")
    finally:
        await client.async_close()
