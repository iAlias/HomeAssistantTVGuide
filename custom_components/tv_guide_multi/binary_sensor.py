"""Binary sensors that turn on when a favorite program is airing right now."""

from __future__ import annotations

from typing import Dict

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_FAVORITES, DOMAIN
from .coordinator import SorrisiCoordinator
from .favorites import matching_channels, parse_favorites


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up one binary sensor per configured favorite program."""
    coordinator: SorrisiCoordinator = hass.data[DOMAIN][entry.entry_id]
    favorites = parse_favorites(entry.options.get(CONF_FAVORITES, ""))
    async_add_entities(
        SorrisiFavoriteBinarySensor(coordinator, favorite) for favorite in favorites
    )


class SorrisiFavoriteBinarySensor(CoordinatorEntity[SorrisiCoordinator], BinarySensorEntity):
    """On when a program whose title contains ``favorite`` is on air now."""

    _attr_icon = "mdi:star-check"

    def __init__(self, coordinator: SorrisiCoordinator, favorite: str) -> None:
        super().__init__(coordinator)
        self._favorite = favorite
        self._attr_name = f"In onda: {favorite}"
        self._attr_unique_id = f"tvguide_sorrisi_favorite_{favorite.casefold()}"

    @property
    def is_on(self) -> bool:
        cache_now, _ = self.coordinator.data
        return bool(matching_channels(cache_now, self._favorite))

    @property
    def extra_state_attributes(self) -> Dict[str, object]:
        cache_now, _ = self.coordinator.data
        return {"canali": matching_channels(cache_now, self._favorite)}
