"""Read and verify installation settings on a local ecoMain host."""

from dataclasses import dataclass
from decimal import Decimal

from pymodbus import ModbusException

from ..client_modbus import EnecessModbusClient, decode_int16, decode_int32_word_swap
from .phase import async_read_phases, async_write_phases

_CHANNELS = tuple(f"channel_{channel}" for channel in range(1, 11))
_MAIN_PHASES = ("l1", "l2", "l3")
_INVERTER_CHANNELS = tuple(str(channel) for channel in range(1, 11))
_IO_ERRORS = (ModbusException, OSError, TimeoutError)


@dataclass(frozen=True)
class ChannelSettings:
    """Expose device choices; omitted or unselected write fields stay untouched."""

    phases: dict[str, str | None]
    transformers: dict[str, str | None]
    main_transformers: dict[str, str | None]


@dataclass(frozen=True)
class SolarSettings:
    """Expose host parameters and only the requested inverter groups."""

    capacity: int
    temperature_coefficient: float
    inverter_channels: dict[int, list[str]]


def _validate_device_index(device_index: int) -> None:
    if type(device_index) is not int or not 0 <= device_index <= 3:
        raise ValueError("device_index must be an integer from 0 to 3")


async def _async_write_verified(
    client: EnecessModbusClient, address: int, values: list[int]
) -> str | None:
    """Write an absolute value once and distinguish write from readback failure."""
    try:
        if len(values) == 1:
            await client.write_register(address, values[0])
        else:
            await client.write_registers(address, values)
    except _IO_ERRORS:
        return "write_failed"
    try:
        actual = await client.read_holding_registers(address, len(values))
        if actual.registers != values:
            return "verify_failed"
    except _IO_ERRORS:
        return "verify_failed"
    return None


async def async_read_channel_settings(
    client: EnecessModbusClient, device_index: int
) -> ChannelSettings:
    """Read phase and CT selections without inventing undefined choices."""
    _validate_device_index(device_index)
    phases = await async_read_phases(client, device_index)
    transformers = await client.read_holding_registers(2043 + 10 * device_index, 10)
    main_transformers = {}
    if device_index == 0:
        main = await client.read_holding_registers(2040, 3)
        main_transformers = {
            phase: "100" if value == 100 else None
            for phase, value in zip(_MAIN_PHASES, main.registers, strict=True)
        }
    return ChannelSettings(
        phases=phases,
        transformers={
            channel: str(value) if value in (30, 100) else None
            for channel, value in zip(_CHANNELS, transformers.registers, strict=True)
        },
        main_transformers=main_transformers,
    )


async def async_write_channel_settings(
    client: EnecessModbusClient, device_index: int, desired: ChannelSettings
) -> dict[str, str]:
    """Apply a validated patch, retaining successes for a subsequent retry."""
    _validate_device_index(device_index)
    if not isinstance(desired, ChannelSettings):
        raise TypeError("desired must be ChannelSettings")
    for selections, keys, choices in (
        (desired.phases, _CHANNELS, ("L1", "L2", "L3")),
        (desired.transformers, _CHANNELS, ("30", "100")),
        (desired.main_transformers, _MAIN_PHASES, ("100",)),
    ):
        if not isinstance(selections, dict) or any(
            key not in keys or (value is not None and value not in choices)
            for key, value in selections.items()
        ):
            raise ValueError("Invalid channel settings choices")
    if device_index != 0 and any(
        value is not None for value in desired.main_transformers.values()
    ):
        raise ValueError("Main transformers belong to ecoMain only")

    phases = {key: value for key, value in desired.phases.items() if value is not None}
    transformers = {
        key: value for key, value in desired.transformers.items() if value is not None
    }
    main_transformers = {
        key: value
        for key, value in desired.main_transformers.items()
        if value is not None
    }
    fields = [
        *(f"{key}_phase" for key in phases),
        *(f"{key}_transformer" for key in transformers),
        *(f"main_transformer_{key}" for key in main_transformers),
    ]
    if not fields:
        return {}
    try:
        current = await async_read_channel_settings(client, device_index)
    except _IO_ERRORS:
        return dict.fromkeys(fields, "write_failed")

    phase_errors = await async_write_phases(
        client,
        device_index,
        {key: value for key, value in phases.items() if value != current.phases[key]},
    )
    errors = {
        f"{key}_phase": error.removeprefix("phase_")
        for key, error in phase_errors.items()
    }
    writes = [
        *(
            (
                f"{key}_transformer",
                2043 + 10 * device_index + _CHANNELS.index(key),
                int(value),
            )
            for key, value in transformers.items()
            if value != current.transformers[key]
        ),
        *(
            (f"main_transformer_{key}", 2040 + _MAIN_PHASES.index(key), int(value))
            for key, value in main_transformers.items()
            if value != current.main_transformers[key]
        ),
    ]
    for field, address, value in writes:
        error = await _async_write_verified(client, address, [value])
        if error is not None:
            errors[field] = error
    return errors


