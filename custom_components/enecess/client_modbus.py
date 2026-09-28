"""Serialize ecoMain Modbus requests and decode its register byte order."""

import asyncio
from dataclasses import dataclass

from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient

from .const import CONF_ECOMAIN_UNIT_ID


@dataclass
class ModbusReadResult:
    """Expose the validated register payload returned by a read."""

    registers: list[int]


def _registers_to_bytes(registers: list[int]) -> bytes:
    # Each register is 16-bit; Modbus register is big-endian.
    return b"".join(int(r & 0xFFFF).to_bytes(2, "big") for r in registers)


def decode_int16(registers: list[int], *, signed: bool = True) -> int:
    """Decode one big-endian 16-bit register."""
    raw = _registers_to_bytes(registers[:1])
    return int.from_bytes(raw, byteorder="big", signed=signed)


def decode_int32_word_swap(registers: list[int], *, signed: bool = True) -> int:
    """Decode two registers transmitted least-significant word first."""
    raw = _registers_to_bytes(list(reversed(registers[:2])))
    return int.from_bytes(raw, byteorder="big", signed=signed)


def decode_int64_word_swap(registers: list[int], *, signed: bool = True) -> int:
    """Decode four registers transmitted least-significant word first."""
    raw = _registers_to_bytes(list(reversed(registers[:4])))
    return int.from_bytes(raw, byteorder="big", signed=signed)


class EnecessModbusClient:
    """Own one TCP connection and serialize requests to the device."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize a target without opening a network connection."""
        self._host = host
        self._port = port
        self._client: AsyncModbusTcpClient | None = None
        self._lock = asyncio.Lock()

    async def async_connect(self) -> None:
        """Connect on demand, reusing an established connection."""
        if self._client is not None and self._client.connected:
            return
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        ok = await self._client.connect()
        if not ok:
            raise ConnectionError(f"Failed to connect to {self._host}:{self._port}")

    async def async_close(self) -> None:
        """Close the owned transport and clear its reference."""
        if self._client is None:
            return
        self._client.close()
        self._client = None

    async def read_holding_registers(
        self, address: int, count: int
    ) -> ModbusReadResult:
        """Read a complete register range from the configured Modbus unit."""
        async with self._lock:
            await self.async_connect()
            assert self._client is not None
            resp = await self._client.read_holding_registers(
                address=address, count=count, device_id=CONF_ECOMAIN_UNIT_ID
            )
            if resp.isError():
                raise ModbusException(str(resp))
            if len(resp.registers) != count:
                raise ModbusException(
                    f"Expected {count} registers at {address}, got {len(resp.registers)}"
                )
            return ModbusReadResult(registers=list(resp.registers))

    async def write_register(self, address: int, value: int) -> None:
        """Write one register and require a matching function-06 response echo."""
        async with self._lock:
            await self.async_connect()
            assert self._client is not None
            resp = await self._client.write_register(
                address=address, value=value, device_id=CONF_ECOMAIN_UNIT_ID
            )
            if resp is None or resp.isError():
                raise ModbusException(f"Register write failed at {address}: {resp}")
            registers = getattr(resp, "registers", None)
            if getattr(resp, "address", None) != address or registers != [value]:
                raise ModbusException(
                    f"Invalid register write echo at {address}: {resp}"
                )

    async def async_set_target(self, host: str, port: int) -> None:
        """Close the previous transport when discovery changes its target."""
        if host == self._host and port == self._port:
            return
        self._host = host
        self._port = port
        await self.async_close()
