import asyncio
from dataclasses import dataclass
from typing import Optional

from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient

from .const import CONF_ECOMAIN_UNIT_ID


@dataclass
class ModbusReadResult:
    registers: list[int]


def _registers_to_bytes(registers: list[int]) -> bytes:
    # Each register is 16-bit; Modbus register is big-endian.
    return b"".join(int(r & 0xFFFF).to_bytes(2, "big") for r in registers)


def decode_int16(registers: list[int], *, signed: bool = True) -> int:
    # 16-bit integer in a single Modbus register (big-endian within the register)
    raw = _registers_to_bytes(registers[:1])
    return int.from_bytes(raw, byteorder="big", signed=signed)


def decode_int32_word_swap(registers: list[int], *, signed: bool = True) -> int:
    # On-wire bytes: CDAB (word swap), example: 56 78 12 34 -> 0x12345678
    raw = _registers_to_bytes(list(reversed(registers[:2])))
    return int.from_bytes(raw, byteorder="big", signed=signed)


def decode_int64_word_swap(registers: list[int], *, signed: bool = True) -> int:
    # On-wire bytes: R4 R3 R2 R1, example: 56 78 12 34 EF GH AB CD -> 0xABCDEFGH12345678
    raw = _registers_to_bytes(list(reversed(registers[:4])))
    return int.from_bytes(raw, byteorder="big", signed=signed)


class EnecessModbusClient:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._client: Optional[AsyncModbusTcpClient] = None
        self._lock = asyncio.Lock()

    async def async_connect(self) -> None:
        if self._client is not None and self._client.connected:
            return
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        ok = await self._client.connect()
        if not ok:
            raise ConnectionError(f"Failed to connect to {self._host}:{self._port}")

    async def async_close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None

    async def read_holding_registers(self, address: int, count: int) -> ModbusReadResult:
        async with self._lock:
            await self.async_connect()
            assert self._client is not None
            try:
                resp = await self._client.read_holding_registers(address=address, count=count, device_id=CONF_ECOMAIN_UNIT_ID)
            except TypeError:
                resp = await self._client.read_holding_registers(address=address, count=count, slave=CONF_ECOMAIN_UNIT_ID)  # noqa
            except ModbusException:
                raise
            if resp.isError():
                raise ModbusException(str(resp))
            return ModbusReadResult(registers=list(resp.registers))

    async def async_set_target(self, host: str, port: int) -> None:
        if host == self._host and port == self._port:
            return
        self._host = host
        self._port = port
        await self.async_close()
