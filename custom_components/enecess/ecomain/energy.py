"""Persist cloud energy totals independently of enabled sensor entities."""

import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry, restore_state
from homeassistant.helpers.storage import Store

from ..const import DOMAIN
from .model import RegisterSpec


def _valid_total(value: object) -> float | None:
    """Accept finite nonnegative native energy values only."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None


class CloudEnergyStore:
    """Own entry-level energy state using Home Assistant's storage helper."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Bind stored totals to the entry, independent of entity names."""
        self._hass = hass
        self._entry = entry
        self._store = Store[dict[str, float]](
            hass, 1, f"{DOMAIN}.{entry.entry_id}.cloud_energy"
        )
        self._totals: dict[str, float] = {}
        self._skip_initial: set[str] = set()
        self._loaded = False
        self._save_pending = False

    async def async_load(self, specs: list[RegisterSpec]) -> None:
        """Restore totals, including previously stored native sensor values."""
        stored = await self._store.async_load()
        if stored is not None:
            self._totals = {
                key: total
                for key, value in stored.items()
                if (total := _valid_total(value)) is not None
            }
        else:
            # Preserve the previous RestoreSensor total even if it is disabled.
            registry = entity_registry.async_get(self._hass)
            states = restore_state.async_get(self._hass).last_states
            keys = {spec.key for spec in specs if spec.kind == "energy_accumulated"}
            for entity in entity_registry.async_entries_for_config_entry(
                registry, self._entry.entry_id
            ):
                key = entity.unique_id.partition(":key_")[2].removesuffix(":mode_cloud")
                previous = states.get(entity.entity_id)
                if key not in keys or previous is None or previous.extra_data is None:
                    continue
                extra = previous.extra_data.as_dict()
                total = _valid_total(extra.get("native_value"))
                if (
                    total is not None
                    and extra.get("native_unit_of_measurement") == "Wh"
                ):
                    self._totals[key] = total
        self._skip_initial = set(self._totals)
        self._loaded = True

    @callback
    def async_accumulate(
        self, values: dict[str, float], specs: list[RegisterSpec]
    ) -> None:
        """Add each successful poll once before notifying any entity listeners."""
        for spec in specs:
            if spec.kind != "energy_accumulated":
                continue
            skip = spec.key in self._skip_initial
            self._skip_initial.discard(spec.key)
            delta = _valid_total(values.get(spec.source_key))
            if delta is None:
                continue
            total = self._totals.get(spec.key, 0.0)
            if not skip:
                total += delta
            self._totals[spec.key] = total
            values[spec.key] = round(total, 3)
        if not self._save_pending:
            self._save_pending = True
            self._store.async_delay_save(self._data_to_save, 60)

    @callback
    def _data_to_save(self) -> dict[str, float]:
        """Capture the latest totals without postponing an existing checkpoint."""
        self._save_pending = False
        return self._totals.copy()

    async def async_save(self) -> None:
        """Flush totals on unload without overwriting a failed load."""
        if self._loaded:
            await self._store.async_save(self._data_to_save())
            self._loaded = False

    async def async_remove(self) -> None:
        """Remove persistent totals when the config entry is deleted."""
        await self._store.async_remove()