async def async_read_solar_settings(
    client: EnecessModbusClient, device_indices: list[int]
) -> SolarSettings:
    """Read host parameters and requested meter flags without an online gate."""
    for device_index in device_indices:
        _validate_device_index(device_index)
    parameters = await client.read_holding_registers(5000, 3)
    inverter_channels = {}
    for device_index in dict.fromkeys(device_indices):
        flags = await client.read_holding_registers(2200 + 10 * device_index, 10)
        inverter_channels[device_index] = [
            channel
            for channel, value in zip(_INVERTER_CHANNELS, flags.registers, strict=True)
            if value == 1
        ]
    return SolarSettings(
        capacity=decode_int32_word_swap(parameters.registers[:2]),
        temperature_coefficient=decode_int16(parameters.registers[2:]) / 1000,
        inverter_channels=inverter_channels,
    )


async def async_write_solar_settings(
    client: EnecessModbusClient, desired: SolarSettings
) -> dict[str, str]:
    """Write representable host parameters and explicitly supplied inverter groups."""
    if not isinstance(desired, SolarSettings):
        raise TypeError("desired must be SolarSettings")
    if type(desired.capacity) is not int or not 0 <= desired.capacity <= 2147483647:
        raise ValueError("capacity must be an integer from 0 to 2147483647")
    if type(desired.temperature_coefficient) not in (int, float):
        raise ValueError("temperature_coefficient must be numeric")
    coefficient = Decimal(str(desired.temperature_coefficient)) * 1000
    if (
        not coefficient.is_finite()
        or coefficient != coefficient.to_integral_value()
        or not -32768 <= coefficient <= 32767
    ):
        raise ValueError("temperature_coefficient must fit Int16 at precision 0.001")
    if not isinstance(desired.inverter_channels, dict):
        raise TypeError("inverter_channels must be a device-to-channel mapping")
    for device_index, channels in desired.inverter_channels.items():
        _validate_device_index(device_index)
        if not isinstance(channels, list) or any(
            channel not in _INVERTER_CHANNELS for channel in channels
        ):
            raise ValueError("Inverter channels must be strings from 1 to 10")

    fields = [
        "capacity",
        "temperature_coefficient",
        *(
            f"inverter_channels_{device_index}"
            for device_index in desired.inverter_channels
        ),
    ]
    try:
        current = await async_read_solar_settings(
            client, list(desired.inverter_channels)
        )
    except _IO_ERRORS:
        return dict.fromkeys(fields, "write_failed")

    writes = []
    if desired.capacity != current.capacity:
        writes.append(
            ("capacity", 5000, [desired.capacity & 0xFFFF, desired.capacity >> 16])
        )
    if desired.temperature_coefficient != current.temperature_coefficient:
        writes.append(("temperature_coefficient", 5002, [int(coefficient) & 0xFFFF]))
    writes.extend(
        (
            f"inverter_channels_{device_index}",
            2200 + 10 * device_index + offset,
            [int(channel in channels)],
        )
        for device_index, channels in desired.inverter_channels.items()
        for offset, channel in enumerate(_INVERTER_CHANNELS)
        if (channel in channels) != (channel in current.inverter_channels[device_index])
    )
    errors = {}
    for field, address, values in writes:
        error = await _async_write_verified(client, address, values)
        if error is not None and errors.get(field) != "write_failed":
            errors[field] = error
    return errors
