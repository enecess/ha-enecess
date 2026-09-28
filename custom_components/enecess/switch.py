"""Route switch setup to the ecoPlug platform."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONST_DEVICE_ECOPLUG, CONST_DEVICE_TYPE
from .ecoplug.switch import async_setup_entry as async_setup_ecoplug
from .runtime import EnecessConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EnecessConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform for supported device types."""
    if entry.data.get(CONST_DEVICE_TYPE) != CONST_DEVICE_ECOPLUG:
        return

    await async_setup_ecoplug(hass, entry, async_add_entities)
