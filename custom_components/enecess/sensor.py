from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONST_DEVICE_TYPE, CONST_DEVICE_ECOMAIN


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    device_type = entry.data.get(CONST_DEVICE_TYPE)
    if device_type == CONST_DEVICE_ECOMAIN:
        from .ecomain.sensor import async_setup_entry as async_setup_ecomain

        await async_setup_ecomain(hass, entry, async_add_entities)
        return
