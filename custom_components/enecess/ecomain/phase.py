"""Read and write ecoMain/ecoSub branch phase configuration."""

from pymodbus import ModbusException

from ..client_modbus import EnecessModbusClient

_PHASES = ("L1", "L2", "L3")
_CHANNELS = tuple(f"channel_{channel}" for channel in range(1, 11))
_IO_ERRORS = (ModbusException, OSError, TimeoutError)


def _base_address(device_index: int) -> int:
    if type(device_index) is not int or not 0 <= device_index <= 3:
        raise ValueError("device_index must be an integer from 0 to 3")
    return 2000 + 10 * device_index


async def async_read_phases(
    client: EnecessModbusClient, device_index: int
) -> dict[str, str | None]:
    """Read ten channels; undefined low-bit phase values have no selection."""
    result = await client.read_holding_registers(_base_address(device_index), 10)
    phases = {}
    for channel, register in zip(_CHANNELS, result.registers, strict=True):
        value = register & 3
        phases[channel] = _PHASES[value] if value < 3 else None
    return phases


async def async_write_phases(
    client: EnecessModbusClient, device_index: int, desired: dict[str, str]
) -> dict[str, str]:
    """Save changed phases and return per-channel write or verification errors."""
    base = _base_address(device_index)
    for channel, phase in desired.items():
        if channel not in _CHANNELS or phase not in _PHASES:
            raise ValueError(f"Invalid channel phase: {channel}={phase!r}")
    if not desired:
        return {}
    try:
        current = (await client.read_holding_registers(base, 10)).registers
    except _IO_ERRORS:
        return {channel: "phase_write_failed" for channel in desired}

    errors = {}
    for channel, phase in desired.items():
        offset = _CHANNELS.index(channel)
        value = _PHASES.index(phase)
        if current[offset] & 3 == value:
            continue
        address = base + offset
        try:
            # Never propagate reserved bits into a write.
            await client.write_register(address, value)
        except _IO_ERRORS:
            errors[channel] = "phase_write_failed"
            continue
        try:
            actual = (await client.read_holding_registers(address, 1)).registers[0]
            if actual & 3 != value:
                errors[channel] = "phase_verify_failed"
        except _IO_ERRORS:
            errors[channel] = "phase_verify_failed"
    return errors
