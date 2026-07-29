from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONST_DEVICE_ECOPLUG, CONST_DEVICE_TYPE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform for supported device types."""
    if entry.data.get(CONST_DEVICE_TYPE) != CONST_DEVICE_ECOPLUG:
        return

    from .ecoplug.switch import async_setup_entry as async_setup_ecoplug

    await async_setup_ecoplug(hass, entry, async_add_entities)
