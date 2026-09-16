"""TV Guide Multi-Source integration.

This module fetches Italian TV schedules from `sorrisi.com` and exposes two
sensors:
- ``sensor.guida_tv_ora_in_onda`` for the current programmes;
- ``sensor.guida_tv_prima_serata`` for the prime time programmes.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Dict, Tuple

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Guida TV"

# "Ora in onda" needs to actually change during the day; a plain per-calendar-day
# cache never refreshes again after the first poll. Sorrisi.com does not publish
# a change-frequency guarantee, so 10 minutes is a compromise between freshness
# and not hammering their servers.
REFRESH_INTERVAL = timedelta(minutes=10)

URL_NOW = "https://www.sorrisi.com/guidatv/ora-in-tv/"
URL_PRIME = "https://www.sorrisi.com/guidatv/stasera-in-tv/"

CHANNEL_ORDER = [
    "Rai 1",
    "Rai 2",
    "Rai 3",
    "Rete 4",
    "Canale 5",
    "Italia 1",
    "La7",
    "TV8",
    "NOVE",
]

SKIP_CHANNELS = {
    "IRIS",
    "CANALE20",
    "20",
    "20MEDIASET",
    "RAI4",
}

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
) -> None:
    """Set up the sensors."""
    name = config.get(CONF_NAME)
    session = async_get_clientsession(hass)
    coordinator = SorrisiCoordinator(hass, session)
    await coordinator.async_refresh()
    async_add_entities([
        SorrisiNowSensor(name, coordinator),
        SorrisiPrimeSensor(name, coordinator),
    ])


# -----------------------------------------------------------------------------
# fetching utilities
# -----------------------------------------------------------------------------

async def _fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with async_timeout.timeout(15):
            resp = await session.get(url)
            if resp.status != 200:
                _LOGGER.warning("Sorrisi: %s status %s", url, resp.status)
                return ""
            return await resp.text()
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Error fetching %s: %s", url, err)
        return ""


def _parse_programs(html: str) -> Dict[str, str]:
    """Return a mapping {channel: title} from the provided HTML."""
    soup = BeautifulSoup(html, "html.parser")
    mapping: Dict[str, str] = {}

    for header in soup.select("div.gtv-channel-header"):
        logo = header.find("a", class_="gtv-logo")
        channel = logo.get("data-channel-name") if logo else header.get_text(strip=True)

        article = header.find_next("article", class_="gtv-program-on-air") or \
            header.find_next("article", class_="gtv-program")
        title_el = article.find("h3", class_="gtv-program-title") if article else None
        if channel and title_el:
            key = channel.upper().replace(" ", "")
            if key in SKIP_CHANNELS:
                continue
            mapping[channel.strip()] = title_el.get_text(strip=True)

    def sort_key(item: Tuple[str, str]) -> Tuple[int, str]:
        try:
            idx = CHANNEL_ORDER.index(item[0])
        except ValueError:
            idx = len(CHANNEL_ORDER)
        return idx, item[0]

    return dict(sorted(mapping.items(), key=sort_key))


async def get_schedules(session: aiohttp.ClientSession) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Download and parse schedules from ``sorrisi.com``."""
    html_now, html_prime = await asyncio.gather(
        _fetch_page(session, URL_NOW),
        _fetch_page(session, URL_PRIME),
    )
    return _parse_programs(html_now), _parse_programs(html_prime)


# -----------------------------------------------------------------------------
# Coordinator
# -----------------------------------------------------------------------------

class SorrisiCoordinator(DataUpdateCoordinator[Tuple[Dict[str, str], Dict[str, str]]]):
    """Refreshes both schedules together on a fixed interval.

    A single coordinator shared by both sensors, instead of a per-sensor cache,
    is also what keeps this to 2 downloads per refresh rather than 4.
    """

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="TV Guide Multi-Source",
            update_interval=REFRESH_INTERVAL,
        )
        self._session = session

    async def _async_update_data(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        return await get_schedules(self._session)


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
