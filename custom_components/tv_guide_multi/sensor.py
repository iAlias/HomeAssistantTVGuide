"""TV Guide Multi-Source integration.

This module exposes two sensors fed by ``coordinator.SorrisiCoordinator``:
- ``sensor.guida_tv_ora_in_onda`` for the current programmes;
- ``sensor.guida_tv_prima_serata`` for the prime time programmes.
"""

from __future__ import annotations

from typing import Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SorrisiCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensors from a config entry."""
    coordinator: SorrisiCoordinator = hass.data[DOMAIN][entry.entry_id]
    base_name = entry.data.get("name", entry.title)
    async_add_entities([
        SorrisiNowSensor(base_name, coordinator),
        SorrisiPrimeSensor(base_name, coordinator),
    ])


# -----------------------------------------------------------------------------
# Sensor classes
# -----------------------------------------------------------------------------

class _SorrisiBase(CoordinatorEntity[SorrisiCoordinator], SensorEntity):
    """Common functionality for both sensors."""

    def __init__(self, base_name: str, coordinator: SorrisiCoordinator) -> None:
        super().__init__(coordinator)
        self._base_name = base_name


class SorrisiNowSensor(_SorrisiBase):
    """Current programmes sensor."""

    _attr_icon = "mdi:television-play"

    def __init__(self, base_name: str, coordinator: SorrisiCoordinator) -> None:
        super().__init__(base_name, coordinator)
        self._attr_name = f"{base_name} - Ora in onda"
        self._attr_unique_id = "tvguide_sorrisi_now"

    @property
    def native_value(self) -> str:
        cache_now, _ = self.coordinator.data
        return next(iter(cache_now.values()), "Nessun dato")

    @property
    def extra_state_attributes(self) -> Dict[str, object]:
        cache_now, _ = self.coordinator.data
        return {
            "programmi_correnti": cache_now,
            "fonte": "sorrisi.com",
        }


class SorrisiPrimeSensor(_SorrisiBase):
    """Prime time programmes sensor."""

    _attr_icon = "mdi:movie-open"

    def __init__(self, base_name: str, coordinator: SorrisiCoordinator) -> None:
        super().__init__(base_name, coordinator)
        self._attr_name = f"{base_name} - Prima serata"
        self._attr_unique_id = "tvguide_sorrisi_prime"

    @property
    def native_value(self) -> str:
        _, cache_prime = self.coordinator.data
        return next(iter(cache_prime.values()), "Nessun dato")

    @property
    def extra_state_attributes(self) -> Dict[str, object]:
        _, cache_prime = self.coordinator.data
        return {
            "prima_serata": cache_prime,
            "fonte": "sorrisi.com",
        }
