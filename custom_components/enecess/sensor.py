"""Route sensor setup to the configured enecess product platform."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONST_DEVICE_ECOMAIN, CONST_DEVICE_ECOPLUG, CONST_DEVICE_TYPE
from .ecomain.sensor import async_setup_entry as async_setup_ecomain
from .ecoplug.sensor import async_setup_entry as async_setup_ecoplug
from .runtime import EnecessConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EnecessConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform for supported device types."""
    device_type = entry.data.get(CONST_DEVICE_TYPE)
    if device_type == CONST_DEVICE_ECOMAIN:
        await async_setup_ecomain(hass, entry, async_add_entities)
        return
    if device_type == CONST_DEVICE_ECOPLUG:
        await async_setup_ecoplug(hass, entry, async_add_entities)
